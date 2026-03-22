from datetime import datetime
from repositories.repository import Repository


# ----------------------------
# R3 — Stage Repository
# ----------------------------

def create_stage(repo: Repository, workflow_id: int, stage_name: str, status: str) -> int:
    """
    Creates a new Stage row.

    - started_at is set at creation.
    - ended_at is initially NULL.

    Returns:
        int: Newly created stage ID
    """

    started_at = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:
        cursor.execute(
            """
            INSERT INTO Stage (
                workflow_id,
                stage_name,
                status,
                started_at,
                ended_at
            )
            VALUES (?, ?, ?, ?, NULL);
            """,
            (workflow_id, stage_name, status, started_at)
        )

        return cursor.lastrowid


def update_stage_status(repo: Repository, stage_id: int, new_status: str) -> None:
    """
    Updates Stage status.

    - If status becomes 'completed' or 'failed',
      ended_at is set.
    """

    ended_at = None

    if new_status in ("completed", "failed"):
        ended_at = datetime.utcnow().isoformat()

    with repo.transaction() as cursor:

        if ended_at:
            cursor.execute(
                """
                UPDATE Stage
                SET status = ?, ended_at = ?
                WHERE id = ?;
                """,
                (new_status, ended_at, stage_id)
            )
        else:
            cursor.execute(
                """
                UPDATE Stage
                SET status = ?
                WHERE id = ?;
                """,
                (new_status, stage_id)
            )

        if cursor.rowcount == 0:
            raise ValueError(f"Stage ID {stage_id} does not exist.")


def get_stage_by_id(repo: Repository, stage_id: int) -> dict | None:
    """
    Retrieves Stage by ID.
    """

    row = repo.fetch_one(
        """
        SELECT id, workflow_id, stage_name, status, started_at, ended_at
        FROM Stage
        WHERE id = ?;
        """,
        (stage_id,)
    )

    if not row:
        return None

    return dict(row)


def get_stage_by_workflow_and_name(
    repo: Repository,
    workflow_id: int,
    stage_name: str
) -> dict | None:
    """
    Retrieves Stage by workflow and stage name.
    """

    row = repo.fetch_one(
        """
        SELECT id, workflow_id, stage_name, status, started_at, ended_at
        FROM Stage
        WHERE workflow_id = ?
        AND stage_name = ?;
        """,
        (workflow_id, stage_name)
    )

    if not row:
        return None

    return dict(row)
