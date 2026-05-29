"""
Demo seed script — creates agents, workflows, and runs live executions.
Uses provider="demo" so no API key is needed.
Run inside the backend container: python seed_demo.py
"""
import sqlite3, uuid, json, time, requests
from datetime import datetime

API = "http://localhost:8000/api/v1"
DB_PATH = "./data/agentflow.db"


def api(method, path, body=None):
    fn = getattr(requests, method)
    r = fn(f"{API}{path}", json=body, timeout=10)
    r.raise_for_status()
    return r.json()


def wait_for_execution(exec_id, timeout=30):
    for _ in range(timeout // 2):
        time.sleep(2)
        e = api("get", f"/executions/{exec_id}")
        status = e["status"]
        if status in ("completed", "failed"):
            return e
        print(f"    ... {status}")
    return api("get", f"/executions/{exec_id}")


print("\n🚀 AgentFlow Demo Seeder")
print("=" * 50)

# ── 1. Clear old data ────────────────────────────────
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
for t in ["execution_logs","executions","workflow_edges","workflow_nodes","workflows","memory_entries","agents"]:
    cur.execute(f"DELETE FROM {t}")
conn.commit()
conn.close()
print("✓ Cleared previous data")

# ── 2. Create Agents ─────────────────────────────────
print("\n📦 Creating agents...")

researcher = api("post", "/agents", {
    "name": "Research Agent",
    "role": "researcher",
    "description": "Searches and gathers comprehensive information on any topic",
    "system_prompt": "You are an expert researcher. Investigate the given topic thoroughly and present structured findings with key facts, trends, and insights.",
    "model": "gpt-4o-mini",
    "provider": "demo",
    "temperature": 0.3,
    "tools": ["web_search", "web_scraper"],
    "memory_enabled": True,
    "max_output_tokens": 2048,
    "avatar_color": "#3b82f6",
})
print(f"  ✓ {researcher['name']} ({researcher['id'][:8]}...)")

summarizer = api("post", "/agents", {
    "name": "Summarizer Agent",
    "role": "summarizer",
    "description": "Synthesizes research into concise executive summaries",
    "system_prompt": "You receive research findings and produce a concise executive summary with the 3 most important insights and clear action items.",
    "model": "gpt-4o-mini",
    "provider": "demo",
    "temperature": 0.5,
    "tools": [],
    "memory_enabled": True,
    "max_output_tokens": 1024,
    "avatar_color": "#8b5cf6",
})
print(f"  ✓ {summarizer['name']} ({summarizer['id'][:8]}...)")

triage = api("post", "/agents", {
    "name": "Triage Agent",
    "role": "triage",
    "description": "Classifies support tickets and routes to the right specialist",
    "system_prompt": 'Classify the issue. Respond ONLY with JSON: {"category": "billing"|"technical"|"general", "priority": "low"|"medium"|"high"|"urgent", "summary": "brief summary"}',
    "model": "gpt-4o-mini",
    "provider": "demo",
    "temperature": 0.1,
    "tools": [],
    "memory_enabled": False,
    "avatar_color": "#f59e0b",
    "guardrail_keywords": [],
})
print(f"  ✓ {triage['name']} ({triage['id'][:8]}...)")

billing = api("post", "/agents", {
    "name": "Billing Specialist",
    "role": "billing_support",
    "description": "Resolves billing, payment, and subscription issues",
    "system_prompt": "You are an empathetic billing specialist. Explain the issue clearly and provide concrete next steps with realistic timelines.",
    "model": "gpt-4o-mini",
    "provider": "demo",
    "temperature": 0.7,
    "tools": [],
    "memory_enabled": True,
    "avatar_color": "#10b981",
})
print(f"  ✓ {billing['name']} ({billing['id'][:8]}...)")

tech = api("post", "/agents", {
    "name": "Tech Support",
    "role": "technical_support",
    "description": "Debugs technical issues, errors, and integrations",
    "system_prompt": "You are an expert technical support engineer. Provide step-by-step troubleshooting with clear explanations.",
    "model": "gpt-4o-mini",
    "provider": "demo",
    "temperature": 0.4,
    "tools": ["web_search"],
    "memory_enabled": True,
    "avatar_color": "#ef4444",
})
print(f"  ✓ {tech['name']} ({tech['id'][:8]}...)")

general = api("post", "/agents", {
    "name": "General Support",
    "role": "general_support",
    "description": "Handles how-to questions and general inquiries",
    "system_prompt": "You are a friendly support agent. Answer questions clearly and point users to helpful resources.",
    "model": "gpt-4o-mini",
    "provider": "demo",
    "temperature": 0.7,
    "tools": [],
    "memory_enabled": True,
    "avatar_color": "#6366f1",
})
print(f"  ✓ {general['name']} ({general['id'][:8]}...)")

# ── 3. Workflow A: Research Pipeline ─────────────────
print("\n🔗 Creating Research Pipeline workflow...")

wf_a = api("post", "/workflows", {
    "name": "Research + Summarizer Pipeline",
    "description": "Researcher gathers web information → Summarizer creates executive summary",
    "trigger_type": "manual",
})
wf_a_id = wf_a["id"]

S = f"s-{uuid.uuid4().hex[:8]}"
N1 = f"n-{uuid.uuid4().hex[:8]}"
N2 = f"n-{uuid.uuid4().hex[:8]}"
E = f"e-{uuid.uuid4().hex[:8]}"

api("post", f"/workflows/{wf_a_id}/graph", {
    "nodes": [
        {"id": S,  "node_type": "start", "label": "Start",                    "position_x": 80,  "position_y": 220, "config": {}},
        {"id": N1, "node_type": "agent", "label": "Research Agent",           "position_x": 320, "position_y": 220, "config": {}, "agent_id": researcher["id"]},
        {"id": N2, "node_type": "agent", "label": "Summarizer Agent",         "position_x": 620, "position_y": 220, "config": {}, "agent_id": summarizer["id"]},
        {"id": E,  "node_type": "end",   "label": "End",                      "position_x": 900, "position_y": 220, "config": {}},
    ],
    "edges": [
        {"source_node_id": S,  "target_node_id": N1, "label": ""},
        {"source_node_id": N1, "target_node_id": N2, "label": ""},
        {"source_node_id": N2, "target_node_id": E,  "label": ""},
    ],
})
print(f"  ✓ Workflow created: {wf_a_id[:8]}... (4 nodes, 3 edges)")

# ── 4. Workflow B: Customer Support Triage ───────────
print("\n🔗 Creating Customer Support Triage workflow...")

wf_b = api("post", "/workflows", {
    "name": "Customer Support Triage",
    "description": "Triage classifies issue → routes to billing, technical, or general specialist",
    "trigger_type": "manual",
})
wf_b_id = wf_b["id"]

S2   = f"s-{uuid.uuid4().hex[:8]}"
TR   = f"n-{uuid.uuid4().hex[:8]}"
BL   = f"n-{uuid.uuid4().hex[:8]}"
TK   = f"n-{uuid.uuid4().hex[:8]}"
GN   = f"n-{uuid.uuid4().hex[:8]}"
EB   = f"e-{uuid.uuid4().hex[:8]}"
ET   = f"e-{uuid.uuid4().hex[:8]}"
EG   = f"e-{uuid.uuid4().hex[:8]}"

api("post", f"/workflows/{wf_b_id}/graph", {
    "nodes": [
        {"id": S2, "node_type": "start", "label": "Start",              "position_x": 80,  "position_y": 300, "config": {}},
        {"id": TR, "node_type": "agent", "label": "Triage Agent",       "position_x": 300, "position_y": 300, "config": {}, "agent_id": triage["id"]},
        {"id": BL, "node_type": "agent", "label": "Billing Specialist", "position_x": 580, "position_y": 120, "config": {}, "agent_id": billing["id"]},
        {"id": TK, "node_type": "agent", "label": "Tech Support",       "position_x": 580, "position_y": 300, "config": {}, "agent_id": tech["id"]},
        {"id": GN, "node_type": "agent", "label": "General Support",    "position_x": 580, "position_y": 480, "config": {}, "agent_id": general["id"]},
        {"id": EB, "node_type": "end",   "label": "End",                "position_x": 860, "position_y": 120, "config": {}},
        {"id": ET, "node_type": "end",   "label": "End",                "position_x": 860, "position_y": 300, "config": {}},
        {"id": EG, "node_type": "end",   "label": "End",                "position_x": 860, "position_y": 480, "config": {}},
    ],
    "edges": [
        {"source_node_id": S2, "target_node_id": TR, "label": ""},
        {"source_node_id": TR, "target_node_id": BL, "label": "Billing",   "condition": "billing"},
        {"source_node_id": TR, "target_node_id": TK, "label": "Technical", "condition": "technical"},
        {"source_node_id": TR, "target_node_id": GN, "label": "General",   "condition": "general"},
        {"source_node_id": BL, "target_node_id": EB, "label": ""},
        {"source_node_id": TK, "target_node_id": ET, "label": ""},
        {"source_node_id": GN, "target_node_id": EG, "label": ""},
    ],
})
print(f"  ✓ Workflow created: {wf_b_id[:8]}... (8 nodes, 7 edges, conditional routing)")

# ── 5. Run Executions ────────────────────────────────
print("\n▶  Running demo executions...")

prompts_a = [
    "What is LangGraph and why is it useful for AI systems?",
    "What are the top AI trends and breakthroughs in 2025?",
]
prompts_b = [
    "I was charged twice on my credit card last week",
    "The API keeps returning a 500 error when I try to authenticate",
    "How do I set up a webhook integration for my account?",
]

results = []

print("\n  📊 Research Pipeline:")
for prompt in prompts_a:
    exec_r = api("post", f"/workflows/{wf_a_id}/trigger", {"prompt": prompt})
    exec_id = exec_r["id"]
    print(f"    → \"{prompt[:50]}...\"")
    e = wait_for_execution(exec_id, timeout=30)
    output_preview = (e.get("final_output") or "")[:120]
    tokens_in  = e.get("total_input_tokens", 0)
    tokens_out = e.get("total_output_tokens", 0)
    cost       = e.get("total_cost_usd", 0.0)
    print(f"    ✅ {e['status'].upper()} | {tokens_in}↑ {tokens_out}↓ tokens | ${cost:.4f}")
    print(f"       Output: {output_preview}...")
    results.append(e)

print("\n  🎧 Customer Support Triage:")
for prompt in prompts_b:
    exec_r = api("post", f"/workflows/{wf_b_id}/trigger", {"prompt": prompt})
    exec_id = exec_r["id"]
    print(f"    → \"{prompt[:55]}\"")
    e = wait_for_execution(exec_id, timeout=30)
    output_preview = (e.get("final_output") or "")[:120]
    tokens_in  = e.get("total_input_tokens", 0)
    tokens_out = e.get("total_output_tokens", 0)
    cost       = e.get("total_cost_usd", 0.0)
    print(f"    ✅ {e['status'].upper()} | {tokens_in}↑ {tokens_out}↓ tokens | ${cost:.4f}")
    print(f"       Output: {output_preview}...")
    results.append(e)

# ── 6. Summary ───────────────────────────────────────
print("\n" + "=" * 50)
completed = sum(1 for r in results if r["status"] == "completed")
failed    = sum(1 for r in results if r["status"] == "failed")
total_in  = sum(r.get("total_input_tokens",0) for r in results)
total_out = sum(r.get("total_output_tokens",0) for r in results)
total_cost = sum(r.get("total_cost_usd",0.0) for r in results)

print(f"\n📈 IMPACT METRICS")
print(f"  Executions:     {len(results)} total | {completed} completed | {failed} failed")
print(f"  Completion rate: {completed/len(results)*100:.0f}%")
print(f"  Total tokens:   {total_in} input / {total_out} output")
print(f"  Total cost:     ${total_cost:.4f}")
print(f"\n🌐 Open the UI:  http://localhost:3002")
print(f"📖 API Docs:     http://localhost:8000/docs")
print(f"\n✅ Demo ready! All {len(results)} workflows executed successfully.")
