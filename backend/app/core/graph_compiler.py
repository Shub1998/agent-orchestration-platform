import json
import os
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt
from app.core.state import AgentFlowState
from app.core.agent_builder import agent_builder
from app.core.log_emitter import log_emitter
from app.config import settings


def _get_checkpointer():
    try:
        import sqlite3 as _sqlite3
        from langgraph.checkpoint.sqlite import SqliteSaver
        os.makedirs(os.path.dirname(settings.CHECKPOINTER_DB_PATH) or ".", exist_ok=True)
        conn = _sqlite3.connect(settings.CHECKPOINTER_DB_PATH, check_same_thread=False)
        cp = SqliteSaver(conn)
        cp.setup()
        return cp
    except ImportError:
        pass
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()


def _resolve_target(target_id: str, end_node_ids: set) -> str:
    return END if target_id in end_node_ids else target_id


def _make_approval_node(node_id: str, label: str, config: dict):
    """
    Pause the graph and wait for a human decision using LangGraph's native
    interrupt().  The Celery worker catches GraphInterrupt, persists
    'awaiting_approval' status, and returns.  A separate resume_workflow_task
    is dispatched when the human approves/rejects via the API, calling
    graph.invoke(Command(resume=payload), config=...) to continue from here.
    """
    description = (config or {}).get("description", "")

    def approval_node(state: AgentFlowState) -> dict:
        execution_id = state.get("execution_id", "")
        current_output = state.get("output", "")

        msg = f"⏸ [{label}] Waiting for human approval"
        if description:
            msg += f": {description}"
        log_emitter.emit(
            execution_id, "approval", msg,
            metadata={"node_id": node_id, "approval_required": True,
                      "current_output": current_output[:500]},
        )

        # Suspends execution here; resumes when Command(resume=payload) is invoked.
        payload = interrupt({
            "node_id": node_id,
            "label": label,
            "current_output": current_output[:500],
        })

        # payload is whatever was passed to Command(resume=...) by resume_workflow_task
        if isinstance(payload, dict):
            decision = payload.get("decision", "approved")
            comment = payload.get("comment", "")
        else:
            decision = str(payload)
            comment = ""

        if decision == "approved":
            log_emitter.emit(execution_id, "approval", f"✅ [{label}] Approved — continuing to next agent")
            ctx = dict(state.get("context") or {})
            ctx["approval"] = "approved"
            return {"approval_decision": "approved", "rejection_comment": None, "context": ctx}
        else:
            reason = f" Reason: {comment}" if comment else ""
            log_emitter.emit(execution_id, "approval",
                             f"🔄 [{label}] Rejected — sending back to agent for revision.{reason}")
            return {"approval_decision": "rejected", "rejection_comment": comment or ""}

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
        # Separate conditional edges from the optional unconditional default
        conditional = [e for e in outgoing_edges if e.get("condition")]
        default_edge = next((e for e in outgoing_edges if not e.get("condition")), None)

        def _extract_json(text: str) -> dict | None:
            """Try to parse JSON from raw text or from a markdown code block."""
            stripped = text.strip()
            # Strip ```json ... ``` fences
            if stripped.startswith("```"):
                lines = stripped.splitlines()
                inner = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                stripped = inner.strip()
            try:
                parsed = json.loads(stripped)
                return parsed if isinstance(parsed, dict) else None
            except (json.JSONDecodeError, Exception):
                pass
            # Try extracting first {...} block from mixed text
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end > start:
                try:
                    parsed = json.loads(text[start:end + 1])
                    return parsed if isinstance(parsed, dict) else None
                except (json.JSONDecodeError, Exception):
                    pass
            return None

        def _flatten_json(obj: dict, prefix: str = "") -> dict:
            """Flatten nested JSON to dot-notation keys for deep matching."""
            result = {}
            for k, v in obj.items():
                full_key = f"{prefix}.{k}" if prefix else k
                result[full_key] = v
                if isinstance(v, dict):
                    result.update(_flatten_json(v, full_key))
            return result

        def router(state: AgentFlowState) -> str:
            output = state.get("output", "")
            execution_id = state.get("execution_id", "")

            parsed_json = _extract_json(output)
            flat = _flatten_json(parsed_json) if parsed_json else {}

            for edge in conditional:
                condition = (edge.get("condition") or "").strip().lower()
                if not condition:
                    continue

                # 1. Exact JSON value match — condition == value of any key (most reliable)
                if flat:
                    for k, v in flat.items():
                        if condition == str(v).lower():
                            log_emitter.emit(execution_id, "info",
                                             f"Router: condition '{condition}' exact-matched JSON '{k}'={v!r}")
                            return edge["target_node_id"]

                # 2. JSON key or value substring match
                if flat:
                    for k, v in flat.items():
                        if condition in k.lower() or condition in str(v).lower():
                            log_emitter.emit(execution_id, "info",
                                             f"Router: condition '{condition}' substring-matched JSON '{k}'={v!r}")
                            return edge["target_node_id"]

                # 3. Plain text substring match (case-insensitive)
                if condition in output.lower():
                    log_emitter.emit(execution_id, "info",
                                     f"Router: condition '{condition}' matched in output text")
                    return edge["target_node_id"]

            # 4. Unconditional default edge
            if default_edge:
                log_emitter.emit(execution_id, "info",
                                 f"Router: no condition matched — taking default edge")
                return default_edge["target_node_id"]

            # 5. Hard fallback: first conditional edge with a warning
            fallback = outgoing_edges[0]["target_node_id"]
            log_emitter.emit(execution_id, "info",
                             f"Router: no condition matched and no default — falling back to '{fallback}'")
            return fallback

        return router


graph_compiler = GraphCompiler()
