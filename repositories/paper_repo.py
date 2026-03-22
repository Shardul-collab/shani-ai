from datetime import datetime
import sqlite3
from repositories.repository import Repository


# ------------------------------------------------
# Paper (S3)
# ------------------------------------------------

def create_paper(repo: Repository, workflow_id: int, title: str, source: str, pdf_url: str, status: str):

    timestamp = datetime.utcnow().isoformat()

    try:
        with repo.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO Paper (
                    workflow_id,
                    title,
                    source,
                    pdf_url,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (workflow_id, title, source, pdf_url, status, timestamp, timestamp)
            )

            return cursor.lastrowid

    except sqlite3.IntegrityError:
        # Duplicate paper detected
        return None


def update_paper_status(repo: Repository, paper_id: int, new_status: str):

    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            UPDATE Paper
            SET status = ?,
                updated_at = ?
            WHERE id = ?;
            """,
            (new_status, timestamp, paper_id)
        )

        if cursor.rowcount == 0:
            raise ValueError(f"Paper ID {paper_id} does not exist.")


def get_pending_papers(repo: Repository, workflow_id: int):

    rows = repo.fetch_all(
        """
        SELECT id, workflow_id, title, source, pdf_url, status
        FROM Paper
        WHERE workflow_id = ?
        AND status = 'pending'
        """,
        (workflow_id,)
    )

    return [dict(row) for row in rows]


# ------------------------------------------------
# Paper Processing Helpers (S4)
# ------------------------------------------------

def get_processing_paper(repo: Repository, workflow_id: int):

    rows = repo.fetch_all(
       """
        SELECT id, workflow_id, title, source, pdf_url, status
        FROM Paper
        WHERE workflow_id = ?
        AND status = 'processing'
        LIMIT 1
        """,
        (workflow_id,)
    )

    if not rows:
        return None

    return dict(rows[0])


def store_paper_text(repo: Repository, paper_id: int, raw_text: str):

    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            UPDATE Paper
            SET raw_text = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (raw_text, timestamp, paper_id)
        )


# ------------------------------------------------
# ResearchKnowledge (S5)
# ------------------------------------------------

def insert_research_knowledge(repo: Repository, paper_id: int, category: str, value: str):

    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO ResearchKnowledge (
                paper_id,
                category,
                value
            )
            VALUES (?, ?, ?);
            """,
            (paper_id, category, value)
        )

        return cursor.lastrowid

def update_paper_file_path(repo, paper_id, file_path):

    with repo.transaction() as cursor:
        cursor.execute(
            """
            UPDATE Paper
            SET pdf_url = ?
            WHERE id = ?
            """,
            (file_path, paper_id)
        )

def get_knowledge_for_paper(repo: Repository, paper_id: int):

    rows = repo.fetch_all(
        """
        SELECT id, paper_id, category, value
        FROM ResearchKnowledge
        WHERE paper_id = ?
        """,
        (paper_id,)
    )

    return [dict(row) for row in rows]
