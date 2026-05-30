import sqlite3
import json
import os
from app.workers.execution_tasks import _sqlite_path


def find_workflow_for_chat(chat_id: int) -> dict | None:
    """Find a telegram-enabled workflow for the given chat_id."""
    db_path = _sqlite_path()
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, name, trigger_config FROM workflows WHERE trigger_type='telegram' AND is_active=1")
        for row in cur.fetchall():
            workflow_id, name, trigger_config_str = row
            try:
                config = json.loads(trigger_config_str) if trigger_config_str else {}
                allowed_chats = config.get("chat_ids", [])
                if not allowed_chats or chat_id in allowed_chats:
                    return {"id": workflow_id, "name": name}
            except Exception:
                continue
        cur.execute("SELECT id, name FROM workflows WHERE is_active=1 ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return {"id": row[0], "name": row[1]}
        return None
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def create_execution(workflow_id: str, chat_id: int, text: str) -> str | None:
    """Create an execution record for a Telegram-triggered workflow."""
    import uuid
    from datetime import datetime
    db_path = _sqlite_path()
    execution_id = str(uuid.uuid4())
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        payload = json.dumps({"prompt": text, "chat_id": chat_id, "source": "telegram"})
        cur.execute(
            "INSERT INTO executions "
            "(id, workflow_id, status, trigger_type, trigger_payload, created_at, "
            "total_input_tokens, total_output_tokens, total_cost_usd) "
            "VALUES (?,?,?,?,?,?,0,0,0.0)",
            (execution_id, workflow_id, "pending", "telegram", payload, datetime.utcnow().isoformat())
        )
        conn.commit()
        return execution_id
    except Exception as e:
        print(f"Failed to create execution: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_agents_sync() -> list[dict]:
    """Return all agents from the database."""
    db_path = _sqlite_path()
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, name, role, description FROM agents ORDER BY name")
        return [{"id": r[0], "name": r[1], "role": r[2], "description": r[3] or ""} for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def list_workflows_sync() -> list[dict]:
    """Return all active workflows from the database."""
    db_path = _sqlite_path()
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, name, description FROM workflows WHERE is_active=1 ORDER BY name")
        return [{"id": r[0], "name": r[1], "description": r[2] or ""} for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_execution_workflow_sync(execution_id: str) -> dict | None:
    """Return workflow_id and chat_id for an execution."""
    db_path = _sqlite_path()
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT workflow_id, trigger_payload FROM executions WHERE id=?", (execution_id,))
        row = cur.fetchone()
        if not row:
            return None
        chat_id = None
        if row[1]:
            try:
                chat_id = json.loads(row[1]).get("chat_id")
            except Exception:
                pass
        return {"workflow_id": row[0], "chat_id": chat_id}
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_workflow_sync(workflow_id: str) -> dict | None:
    """Fetch a single workflow by ID."""
    db_path = _sqlite_path()
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, name, description FROM workflows WHERE id=?", (workflow_id,))
        row = cur.fetchone()
        return {"id": row[0], "name": row[1], "description": row[2] or ""} if row else None
    except Exception:
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass
