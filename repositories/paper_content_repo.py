from repositories.repository import Repository


# ----------------------------
# R7 — PaperContent Repository (FINAL)
# ----------------------------

def create_paper_content(repo: Repository, paper_id: int, section_name: str, content: str):

    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO PaperContent (paper_id, section_name, content)
            VALUES (?, ?, ?)
            """,
            (paper_id, section_name, content)
        )


def get_paper_content(repo: Repository, paper_id: int):

    rows = repo.fetch_all(
        """
        SELECT section_name, content
        FROM PaperContent
        WHERE paper_id = ?
        """,
        (paper_id,)
    )

    if not rows:
        return None

    # Convert row-based → dict
    content_dict = {}

    for r in rows:
        content_dict[r["section_name"]] = r["content"]

    return content_dict