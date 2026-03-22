import sqlite3
import sys
from pathlib import Path

# -------------------------------------------------
# Ensure project root is in Python path
# -------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from repositories.repository import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables(conn):

    with conn:

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Workflow (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            current_stage TEXT NOT NULL
                CHECK (current_stage IN ('S1','S2','S3','S4','S5','S5_5','S6','S7')),
            status TEXT NOT NULL
                CHECK (status IN ('running','paused','completed','failed')),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Stage (
            id INTEGER PRIMARY KEY,
            workflow_id INTEGER NOT NULL,
            stage_name TEXT NOT NULL
                CHECK (stage_name IN ('S1','S2','S3','S4','S5','S5_5','S6','S7')),
            status TEXT NOT NULL
                CHECK (status IN ('running','completed','failed')),
            started_at DATETIME,
            ended_at DATETIME,
            FOREIGN KEY (workflow_id)
                REFERENCES Workflow(id)
                ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS ExecutionAttempt (
            id INTEGER PRIMARY KEY,
            stage_id INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL
                CHECK (attempt_number > 0),
            status TEXT NOT NULL
                CHECK (status IN ('running','failed','completed')),
            started_at DATETIME,
            ended_at DATETIME,
            error_message TEXT,
            FOREIGN KEY (stage_id)
                REFERENCES Stage(id)
                ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS Paper (
            id INTEGER PRIMARY KEY,
            workflow_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            file_path TEXT,
            pdf_url TEXT,
            status TEXT NOT NULL
                CHECK (status IN ('pending','downloading','processing','completed','failed')),
            raw_text TEXT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            UNIQUE(workflow_id, title),
            FOREIGN KEY (workflow_id)
                REFERENCES Workflow(id)
                ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS PaperContent (
            id INTEGER PRIMARY KEY,
            paper_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (paper_id)
                REFERENCES Paper(id)
                ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS ResearchKnowledge (
            id INTEGER PRIMARY KEY,
            paper_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            value TEXT NOT NULL,
            section_source TEXT,
            sentence TEXT,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (paper_id)
                REFERENCES Paper(id)
                ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS ResearchRelation (
            id INTEGER PRIMARY KEY,
            paper_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            relation TEXT NOT NULL,
            object TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (paper_id)
                REFERENCES Paper(id)
                ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS DraftSection (
            id INTEGER PRIMARY KEY,
            workflow_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY (workflow_id)
                REFERENCES Workflow(id)
                ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS FinalPaperSection (
            id INTEGER PRIMARY KEY,
            workflow_id INTEGER NOT NULL,
            section_name TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (workflow_id)
                REFERENCES Workflow(id)
                ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS WorkflowResearchConfig (
            id INTEGER PRIMARY KEY,
            workflow_id INTEGER,
            domain TEXT,
            material TEXT,
            structure TEXT,
            focus TEXT,
            method TEXT,
            properties TEXT,
            characterization TEXT,
            use_local INTEGER DEFAULT 0
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS FailureLog (
            id INTEGER PRIMARY KEY,
            workflow_id INTEGER NOT NULL,
            stage_id INTEGER,
            execution_attempt_id INTEGER,
            paper_id INTEGER,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            created_at DATETIME NOT NULL,

            FOREIGN KEY (workflow_id)
                REFERENCES Workflow(id)
                ON DELETE CASCADE,

            FOREIGN KEY (stage_id)
                REFERENCES Stage(id)
                ON DELETE SET NULL,

            FOREIGN KEY (execution_attempt_id)
                REFERENCES ExecutionAttempt(id)
                ON DELETE SET NULL,

            FOREIGN KEY (paper_id)
                REFERENCES Paper(id)
                ON DELETE SET NULL
        );
        """)


if __name__ == "__main__":

    print("Database path:", DB_PATH)

    conn = get_connection()

    print("SQLite version:", sqlite3.sqlite_version)

    fk_status = conn.execute("PRAGMA foreign_keys;").fetchone()[0]
    print("Foreign keys enabled:", fk_status)

    create_tables(conn)

    print("Initialization complete.")

    conn.close()