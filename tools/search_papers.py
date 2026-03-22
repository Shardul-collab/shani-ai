import difflib
import requests
import time

import repositories.paper_repo as pr
import repositories.workflow_repo as wr

from tools.search_arxiv import search_arxiv
from tools.generate_queries import generate_queries


# =========================================================
# CONFIG
# =========================================================

MAX_RESULTS_PER_SOURCE = 10
QUERY_CAP = 15
FINAL_PAPER_LIMIT = 50


# =========================================================
# SAFE REQUEST
# =========================================================

def safe_request(url, params):

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 429:
            time.sleep(2)
            response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as e:
        print("Request error:", e)
        return None


# =========================================================
# OPENALEX ABSTRACT FIX
# =========================================================

def parse_openalex_abstract(inverted_index):

    if not inverted_index:
        return ""

    words = []

    for word, positions in inverted_index.items():
        for pos in positions:
            words.append((pos, word))

    words.sort()
    return " ".join([w for _, w in words])


# =========================================================
# SCORING FUNCTION
# =========================================================

def compute_score(paper, primary, query):

    title = paper.get("title", "").lower()
    abstract = paper.get("summary", "").lower()

    score = 0

    if primary:
        if primary in title:
            score += 5
        elif primary in abstract:
            score += 3
        else:
            return 0

    for token in query.lower().split():
        if token in title:
            score += 2
        elif token in abstract:
            score += 1

    if len(abstract) > 500:
        score += 1

    source = paper.get("source", "")
    if source == "arxiv":
        score += 2

    return score


# =========================================================
# DUPLICATE DETECTION
# =========================================================

def is_duplicate(title, seen_titles):

    for t in seen_titles:
        if difflib.SequenceMatcher(None, title, t).ratio() > 0.9:
            return True

    return False


# =========================================================
# SOURCE: SEMANTIC SCHOLAR
# =========================================================

def search_semantic_scholar(query):

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "limit": MAX_RESULTS_PER_SOURCE,
        "fields": "title,abstract,openAccessPdf"
    }

    results = []

    data = safe_request(url, params)

    if not data:
        return results

    for paper in data.get("data", []):

        pdf = paper.get("openAccessPdf")

        results.append({
            "title": paper.get("title"),
            "summary": paper.get("abstract", "") or "",
            "pdf_url": pdf.get("url") if pdf else None,
            "source": "semantic_scholar"
        })

    return results


# =========================================================
# SOURCE: OPENALEX
# =========================================================

def search_openalex(query):

    url = "https://api.openalex.org/works"

    params = {
        "search": query,
        "per_page": MAX_RESULTS_PER_SOURCE
    }

    results = []

    data = safe_request(url, params)

    if not data:
        return results

    for work in data.get("results", []):

        pdf_url = None

        if work.get("primary_location"):
            pdf_url = work["primary_location"].get("pdf_url")

        abstract = parse_openalex_abstract(
            work.get("abstract_inverted_index")
        )

        results.append({
            "title": work.get("title"),
            "summary": abstract,
            "pdf_url": pdf_url,
            "source": "openalex"
        })

    return results


# =========================================================
# MULTI-SOURCE FETCH
# =========================================================

def fetch_from_sources(query):

    results = []
    results.extend(search_arxiv(query))
    results.extend(search_semantic_scholar(query))
    results.extend(search_openalex(query))

    return results


# =========================================================
# MAIN TOOL (S2)
# =========================================================

def search_papers(repo, workflow_id, execution_attempt_id=None, **kwargs):

    workflow = wr.get_workflow(repo, workflow_id)

    if not workflow:
        return {
            "status": "error",
            "data": None,
            "error": "Workflow not found"
        }

    config = repo.fetch_one(
        """
        SELECT material
        FROM WorkflowResearchConfig
        WHERE workflow_id = ?
        """,
        (workflow_id,)
    )

    primary = config["material"].lower() if config and config["material"] else None

    query_result = generate_queries(repo, workflow_id)

    if query_result["status"] != "success":
        return query_result

    queries = query_result["data"]

    all_candidates = []

    for query in queries:

        print(f"Searching: {query}")

        papers = fetch_from_sources(query)

        count = 0

        for p in papers:

            if count >= QUERY_CAP:
                break

            title = p.get("title")
            pdf_url = p.get("pdf_url")

            # ------------------------------
            # SAFE VALIDATION
            # ------------------------------

            if not title or not pdf_url:
                continue

            pdf_url = pdf_url.strip()

            # STRICT PDF FILTER (ONLY REAL PDFs)
            if not pdf_url.lower().endswith(".pdf"):
                continue

            score = compute_score(p, primary, query)

            if score < 3:
                continue

            all_candidates.append({
                "paper": p,
                "score": score
            })

            count += 1

    # --------------------------------------------------
    # RANK
    # --------------------------------------------------

    all_candidates.sort(key=lambda x: x["score"], reverse=True)

    seen_titles = set()
    inserted_ids = []

    for item in all_candidates:

        p = item["paper"]
        title = p["title"]

        if is_duplicate(title, seen_titles):
            continue

        existing = repo.fetch_one(
            """
            SELECT id FROM Paper
            WHERE workflow_id = ? AND title = ?
            """,
            (workflow_id, title)
        )

        if existing:
            continue

        seen_titles.add(title)

        paper_id = pr.create_paper(
            repo,
            workflow_id,
            title,
            p.get("source", "unknown"),
            p["pdf_url"],
            "pending"
        )

        if paper_id:
            inserted_ids.append(paper_id)

        if len(inserted_ids) >= FINAL_PAPER_LIMIT:
            break

    return {
        "status": "success",
        "data": inserted_ids,
        "error": None
    }