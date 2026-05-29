"""
Tests for the Celery execution task logic.
These tests exercise _load_workflow_sync, _sum_token_usage_from_logs,
and the full run_workflow_task flow using an in-memory SQLite DB.
"""
import json
import sqlite3
import uuid
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from langchain_core.messages import AIMessage


# ---------- helpers ----------

def _make_db(tmp_path) -> str:
    """Create a minimal SQLite DB at tmp_path and return the path string."""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE workflows (
            id TEXT PRIMARY KEY, name TEXT, description TEXT,
            trigger_type TEXT, trigger_config TEXT, is_active INTEGER DEFAULT 1
        );
        CREATE TABLE workflow_nodes (
            id TEXT PRIMARY KEY, workflow_id TEXT, agent_id TEXT,
            node_type TEXT, label TEXT, position_x REAL, position_y REAL, config TEXT
        );
        CREATE TABLE workflow_edges (
            id TEXT PRIMARY KEY, workflow_id TEXT, source_node_id TEXT,
            target_node_id TEXT, condition TEXT, label TEXT
        );
        CREATE TABLE agents (
            id TEXT PRIMARY KEY, name TEXT, role TEXT, system_prompt TEXT,
            model TEXT, provider TEXT, temperature REAL, max_iterations INTEGER,
            memory_enabled INTEGER, tools TEXT, max_output_tokens INTEGER, guardrail_keywords TEXT
        );
        CREATE TABLE executions (
            id TEXT PRIMARY KEY, workflow_id TEXT, status TEXT, trigger_type TEXT,
            trigger_payload TEXT, final_output TEXT, error_message TEXT,
            started_at TEXT, completed_at TEXT, celery_task_id TEXT,
            total_input_tokens INTEGER DEFAULT 0, total_output_tokens INTEGER DEFAULT 0,
            total_cost_usd REAL DEFAULT 0.0, created_at TEXT
        );
        CREATE TABLE execution_logs (
            id TEXT PRIMARY KEY, execution_id TEXT, agent_id TEXT, agent_name TEXT,
            node_id TEXT, level TEXT, message TEXT, metadata TEXT, timestamp TEXT
        );
    """)
    conn.commit()
    conn.close()
    return db_path


def _seed_workflow(db_path: str) -> tuple[str, str, str]:
    """Insert a minimal one-agent workflow and return (wf_id, agent_id, exec_id)."""
    wf_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    node_id = str(uuid.uuid4())
    exec_id = str(uuid.uuid4())

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO workflows VALUES (?,?,?,?,?,1)",
        (wf_id, "Test WF", "", "manual", "{}"),
    )
    conn.execute(
        "INSERT INTO agents VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (agent_id, "T Agent", "assistant", "You help.", "demo", "demo",
         0.7, 3, 1, "[]", 1024, "[]"),
    )
    start_id, end_id = str(uuid.uuid4()), str(uuid.uuid4())
    conn.execute(
        "INSERT INTO workflow_nodes VALUES (?,?,?,?,?,?,?,?)",
        (start_id, wf_id, None, "start", "Start", 0, 0, "{}"),
    )
    conn.execute(
        "INSERT INTO workflow_nodes VALUES (?,?,?,?,?,?,?,?)",
        (node_id, wf_id, agent_id, "agent", "T Agent", 200, 0, "{}"),
    )
    conn.execute(
        "INSERT INTO workflow_nodes VALUES (?,?,?,?,?,?,?,?)",
        (end_id, wf_id, None, "end", "End", 400, 0, "{}"),
    )
    conn.execute(
        "INSERT INTO workflow_edges VALUES (?,?,?,?,?,?)",
        (str(uuid.uuid4()), wf_id, start_id, node_id, None, ""),
    )
    conn.execute(
        "INSERT INTO workflow_edges VALUES (?,?,?,?,?,?)",
        (str(uuid.uuid4()), wf_id, node_id, end_id, None, ""),
    )
    conn.execute(
        "INSERT INTO executions VALUES (?,?,?,?,?,?,?,?,?,?,0,0,0.0,?)",
        (exec_id, wf_id, "pending", "manual", "{}", None, None,
         None, None, None, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()
    return wf_id, agent_id, exec_id


# ---------- tests ----------

def test_load_workflow_sync(tmp_path):
    db_path = _make_db(tmp_path)
    wf_id, agent_id, _ = _seed_workflow(db_path)

    from app.workers import execution_tasks

    with patch.object(execution_tasks, "_sqlite_path", return_value=db_path):
        workflow, nodes, edges, agent_map = execution_tasks._load_workflow_sync(wf_id)

    assert workflow is not None
    assert workflow["name"] == "Test WF"
    assert len(nodes) == 3
    assert len(edges) == 2
    assert agent_id in agent_map
    assert agent_map[agent_id]["name"] == "T Agent"


def test_load_workflow_not_found(tmp_path):
    db_path = _make_db(tmp_path)
    from app.workers import execution_tasks

    with patch.object(execution_tasks, "_sqlite_path", return_value=db_path):
        workflow, nodes, edges, agent_map = execution_tasks._load_workflow_sync("nonexistent")

    assert workflow is None
    assert nodes == []


def test_sum_token_usage_from_logs(tmp_path):
    db_path = _make_db(tmp_path)
    _, _, exec_id = _seed_workflow(db_path)

    # Insert fake llm_end log entries
    conn = sqlite3.connect(db_path)
    for i in range(3):
        conn.execute(
            "INSERT INTO execution_logs VALUES (?,?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), exec_id, None, None, None, "llm_end", "done",
             json.dumps({"input_tokens": 100, "output_tokens": 50, "cost_usd": 0.002}),
             datetime.utcnow().isoformat()),
        )
    conn.commit()
    conn.close()

    from app.workers import execution_tasks
    with patch.object(execution_tasks, "_sqlite_path", return_value=db_path):
        total_in, total_out, total_cost = execution_tasks._sum_token_usage_from_logs(exec_id)

    assert total_in == 300
    assert total_out == 150
    assert abs(total_cost - 0.006) < 1e-9


def test_run_workflow_task_completes(tmp_path):
    """End-to-end: run_workflow_task with DemoLLM completes successfully."""
    db_path = _make_db(tmp_path)
    wf_id, _, exec_id = _seed_workflow(db_path)

    from app.workers import execution_tasks

    mock_self = MagicMock()
    mock_self.request.id = "celery-test-id"

    with patch.object(execution_tasks, "_sqlite_path", return_value=db_path), \
         patch("app.core.log_emitter.log_emitter.emit"), \
         patch("app.core.log_emitter.log_emitter.emit_completion"), \
         patch("app.core.log_emitter.log_emitter._persist"), \
         patch("app.core.memory_manager.memory_manager.retrieve", return_value=""), \
         patch("app.core.memory_manager.memory_manager.store"):

        result = execution_tasks.run_workflow_task(
            mock_self, wf_id, exec_id, {"prompt": "hello"}
        )

    assert result["status"] == "completed"
    assert result["output"] != ""

    # Verify the DB was updated
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT status FROM executions WHERE id=?", (exec_id,)).fetchone()
    conn.close()
    assert row[0] == "completed"
