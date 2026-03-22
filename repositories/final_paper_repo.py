from datetime import datetime
from repositories.repository import Repository


# ------------------------------------------------
# FinalPaperSection (S7)
# ------------------------------------------------

def create_final_section(
    repo: Repository,
    workflow_id: int,
    section_name: str,
    order_index: int,
    content: str
) -> int:

    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO FinalPaperSection (
                workflow_id,
                section_name,
                order_index,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (workflow_id, section_name, order_index, content, timestamp)
        )

        return cursor.lastrowid


def get_final_sections(repo: Repository, workflow_id: int):

    rows = repo.fetch_all(
        """
        SELECT id, workflow_id, section_name,
               order_index, content, created_at
        FROM FinalPaperSection
        WHERE workflow_id = ?
        ORDER BY order_index ASC
        """,
        (workflow_id,)
    )

    return [dict(row) for row in rows]