import re
import json
from collections import Counter, defaultdict
import spacy

from tools.text_cleaner import clean_scientific_text
from tools.relation_extractor import extract_relations

import repositories.paper_repo as paper_repo
from services.llm_service import LLMService, OllamaClient


# --------------------------------------------------
# NLP MODEL
# --------------------------------------------------

try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")


# --------------------------------------------------
# HIGH VALUE SENTENCE DETECTOR
# --------------------------------------------------

TECH_KEYWORDS = {"xrd", "sem", "tem", "edx", "afm", "uv", "raman", "ftir"}
ACTION_KEYWORDS = {"revealed", "observed", "measured", "analyzed", "determined", "confirmed", "demonstrated", "showed", "indicated", "reported"}
RESULT_KEYWORDS = {"increased", "decreased", "improved", "enhanced", "reduced", "higher", "lower", "significant", "strong", "weak"}
PROCESS_KEYWORDS = {"deposition", "synthesis", "annealing", "fabrication", "growth", "prepared"}


def score_sentence(sentence):
    s = sentence.lower()
    score = 0

    if any(k in s for k in TECH_KEYWORDS):
        score += 3
    if any(k in s for k in ACTION_KEYWORDS):
        score += 2
    if any(k in s for k in RESULT_KEYWORDS):
        score += 2
    if any(k in s for k in PROCESS_KEYWORDS):
        score += 2
    if re.search(r"\d", sentence):
        score += 2
    if len(sentence.split()) > 12:
        score += 1

    return score


# --------------------------------------------------
# CONTEXT-AWARE SELECTION (NEW)
# --------------------------------------------------

def expand_with_context(sentences, selected_indices, window=1):
    expanded = set()

    for idx in selected_indices:
        for i in range(idx - window, idx + window + 1):
            if 0 <= i < len(sentences):
                expanded.add(i)

    return [sentences[i] for i in sorted(expanded)]


def select_with_context(sentences, max_sentences=40):

    scored = [(score_sentence(s), i, s) for i, s in enumerate(sentences)]
    scored = [x for x in scored if x[0] >= 3]

    scored.sort(reverse=True)

    anchors = scored[:max_sentences // 2]
    selected_indices = [i for _, i, _ in anchors]

    return expand_with_context(sentences, selected_indices, window=1)


# --------------------------------------------------
# RULE LISTS
# --------------------------------------------------

CHARACTERIZATION_TECHNIQUES = ["XRD", "SEM", "TEM", "EDX", "AFM", "UV-Vis", "Raman", "FTIR"]

APPLICATION_KEYWORDS = ["sensor", "gas sensing", "photodetector", "solar cell", "catalysis"]

COMPUTATIONAL_METHODS = ["DFT", "density functional theory", "molecular dynamics", "Monte Carlo", "GW approximation", "Hartree-Fock"]

SOFTWARE_TOOLS = ["Quantum ESPRESSO", "VASP", "Gaussian", "LAMMPS", "ABINIT"]


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def clean_text(text):
    text = text.replace("−", "-")
    text = re.sub(r"\s+", " ", text)
    return text


def split_paragraphs(text):
    return [p.strip() for p in text.split("\n") if len(p.strip()) > 60]


def split_sentences(text):
    try:
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 40]
    except:
        return []


# --------------------------------------------------
# MATERIAL DETECTOR
# --------------------------------------------------

def is_probably_material(val):
    val = val.strip()

    if re.match(r"^[A-Z][a-z]?\d*[A-Z0-9]*$", val):
        return True

    keywords = ["oxide", "nanoparticle", "nanostructure", "film", "semiconductor", "composite"]
    return any(k in val.lower() for k in keywords)


FORMULA_PATTERN = re.compile(r"\b[A-Z][a-z]?\d*[A-Z][A-Za-z0-9]*\b")


def detect_materials(text):

    paragraphs = split_paragraphs(text)
    candidates = []

    STOPWORDS = {"film", "films", "sample", "samples", "study", "method", "results", "analysis", "paper", "work"}

    for p in paragraphs:

        try:
            doc = nlp(p)
        except:
            continue

        for ent in doc.ents:
            if ent.label_ in {"PERSON", "GPE", "LOC", "ORG"}:
                continue

            candidate = ent.text.strip()
            if len(candidate) < 2 or candidate.lower() in STOPWORDS:
                continue

            candidates.append(candidate)

        for token in doc:
            word = token.text.strip()
            if FORMULA_PATTERN.match(word):
                candidates.append(word)

        if doc.has_annotation("DEP"):
            for chunk in doc.noun_chunks:
                phrase = chunk.text.strip()
                if len(phrase) < 3 or phrase.lower() in STOPWORDS:
                    continue
                candidates.append(phrase)

    counts = Counter(candidates)
    return [m for m, count in counts.items() if count >= 2 and is_probably_material(m)]


# --------------------------------------------------
# RULE DETECTION
# --------------------------------------------------

def detect_rules_in_sentence(sentence):
    s = sentence.lower()
    knowledge = []

    for tech in CHARACTERIZATION_TECHNIQUES:
        if tech.lower() in s:
            knowledge.append({"category": "characterization", "value": tech})

    for app in APPLICATION_KEYWORDS:
        if app in s:
            knowledge.append({"category": "application", "value": app})

    for method in COMPUTATIONAL_METHODS:
        if method.lower() in s:
            knowledge.append({"category": "computational_method", "value": method})

    for sw in SOFTWARE_TOOLS:
        if sw.lower() in s:
            knowledge.append({"category": "software", "value": sw})

    return knowledge


# --------------------------------------------------
# LLM EXTRACTION (CONTROLLED)
# --------------------------------------------------

def llm_extract(sentence, service):
    try:
        prompt = f"""
Extract structured research knowledge.

Return JSON list.

Sentence:
{sentence}
"""
        raw = service.generate_text(prompt)

        if not raw:
            return []

        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
        except:
            pass

        return []

    except:
        return []


# --------------------------------------------------
# MAIN TOOL
# --------------------------------------------------

def extract_research_knowledge(repo, workflow_id, execution_attempt_id=None, **kwargs):

    all_results = []

    papers = repo.fetch_all(
        """
        SELECT id, raw_text
        FROM Paper
        WHERE workflow_id = ?
        AND raw_text IS NOT NULL
        """,
        (workflow_id,)
    )

    if not papers:
        return {"status": "success", "data": [], "error": None}

    llm = OllamaClient()
    service = LLMService(llm)

    for paper in papers:

        paper_id = paper["id"]
        raw_text = clean_text(clean_scientific_text(paper["raw_text"] or ""))

        knowledge = []

        for m in detect_materials(raw_text):
            knowledge.append({
                "category": "material",
                "value": m,
                "sentence": None,
                "section_source": "material_detector"
            })

        # 🔥 CONTEXT-AWARE SENTENCES
        sentences = split_sentences(raw_text)
        sentences = select_with_context(sentences, max_sentences=40)

        llm_calls = 0
        MAX_LLM_CALLS = 20

        for sentence in sentences:

            for item in detect_rules_in_sentence(sentence):
                knowledge.append({
                    "category": item["category"],
                    "value": item["value"],
                    "sentence": sentence,
                    "section_source": "rule"
                })

            if llm_calls < MAX_LLM_CALLS and score_sentence(sentence) >= 6:
                extracted = llm_extract(sentence, service)
                llm_calls += 1
            else:
                extracted = []

            for item in extracted:
                if isinstance(item, dict) and "category" in item and "value" in item:
                    knowledge.append({
                        "category": item["category"],
                        "value": str(item["value"]).strip(),
                        "sentence": sentence,
                        "section_source": "llm"
                    })

        seen = set()
        unique = []

        for item in knowledge:
            key = (item["category"], item["value"], item.get("sentence"))
            if key not in seen:
                seen.add(key)
                unique.append(item)

        category_limited = defaultdict(list)
        for item in unique:
            if len(category_limited[item["category"]]) < 15:
                category_limited[item["category"]].append(item)

        unique = [i for sub in category_limited.values() for i in sub]

        relations = extract_relations(raw_text, unique)

        with repo.transaction() as cursor:

            for item in unique:
                cursor.execute(
                    """
                    INSERT INTO ResearchKnowledge
                    (paper_id, category, value, sentence, section_source, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        paper_id,
                        item["category"],
                        item["value"],
                        item.get("sentence"),
                        item["section_source"]
                    )
                )

            for r in relations:
                cursor.execute(
                    """
                    INSERT INTO ResearchRelation
                    (paper_id, subject, relation, object, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (paper_id, r["subject"], r["relation"], r["object"])
                )

        paper_repo.update_paper_status(repo, paper_id, "completed")

        all_results.extend(unique)

    return {"status": "success", "data": all_results, "error": None}