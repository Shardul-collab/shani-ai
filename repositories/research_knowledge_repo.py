from datetime import datetime
from repositories.repository import Repository


def create_research_knowledge(
    repo: Repository,
    paper_id: int,
    category: str,
    value: str,
    section_source: str | None
):

    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute("""
            INSERT INTO ResearchKnowledge (
                paper_id,
                category,
                value,
                section_source,
                created_at
            )
            VALUES (?, ?, ?, ?, ?);
        """, (
            paper_id,
            category,
            value,
            section_source,
            timestamp
        ))

        return cursor.lastrowid


def get_knowledge_for_paper(repo: Repository, paper_id: int):

    rows = repo.fetch_all(
        """
        SELECT *
        FROM ResearchKnowledge
        WHERE paper_id = ?
        """,
        (paper_id,)
    )

    return [dict(r) for r in rows]