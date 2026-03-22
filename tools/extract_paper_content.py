import os
import fitz  # PyMuPDF

import repositories.paper_repo as pr
import repositories.paper_content_repo as pc_repo
import repositories.failure_repo as failure_repo


def extract_text_from_pdf(filepath):
    try:
        doc = fitz.open(filepath)
        text = ""

        for page in doc:
            page_text = page.get_text()
            if page_text:
                text += page_text + "\n"

        doc.close()
        return text.strip()

    except Exception as e:
        print(f"[S4] PDF extraction failed: {filepath} → {e}")
        return ""


def split_sections(text):

    text_lower = text.lower()

    def extract_section(start, end_keywords):
        start_idx = text_lower.find(start)
        if start_idx == -1:
            return None

        end_idx = len(text)

        for ek in end_keywords:
            idx = text_lower.find(ek, start_idx + 10)
            if idx != -1:
                end_idx = min(end_idx, idx)

        return text[start_idx:end_idx].strip()

    return {
        "abstract": extract_section("abstract", ["introduction"]),
        "introduction": extract_section("introduction", ["method", "materials"]),
        "methodology": extract_section("method", ["result", "discussion"]),
        "results": extract_section("result", ["discussion", "conclusion"]),
        "discussion": extract_section("discussion", ["conclusion"]),
        "conclusion": extract_section("conclusion", [])
    }


def extract_paper_content(repo, workflow_id, execution_attempt_id=None, **kwargs):

    papers = repo.fetch_all(
        """
        SELECT id, title, pdf_url
        FROM Paper
        WHERE workflow_id = ?
        AND pdf_url IS NOT NULL
        """,
        (workflow_id,)
    )

    if not papers:
        print("[S4] No papers found for processing")
        return {"status": "success", "data": [], "error": None}

    processed = []

    for paper in papers:

        paper_id = paper["id"]
        title = paper["title"]
        filepath = paper["pdf_url"]
        # ✅ FIX: normalize to absolute path
        if not os.path.isabs(filepath):
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                filepath = os.path.join(BASE_DIR, filepath)

        print(f"\n[S4] Processing paper {paper_id}")
        print(f"[S4] Title: {title}")
        print(f"[S4] File: {filepath}")

        try:

            if not os.path.exists(filepath):
                print(f"[DEBUG] File does not exist at: {filepath}")
                raise RuntimeError(f"Missing PDF file: {filepath}")
            raw_text = extract_text_from_pdf(filepath)

            print(f"[S4] Extracted length: {len(raw_text)}")

            if not raw_text or len(raw_text) < 200:
                raise RuntimeError("Text extraction too weak")

            sections = split_sections(raw_text)

            # Store each section as separate row
            for section_name, content in sections.items():
                if content:
                    pc_repo.create_paper_content(
                        repo,
                        paper_id,
                        section_name,
                        content
                    )

            # Store raw text for S5
            pr.store_paper_text(repo, paper_id, raw_text)

            # Keep status as processing
            pr.update_paper_status(repo, paper_id, "processing")

            processed.append(paper_id)

        except Exception as e:

            error_msg = str(e)

            print(f"[S4] ❌ Failed paper {paper_id}: {error_msg}")

            pr.update_paper_status(repo, paper_id, "failed")

            failure_repo.log_failure(
                repo,
                workflow_id,
                "EXTRACTION_ERROR",
                error_msg,
                paper_id=paper_id
            )

    return {
        "status": "success",
        "data": processed,
        "error": None
    }