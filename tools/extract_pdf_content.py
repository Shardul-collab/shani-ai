import os
import fitz

from repositories.repository import Repository
import repositories.paper_repo as pr

DB_NAME = "research_workflow.db"
PAPERS_DIR = "papers"


def get_processing_papers(repo):

    query = """
        SELECT id, title
        FROM Paper
        WHERE status = 'processing';
    """

    return repo.fetch_all(query)


def extract_text_from_pdf(filepath):

    doc = fitz.open(filepath)

    text = ""

    for page in doc:
        text += page.get_text()

    return text


def split_into_sections(text):

    text_lower = text.lower()

    sections = {
        "abstract": "",
        "introduction": "",
        "methods": "",
        "results": "",
        "discussion": ""
    }

    markers = list(sections.keys())

    for i, marker in enumerate(markers):

        start = text_lower.find(marker)

        if start == -1:
            continue

        if i + 1 < len(markers):
            end = text_lower.find(markers[i + 1], start)
        else:
            end = len(text)

        sections[marker] = text[start:end].strip()

    return sections


def insert_sections(repo, paper_id, sections):

    with repo.transaction() as cursor:

        for name, content in sections.items():

            if not content:
                continue

            cursor.execute(
                """
                INSERT INTO PaperContent (
                    paper_id,
                    section_name,
                    content
                )
                VALUES (?, ?, ?);
                """,
                (paper_id, name, content)
            )


def main():

    repo = Repository(DB_NAME)

    papers = get_processing_papers(repo)

    if not papers:
        print("No papers ready for extraction.")
        return

    print(f"{len(papers)} papers ready for extraction.")

    for paper in papers:

        paper_id = paper["id"]

        try:

            filepath = os.path.join(PAPERS_DIR, f"{paper_id}.pdf")

            print(f"Extracting paper {paper_id}")

            text = extract_text_from_pdf(filepath)

            sections = split_into_sections(text)

            insert_sections(repo, paper_id, sections)

            pr.update_paper_status(repo, paper_id, "completed")

            print(f"Extraction complete for paper {paper_id}")

        except Exception as e:

            print(f"Extraction failed for paper {paper_id}: {e}")

            pr.update_paper_status(repo, paper_id, "failed")


if __name__ == "__main__":
    main()