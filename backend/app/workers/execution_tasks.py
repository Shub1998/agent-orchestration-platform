import json
import re
import uuid
import sqlite3
from datetime import datetime

from app.workers.celery_app import celery_app
from app.core.log_emitter import log_emitter
from app.core.graph_compiler import graph_compiler
from app.core.state import AgentFlowState
from app.config import settings
from langchain_core.messages import HumanMessage


def _sqlite_path() -> str:
    """Derive the raw file path from DATABASE_URL (supports sqlite+aiosqlite:/// prefix)."""
    url = settings.DATABASE_URL
    path = re.sub(r"^sqlite\+aiosqlite:///", "", url)
    return path


def _get_sync_db():
    import os
    path = _sqlite_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return sqlite3.connect(path)


def _load_workflow_sync(workflow_id: str):
    conn = _get_sync_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, description, trigger_type, trigger_config FROM workflows WHERE id=?",
            (workflow_id,),
        )
        row = cur.fetchone()
        if not row:
            return None, [], [], {}
        workflow = {"id": row[0], "name": row[1], "description": row[2], "trigger_type": row[3]}

        cur.execute(
            "SELECT id, workflow_id, agent_id, node_type, label, position_x, position_y, config "
            "FROM workflow_nodes WHERE workflow_id=?",
            (workflow_id,),
        )
        nodes = [
            {"id": r[0], "workflow_id": r[1], "agent_id": r[2], "node_type": r[3],
             "label": r[4], "position_x": r[5], "position_y": r[6], "config": r[7]}
            for r in cur.fetchall()
        ]

        cur.execute(
            "SELECT id, workflow_id, source_node_id, target_node_id, condition, label "
            "FROM workflow_edges WHERE workflow_id=?",
            (workflow_id,),
        )
        edges = [
            {"id": r[0], "workflow_id": r[1], "source_node_id": r[2], "target_node_id": r[3],
             "condition": r[4], "label": r[5]}
            for r in cur.fetchall()
        ]

        agent_ids = [n["agent_id"] for n in nodes if n.get("agent_id")]
        agent_map = {}
        for aid in agent_ids:
            cur.execute(
                "SELECT id, name, role, system_prompt, model, provider, temperature, "
                "max_iterations, memory_enabled, tools, max_output_tokens, guardrail_keywords "
                "FROM agents WHERE id=?",
                (aid,),
            )
            ar = cur.fetchone()
            if ar:
                agent_map[ar[0]] = {
                    "id": ar[0], "name": ar[1], "role": ar[2], "system_prompt": ar[3],
                    "model": ar[4], "provider": ar[5], "temperature": ar[6],
                    "max_iterations": ar[7], "memory_enabled": bool(ar[8]),
                    "tools": json.loads(ar[9]) if ar[9] else [],
                    "max_output_tokens": ar[10] or 4096,
                    "guardrail_keywords": json.loads(ar[11]) if ar[11] else [],
                }

        return workflow, nodes, edges, agent_map
    finally:
        conn.close()


def _update_execution_sync(
    execution_id: str,
    status: str,
    output: str = None,
    error: str = None,
    celery_task_id: str = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float = 0.0,
):
    conn = _get_sync_db()
    try:
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        if status == "running" and celery_task_id:
            # Initial start: set started_at and task ID
            cur.execute(
                "UPDATE executions SET status=?, started_at=?, celery_task_id=? WHERE id=?",
                (status, now, celery_task_id, execution_id),
            )
        elif status == "running":
            # Resume after approval: only update status and task ID, preserve original started_at
            cur.execute(
                "UPDATE executions SET status=?, celery_task_id=? WHERE id=?",
                (status, celery_task_id, execution_id),
            )
        elif status == "awaiting_approval":
            cur.execute(
                "UPDATE executions SET status=?, final_output=? WHERE id=?",
                (status, output, execution_id),
            )
        elif status in ("completed", "failed", "cancelled"):
            cur.execute(
                "UPDATE executions SET status=?, completed_at=?, final_output=?, error_message=?, "
                "total_input_tokens=?, total_output_tokens=?, total_cost_usd=? WHERE id=?",
                (status, now, output, error, input_tokens, output_tokens, cost_usd, execution_id),
            )
        conn.commit()
    finally:
        conn.close()


def _save_log_sync(execution_id: str, level: str, message: str,
                   agent_id: str = None, agent_name: str = None):
    conn = _get_sync_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO execution_logs "
            "(id, execution_id, agent_id, agent_name, level, message, metadata, timestamp) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), execution_id, agent_id, agent_name,
             level, message, "{}", datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def _sum_token_usage_from_logs(execution_id: str) -> tuple[int, int, float]:
    conn = _get_sync_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT metadata FROM execution_logs WHERE execution_id=? AND level='llm_end'",
            (execution_id,),
        )
        total_in = total_out = 0
        total_cost = 0.0
        for (meta_str,) in cur.fetchall():
            try:
                meta = json.loads(meta_str) if meta_str else {}
                total_in += int(meta.get("input_tokens", 0))
                total_out += int(meta.get("output_tokens", 0))
                total_cost += float(meta.get("cost_usd", 0.0))
            except Exception:
                pass
        return total_in, total_out, round(total_cost, 6)
    finally:
        conn.close()


def _send_telegram_reply(chat_id: int, message: str):
    try:
        import httpx
        if not settings.TELEGRAM_BOT_TOKEN:
            return
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        with httpx.Client(timeout=15) as client:
            client.post(url, json={"chat_id": chat_id, "text": message[:4096]})
    except Exception:
        pass


def _finalize_execution(execution_id: str, final_state: dict, telegram_chat_id=None):
    """Persist completion state and optionally reply via Telegram."""
    output = final_state.get("output", "")
    total_in, total_out, total_cost = _sum_token_usage_from_logs(execution_id)

    _save_log_sync(
        execution_id, "info",
        f"Workflow completed — total: {total_in} input / {total_out} output tokens (${total_cost:.4f})",
    )
    log_emitter.emit(
        execution_id, "info",
        f"Total tokens: {total_in} in / {total_out} out | Cost: ${total_cost:.4f}",
        metadata={"input_tokens": total_in, "output_tokens": total_out, "cost_usd": total_cost},
    )
    _update_execution_sync(
        execution_id, "completed", output=output,
        input_tokens=total_in, output_tokens=total_out, cost_usd=total_cost,
    )
    log_emitter.emit_completion(execution_id, "completed", output=output)

    if telegram_chat_id and output:
        _send_telegram_reply(telegram_chat_id, output)

    return output


@celery_app.task(bind=True, max_retries=2, name="run_workflow")
def run_workflow_task(self, workflow_id: str, execution_id: str, input_data: dict):
    from langgraph.errors import GraphInterrupt

    try:
        _update_execution_sync(execution_id, "running", celery_task_id=self.request.id)
        log_emitter.emit(execution_id, "info", "Starting workflow execution",
                         metadata={"workflow_id": workflow_id})

        workflow, nodes, edges, agent_map = _load_workflow_sync(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        agent_nodes = [n for n in nodes if n["node_type"] == "agent" and n.get("agent_id")]
        if not agent_nodes:
            raise ValueError("Workflow has no agent nodes")

        log_emitter.emit(
            execution_id, "info",
            f"Loaded {len(agent_nodes)} agent(s): "
            + ", ".join(agent_map[n["agent_id"]]["name"] for n in agent_nodes if n["agent_id"] in agent_map),
        )

        compiled = graph_compiler.compile(workflow, nodes, edges, agent_map)
        prompt = input_data.get("prompt", "")
        telegram_chat_id = input_data.get("chat_id")

        initial_state = AgentFlowState(
            messages=[HumanMessage(content=prompt)],
            current_agent="",
            execution_id=execution_id,
            workflow_id=workflow_id,
            input=prompt,
            output="",
            iteration=0,
            context=input_data.get("context", {}),
            error=None,
            telegram_chat_id=telegram_chat_id,
        )

        config = {"configurable": {"thread_id": execution_id}}

        try:
            final_state = compiled.invoke(initial_state, config=config)
        except GraphInterrupt:
            # Graph paused at an approval node — update DB and let the UI know.
            # resume_workflow_task will be dispatched by the /approve API endpoint.
            import sqlite3 as _sqlite3
            current_output = ""
            try:
                conn = _get_sync_db()
                cur = conn.cursor()
                cur.execute("SELECT final_output FROM executions WHERE id=?", (execution_id,))
                row = cur.fetchone()
                current_output = (row[0] or "") if row else ""
                conn.close()
            except Exception:
                pass

            _update_execution_sync(execution_id, "awaiting_approval", output=current_output)
            log_emitter.emit_completion(execution_id, "awaiting_approval")
            return {"status": "awaiting_approval", "execution_id": execution_id}

        _finalize_execution(execution_id, final_state, telegram_chat_id)
        return {"status": "completed", "output": final_state.get("output", "")}

    except Exception as exc:
        error_msg = str(exc)
        _save_log_sync(execution_id, "error", f"Workflow failed: {error_msg}")
        _update_execution_sync(execution_id, "failed", error=error_msg)
        log_emitter.emit_completion(execution_id, "failed", error=error_msg)
        raise


@celery_app.task(bind=True, max_retries=2, name="resume_workflow")
def resume_workflow_task(self, workflow_id: str, execution_id: str, decision: str, comment: str = ""):
    """Resume a workflow that was paused at an approval node."""
    from langgraph.errors import GraphInterrupt
    from langgraph.types import Command

    try:
        _update_execution_sync(execution_id, "running", celery_task_id=self.request.id)
        log_emitter.emit(
            execution_id, "info",
            f"Resuming workflow after approval decision: {decision}",
            metadata={"decision": decision, "comment": comment},
        )

        workflow, nodes, edges, agent_map = _load_workflow_sync(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        compiled = graph_compiler.compile(workflow, nodes, edges, agent_map)
        config = {"configurable": {"thread_id": execution_id}}

        resume_payload = {"decision": decision, "comment": comment}

        try:
            final_state = compiled.invoke(Command(resume=resume_payload), config=config)
        except GraphInterrupt:
            # Another approval node in the same workflow
            import sqlite3 as _sqlite3
            current_output = ""
            try:
                conn = _get_sync_db()
                cur = conn.cursor()
                cur.execute("SELECT final_output FROM executions WHERE id=?", (execution_id,))
                row = cur.fetchone()
                current_output = (row[0] or "") if row else ""
                conn.close()
            except Exception:
                pass

            _update_execution_sync(execution_id, "awaiting_approval", output=current_output)
            log_emitter.emit_completion(execution_id, "awaiting_approval")
            return {"status": "awaiting_approval", "execution_id": execution_id}

        telegram_chat_id = final_state.get("telegram_chat_id")
        _finalize_execution(execution_id, final_state, telegram_chat_id)
        return {"status": "completed", "output": final_state.get("output", "")}

    except Exception as exc:
        error_msg = str(exc)
        _save_log_sync(execution_id, "error", f"Workflow failed on resume: {error_msg}")
        _update_execution_sync(execution_id, "failed", error=error_msg)
        log_emitter.emit_completion(execution_id, "failed", error=error_msg)
        raise
