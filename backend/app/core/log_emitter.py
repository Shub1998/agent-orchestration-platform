import json
import re
import uuid
import sqlite3
import os
from datetime import datetime
import redis as sync_redis
from app.config import settings


def _db_path() -> str:
    return re.sub(r"^sqlite\+aiosqlite:///", "", settings.DATABASE_URL)


class LogEmitter:
    """Emits execution log events to Redis pub/sub AND persists them to SQLite."""

    def __init__(self):
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            self._redis = sync_redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._redis

    def _persist(self, execution_id: str, level: str, message: str,
                 agent_id: str, agent_name: str, node_id: str, metadata: dict,
                 timestamp: str):
        try:
            db_path = _db_path()
            if not os.path.exists(db_path):
                return
            conn = sqlite3.connect(db_path)
            conn.execute(
                "INSERT INTO execution_logs (id, execution_id, agent_id, agent_name, node_id, level, message, metadata, timestamp) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), execution_id, agent_id, agent_name, node_id,
                 level, message, json.dumps(metadata or {}), timestamp)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def emit(
        self,
        execution_id: str,
        level: str,
        message: str,
        agent_id: str = None,
        agent_name: str = None,
        node_id: str = None,
        metadata: dict = None,
    ):
        # Single timestamp used for both Redis publish and SQLite persist so
        # the REST-log / WS-log deduplication fingerprint (timestamp|message) matches.
        now = datetime.utcnow().isoformat()
        event = {
            "type": "log",
            "execution_id": execution_id,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "node_id": node_id,
            "level": level,
            "message": message,
            "metadata": metadata or {},
            "timestamp": now,
        }
        try:
            r = self._get_redis()
            r.publish(f"execution:{execution_id}:logs", json.dumps(event))
        except Exception:
            pass
        self._persist(execution_id, level, message, agent_id, agent_name, node_id, metadata, now)

    def emit_completion(self, execution_id: str, status: str, output: str = None, error: str = None):
        event = {
            "type": "execution_complete",
            "execution_id": execution_id,
            "status": status,
            "output": output,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            r = self._get_redis()
            r.publish(f"execution:{execution_id}:logs", json.dumps(event))
        except Exception:
            pass


log_emitter = LogEmitter()
