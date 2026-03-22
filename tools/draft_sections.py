import repositories.draft_section_repo as ds_repo
from services.llm_service import LLMService, OllamaClient
from services.knowledge_compressor import KnowledgeCompressor


SECTION_MAP = {
    "material": "Materials Investigated",
    "synthesis_method": "Synthesis Methods",
    "characterization": "Characterization Techniques",
    "computational_method": "Simulation Methods",
    "application": "Applications"
}


def build_citation_map(papers):
    citation_map = {}
    citation_lines = []

    for i, p in enumerate(papers, start=1):
        citation_map[p["id"]] = i
        citation_lines.append(f"[{i}] {p['title']}")

    return citation_map, "\n".join(citation_lines)


def group_by_section(rows):
    grouped = {}

    for row in rows:
        category = row["category"]

        if category not in SECTION_MAP:
            continue

        section = SECTION_MAP[category]
        grouped.setdefault(section, []).append(row)

    return grouped


def draft_sections(repo, workflow_id, execution_attempt_id=None, **kwargs):

    rows = repo.fetch_all(
        """
        SELECT 
            rk.category,
            rk.value,
            rk.sentence,
            rk.paper_id,
            rr.subject,
            rr.relation,
            rr.object
        FROM ResearchKnowledge rk
        LEFT JOIN ResearchRelation rr 
            ON rk.paper_id = rr.paper_id
        JOIN Paper p ON rk.paper_id = p.id
        WHERE p.workflow_id = ?
        AND rk.sentence IS NOT NULL
        """,
        (workflow_id,)
    )

    if not rows:
        return {"status": "success", "data": "No research knowledge found.", "error": None}

    papers = repo.fetch_all(
        """
        SELECT id, title
        FROM Paper
        WHERE workflow_id = ?
        """,
        (workflow_id,)
    )

    citation_map, citations_text = build_citation_map(papers)
    paper_lookup = {p["id"]: p["title"] for p in papers}

    grouped = group_by_section(rows)

    llm = OllamaClient()
    service = LLMService(llm)

    compressor = KnowledgeCompressor(max_clusters=8)

    created_sections = []

    for section_name, knowledge_rows in grouped.items():

        print(f"\n🧠 Generating section: {section_name}")

        try:
            summaries = compressor.build_cluster_summaries(
                knowledge_rows,
                citation_map,
                paper_lookup,
                service
            )
        except Exception as e:
            print(f"Cluster build failed: {e}")
            continue

        if not summaries:
            print(f"⚠️ No summaries for {section_name}")
            continue

        evidence_text = "\n\n".join(summaries)

        prompt = f"""
You are writing a scientific literature review.

Section:
{section_name}

Available research papers:
{citations_text}

Structured scientific evidence:
{evidence_text}

INSTRUCTIONS:

Write a detailed literature review section (800–1200 words).

Structure:
- Paragraph 1: Introduction
- Paragraph 2–4: Synthesis across studies
- Paragraph 5–6: Comparison and trends
- Paragraph 7: Observations or limitations

STRICT CITATION RULES:
- Every claim MUST include citation like [3]
- Use ONLY numbers inside square brackets
- NEVER generate formats like [2025], [A], [b], [4.2]
- NEVER generate citation ranges like [1-5]

STRICT CONTENT RULES:
- Use ONLY provided evidence
- Do NOT invent information
- Formal academic tone only
- Focus on linking materials, methods, and applications
"""

        section_text = None

        # ✅ IMPROVED RETRY + LOWER THRESHOLD
        for _ in range(3):
            try:
                section_text = service.generate_text(prompt)
                if section_text and len(section_text) > 300:
                    break
            except:
                continue

        # ✅ FALLBACK (CRITICAL FIX)
        if not section_text:
            section_text = f"{section_name} section could not be fully generated due to limited available evidence."

        with repo.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO DraftSection
                (workflow_id, section_name, content, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (workflow_id, section_name, section_text)
            )

        created_sections.append(section_name)

    return {"status": "success", "data": created_sections, "error": None}