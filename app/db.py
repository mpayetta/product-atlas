import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

# Resolve DB path from env
PRODUCT_ATLAS_DB = os.getenv("PRODUCT_ATLAS_DB", "data/product_atlas.db")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH_ABS = os.path.join(BASE_DIR, PRODUCT_ATLAS_DB)
os.makedirs(os.path.dirname(DB_PATH_ABS), exist_ok=True)


def init_schema() -> None:
    """
    Create tables if they don't exist.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # Projects
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        # Conversations
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                project_id TEXT NULL,
                title TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
            """
        )

        # Messages
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,             -- 'user' or 'assistant'
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                order_index INTEGER NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
            """
        )

        conn.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """
    Context-managed connection with row_factory set to sqlite3.Row.
    """
    conn = sqlite3.connect(DB_PATH_ABS)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
