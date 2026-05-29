import json
import time
import os
from langgraph.graph import StateGraph, END
from app.core.state import AgentFlowState
from app.core.agent_builder import agent_builder
from app.core.log_emitter import log_emitter
from app.config import settings


def _get_checkpointer():
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        os.makedirs(os.path.dirname(settings.CHECKPOINTER_DB_PATH) or ".", exist_ok=True)
        return SqliteSaver.from_conn_string(settings.CHECKPOINTER_DB_PATH)
    except ImportError:
        pass
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()


def _resolve_target(target_id: str, end_node_ids: set) -> str:
    return END if target_id in end_node_ids else target_id


def _make_approval_node(node_id: str, label: str, config: dict):
    """Return a callable that pauses until a human approves/rejects via Redis."""
    timeout = int((config or {}).get("timeout_seconds", 3600))
    description = (config or {}).get("description", "")

    def approval_node(state: AgentFlowState) -> dict:
        import redis as _redis
        import sqlite3

        execution_id = state.get("execution_id", "")
        redis_key = f"approval:{execution_id}"

        # Mark execution as awaiting approval in DB
        db_path = "./data/agentflow.db"
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("UPDATE executions SET status='awaiting_approval' WHERE id=?", (execution_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass

        msg = f"⏸ [{label}] Waiting for human approval"
        if description:
            msg += f": {description}"
        log_emitter.emit(execution_id, "approval", msg,
                         metadata={"node_id": node_id, "approval_required": True})

        r = _redis.from_url(settings.REDIS_URL, decode_responses=True)
        deadline = time.time() + timeout
        while time.time() < deadline:
            decision = r.get(redis_key)
            if decision:
                r.delete(redis_key)
                comment_key = f"approval_comment:{execution_id}"
                comment = r.get(comment_key) or ""
                r.delete(comment_key)

                # Restore running status
                try:
                    conn = sqlite3.connect(db_path)
                    conn.execute("UPDATE executions SET status='running' WHERE id=?", (execution_id,))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

                if decision == "approve":
                    log_emitter.emit(execution_id, "approval", f"✅ [{label}] Approved — continuing workflow")
                    ctx = dict(state.get("context") or {})
                    ctx["approval"] = "approved"
                    return {"approval_decision": "approved", "rejection_comment": None, "context": ctx}
                else:
                    reason = f" Reason: {comment}" if comment else ""
                    log_emitter.emit(execution_id, "approval",
                                     f"❌ [{label}] Rejected — routing back for revision.{reason}")
                    return {"approval_decision": "rejected", "rejection_comment": comment or ""}
            time.sleep(3)

        log_emitter.emit(execution_id, "approval", f"⏰ [{label}] Approval timed out after {timeout}s")
        return {"error": f"Approval timed out at step '{label}'"}

    return approval_node


def _make_router_node():
    """A passthrough node; routing logic is purely on outgoing conditional edges."""
    def router_node(state: AgentFlowState) -> dict:
        return {}
    return router_node


class GraphCompiler:
    def compile(self, workflow: dict, nodes: list[dict], edges: list[dict], agent_map: dict[str, dict]):
        builder = StateGraph(AgentFlowState)

        end_node_ids   = {n["id"] for n in nodes if n["node_type"] == "end"}
        start_nodes    = [n for n in nodes if n["node_type"] == "start"]
        agent_nodes    = [n for n in nodes if n["node_type"] == "agent"]
        approval_nodes = [n for n in nodes if n["node_type"] == "approval"]
        router_nodes   = [n for n in nodes if n["node_type"] == "router"]

        # Register agent nodes
        for node in agent_nodes:
            agent_data = agent_map.get(node.get("agent_id", ""))
            if not agent_data:
                continue
            builder.add_node(node["id"], agent_builder.build(agent_data))

        # Register approval nodes
        for node in approval_nodes:
            import json as _json
            raw_config = node.get("config") or {}
            cfg = _json.loads(raw_config) if isinstance(raw_config, str) else raw_config
            builder.add_node(node["id"], _make_approval_node(node["id"], node.get("label", "Approval"), cfg))

        # Register router nodes (passthrough)
        for node in router_nodes:
            builder.add_node(node["id"], _make_router_node())

        # Wire edges for all non-start/non-end nodes
        all_active = agent_nodes + approval_nodes + router_nodes
        start_node_ids = {n["id"] for n in start_nodes}

        # Set entry point: follow edge from any start node; fall back to first registered node
        entry_set = False
        for start in start_nodes:
            first_edges = [e for e in edges if e["source_node_id"] == start["id"]]
            for edge in first_edges:
                target = edge["target_node_id"]
                if target not in end_node_ids:
                    builder.set_entry_point(target)
                    entry_set = True
                    break
            if entry_set:
                break

        if not entry_set:
            for node in all_active:
                builder.set_entry_point(node["id"])
                break

        for node in all_active:
            outgoing = [e for e in edges if e["source_node_id"] == node["id"]]

            # Approval nodes get conditional routing: approved → successor, rejected → predecessor
            if node["node_type"] == "approval":
                incoming = [e for e in edges if e["target_node_id"] == node["id"]]
                predecessor_id = None
                for inc in incoming:
                    if inc["source_node_id"] not in start_node_ids:
                        predecessor_id = inc["source_node_id"]
                        break

                if outgoing:
                    successor_id = _resolve_target(outgoing[0]["target_node_id"], end_node_ids)
                else:
                    successor_id = END

                if predecessor_id:
                    builder.add_conditional_edges(
                        node["id"],
                        lambda state: state.get("approval_decision", "approved"),
                        {"approved": successor_id, "rejected": predecessor_id},
                    )
                else:
                    builder.add_edge(node["id"], successor_id)
                continue

            if not outgoing:
                builder.add_edge(node["id"], END)
            elif len(outgoing) == 1 and not outgoing[0].get("condition"):
                target = _resolve_target(outgoing[0]["target_node_id"], end_node_ids)
                builder.add_edge(node["id"], target)
            else:
                path_map = {
                    e["target_node_id"]: _resolve_target(e["target_node_id"], end_node_ids)
                    for e in outgoing
                }
                builder.add_conditional_edges(
                    node["id"],
                    self._make_router(outgoing, end_node_ids),
                    path_map,
                )

        checkpointer = _get_checkpointer()
        return builder.compile(checkpointer=checkpointer)

    def _make_router(self, outgoing_edges: list[dict], end_node_ids: set):
        def router(state: AgentFlowState) -> str:
            output = state.get("output", "")
            for edge in outgoing_edges:
                condition = edge.get("condition")
                if not condition:
                    continue
                try:
                    parsed = json.loads(output)
                    if isinstance(parsed, dict):
                        for val in parsed.values():
                            if condition.lower() in str(val).lower():
                                return edge["target_node_id"]
                except (json.JSONDecodeError, Exception):
                    pass
                if condition.lower() in output.lower():
                    return edge["target_node_id"]
            return outgoing_edges[0]["target_node_id"]
        return router


graph_compiler = GraphCompiler()
