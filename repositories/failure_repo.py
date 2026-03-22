from datetime import datetime
from repositories.repository import Repository


# ----------------------------
# R6 — FailureLog Repository
# ----------------------------

def log_failure(
    repo: Repository,
    workflow_id: int,
    error_type: str,
    error_message: str,
    stage_id: int | None = None,
    execution_attempt_id: int | None = None,
    paper_id: int | None = None
) -> int:
    """
    Inserts a failure log entry.

    Returns:
        int: Newly created failure log ID
    """
    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO FailureLog (
                workflow_id,
                stage_id,
                execution_attempt_id,
                paper_id,
                error_type,
                error_message,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                workflow_id,
                stage_id,
                execution_attempt_id,
                paper_id,
                error_type,
                error_message,
                timestamp
            )
        )

        return cursor.lastrowid