from datetime import datetime
from repositories.repository import Repository


# ----------------------------
# R4 — ExecutionAttempt Repository
# ----------------------------

def create_execution_attempt(
    repo: Repository,
    stage_id: int,
    attempt_number: int,
    status: str
) -> int:
    """
    Creates a new ExecutionAttempt.

    - started_at set at creation
    - ended_at initially NULL
    - error_message initially NULL

    Returns:
        int: Newly created execution_attempt ID
    """
    started_at = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO ExecutionAttempt (
                stage_id,
                attempt_number,
                status,
                started_at,
                ended_at,
                error_message
            )
            VALUES (?, ?, ?, ?, NULL, NULL);
            """,
            (stage_id, attempt_number, status, started_at)
        )

        return cursor.lastrowid


def update_execution_attempt_status(
    repo: Repository,
    execution_attempt_id: int,
    new_status: str,
    error_message: str | None = None
) -> None:
    """
    Updates ExecutionAttempt status.

    - If status becomes 'completed' or 'failed',
      ended_at is set.
    - If failed, error_message may be stored.
    """
    ended_at = None

    if new_status in ("completed", "failed"):
        ended_at = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        if ended_at:
            cursor.execute(
                """
                UPDATE ExecutionAttempt
                SET status = ?,
                    ended_at = ?,
                    error_message = ?
                WHERE id = ?;
                """,
                (new_status, ended_at, error_message, execution_attempt_id)
            )
        else:
            cursor.execute(
                """
                UPDATE ExecutionAttempt
                SET status = ?
                WHERE id = ?;
                """,
                (new_status, execution_attempt_id)
            )

        if cursor.rowcount == 0:
            raise ValueError(
                f"ExecutionAttempt ID {execution_attempt_id} does not exist."
            )


# ----------------------------
# R4 — Read Methods (Minimal)
# ----------------------------

def get_latest_attempt_for_stage(
    repo: Repository,
    stage_id: int
) -> dict | None:
    """
    Retrieves the most recent ExecutionAttempt for a stage.
    Deterministic ordering by attempt_number DESC.
    """
    with repo.transaction() as cursor:
        cursor.execute(
            """
            SELECT id, stage_id, attempt_number, status,
                   started_at, ended_at, error_message
            FROM ExecutionAttempt
            WHERE stage_id = ?
            ORDER BY attempt_number DESC
            LIMIT 1;
            """,
            (stage_id,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "stage_id": row[1],
            "attempt_number": row[2],
            "status": row[3],
            "started_at": row[4],
            "ended_at": row[5],
            "error_message": row[6],
        }