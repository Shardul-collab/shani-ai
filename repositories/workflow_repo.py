from datetime import datetime
from repositories.repository import Repository


# ----------------------------
# R2 — Workflow Repository
# ----------------------------

def create_workflow(repo: Repository, name: str, current_stage: str, status: str) -> int:
    """
    Creates a new Workflow row.

    Returns:
        int: Newly created workflow ID

    Raises:
        sqlite3.IntegrityError if constraints fail.
    """
    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO Workflow (
                name,
                current_stage,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?);
            """,
            (name, current_stage, status, timestamp, timestamp)
        )

        return cursor.lastrowid


def update_workflow_status(repo: Repository, workflow_id: int, new_status: str) -> None:
    """
    Updates workflow status and refreshes updated_at timestamp.
    """
    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            UPDATE Workflow
            SET status = ?,
                updated_at = ?
            WHERE id = ?;
            """,
            (new_status, timestamp, workflow_id)
        )

        if cursor.rowcount == 0:
            raise ValueError(f"Workflow ID {workflow_id} does not exist.")


def update_current_stage(repo: Repository, workflow_id: int, new_stage: str) -> None:
    """
    Updates workflow current_stage and refreshes updated_at timestamp.
    """
    timestamp = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            UPDATE Workflow
            SET current_stage = ?,
                updated_at = ?
            WHERE id = ?;
            """,
            (new_stage, timestamp, workflow_id)
        )

        if cursor.rowcount == 0:
            raise ValueError(f"Workflow ID {workflow_id} does not exist.")


# ----------------------------
# R2 — Read Methods (Minimal)
# ----------------------------

def get_workflow(repo: Repository, workflow_id: int) -> dict | None:
    """
    Retrieves workflow by ID.

    Returns:
        dict | None
    """
    with repo.transaction() as cursor:
        cursor.execute(
            """
            SELECT id, name, current_stage, status, created_at, updated_at
            FROM Workflow
            WHERE id = ?;
            """,
            (workflow_id,)
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "current_stage": row[2],
            "status": row[3],
            "created_at": row[4],
            "updated_at": row[5],
        }