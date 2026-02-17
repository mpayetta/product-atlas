import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.db import get_connection, init_schema


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


# ---------- Projects ----------

def create_project(name: str, description: str = "") -> str:
    init_schema()
    project_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO projects (id, name, description, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, name, description, _now_iso()),
        )
    return project_id


def list_projects() -> List[Dict[str, Any]]:
    init_schema()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, name, description, created_at
            FROM projects
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    init_schema()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, description, created_at FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
    return dict(row) if row else None


# ---------- Conversations ----------

def create_conversation(project_id: Optional[str] = None, title: str = "") -> str:
    init_schema()
    conv_id = str(uuid.uuid4())
    created_at = _now_iso()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations (id, project_id, title, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (conv_id, project_id, title, created_at),
        )
    return conv_id


def list_conversations(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    init_schema()
    with get_connection() as conn:
        if project_id:
            rows = conn.execute(
                """
                SELECT id, project_id, title, created_at
                FROM conversations
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, project_id, title, created_at
                FROM conversations
                ORDER BY created_at DESC
                """
            ).fetchall()
    return [dict(r) for r in rows]


def get_conversation(conv_id: str) -> Optional[Dict[str, Any]]:
    init_schema()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, project_id, title, created_at
            FROM conversations
            WHERE id = ?
            """,
            (conv_id,),
        ).fetchone()
    return dict(row) if row else None


def update_conversation_title(conv_id: str, new_title: str) -> None:
    init_schema()
    with get_connection() as conn:
        conn.execute(
            "UPDATE conversations SET title = ? WHERE id = ?",
            (new_title, conv_id),
        )

def delete_conversation(conv_id: str) -> None:
    """
    Delete a conversation and all its messages.
    """
    init_schema()
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conv_id,),
        )
        conn.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conv_id,),
        )

# ---------- Messages ----------

def append_message(conv_id: str, role: str, content: str) -> None:
    """
    Append a message to a conversation.
    role: 'user' or 'assistant'
    """
    init_schema()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(MAX(order_index), 0) AS max_idx FROM messages WHERE conversation_id = ?",
            (conv_id,),
        ).fetchone()
        next_idx = (row["max_idx"] or 0) + 1

        conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at, order_index)
            VALUES (?, ?, ?, ?, ?)
            """,
            (conv_id, role, content, _now_iso(), next_idx),
        )


def load_conversation_messages(conv_id: str) -> List[Dict[str, str]]:
    init_schema()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content
            FROM messages
            WHERE conversation_id = ?
            ORDER BY order_index ASC
            """,
            (conv_id,),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]
