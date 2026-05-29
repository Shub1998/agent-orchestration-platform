import sqlite3
import json
import os


def find_workflow_for_chat(chat_id: int) -> dict | None:
    """Find a telegram-enabled workflow for the given chat_id."""
    db_path = "./data/agentflow.db"
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
    db_path = "./data/agentflow.db"
    execution_id = str(uuid.uuid4())
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        payload = json.dumps({"prompt": text, "chat_id": chat_id, "source": "telegram"})
        cur.execute(
            "INSERT INTO executions (id, workflow_id, status, trigger_type, trigger_payload, created_at) VALUES (?,?,?,?,?,?)",
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
