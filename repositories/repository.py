import sqlite3
from pathlib import Path
from contextlib import contextmanager


# Always resolve DB path relative to project root
DB_PATH = Path(__file__).resolve().parents[1] / "database" / "research_workflow.db"


class Repository:
    """
    Controlled SQLite repository layer (v1.0 - Hardened)

    Guarantees:
    - Single connection
    - Explicit transaction control (no implicit SQLite behavior)
    - Foreign keys enforced and verified
    - No SQL leakage
    - Deterministic error propagation
    """

    def __init__(self, db_path: str | None = None):

        if db_path is None:
            db_path = DB_PATH

        # Disable implicit transaction management
        self._conn = sqlite3.connect(
            db_path,
            isolation_level=None  # Full manual transaction control
        )

        # Enable foreign key enforcement
        self._conn.execute("PRAGMA foreign_keys = ON;")

        # Verify foreign key enforcement actually enabled
        fk_status = self._conn.execute("PRAGMA foreign_keys;").fetchone()[0]
        if fk_status != 1:
            raise RuntimeError("Foreign key enforcement failed to enable.")

        # Access rows as dict-like objects
        self._conn.row_factory = sqlite3.Row

    # ----------------------------
    # Explicit Transaction Manager
    # ----------------------------

    @contextmanager
    def transaction(self):
        """
        Deterministic transaction boundary.
        - Explicit BEGIN
        - Explicit COMMIT
        - Explicit ROLLBACK
        - No silent failures
        """
        cursor = self._conn.cursor()
        try:
            cursor.execute("BEGIN;")
            yield cursor
            cursor.execute("COMMIT;")
        except Exception:
            cursor.execute("ROLLBACK;")
            raise
        finally:
            cursor.close()

    # ----------------------------
    # Read Helpers (No Transactions)
    # ----------------------------

    def fetch_one(self, query: str, params: tuple = ()):
        cursor = self._conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            cursor.close()

    def fetch_all(self, query: str, params: tuple = ()):
        cursor = self._conn.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    # ----------------------------
    # Lifecycle Management
    # ----------------------------

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()