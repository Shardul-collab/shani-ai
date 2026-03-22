from datetime import datetime
from repositories.repository import Repository


# ----------------------------
# R9 — DraftSection Repository
# ----------------------------

def create_draft_section(
    repo: Repository,
    workflow_id: int,
    section_name: str,
    content: str
) -> int:

    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO DraftSection (
                workflow_id,
                section_name,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?);
            """,
            (workflow_id, section_name, content, timestamp)
        )

        return cursor.lastrowid


def get_sections_for_workflow(
    repo: Repository,
    workflow_id: int
):

    rows = repo.fetch_all(
        """
        SELECT id, workflow_id, section_name, content, created_at
        FROM DraftSection
        WHERE workflow_id = ?;
        """,
        (workflow_id,)
    )

    return [dict(row) for row in rows]