# AgentFlow — AI Agent Orchestration Platform

> Build, connect, and monitor AI agents through a visual canvas. Trigger workflows from a browser, Telegram, or REST API. Watch every LLM call, tool execution, and routing decision stream live.

---

## Demo

### End-to-end workflow + Telegram live conversation

![AgentFlow Demo](demo.gif)

> *Full walkthrough: agent creation → visual workflow builder → live multi-agent execution (Research + Summarizer Pipeline) → real-time log streaming → Telegram conversation with the bot.*
>
> 📹 [Watch full demo with voiceover (MP4)](docs/voiceover/agentflow-demo-final.mp4)

**What the recording shows:**

| Segment | What you see |
|---|---|
| Agent creation | Name, model, tools, memory, guardrails configured in the UI |
| Workflow builder | React Flow canvas — nodes wired, conditional edges labeled |
| Live execution | Log stream: LLM calls, tool calls, inter-agent handoff, token cost |
| Conditional routing | Customer Support Triage — billing input routes to Billing Specialist |
| Telegram | Live message to bot → execution runs → bot replies in chat |

📖 **New to AgentFlow?** Start with the [User Handbook](HANDBOOK.md) — a step-by-step guide covering every feature from first run to Telegram integration.

---

## Table of Contents

- [Demo](#demo)
- [Overview](#overview)
- [Architecture](#architecture)
  - [System Diagram](#system-diagram)
  - [Execution Flow](#execution-flow)
  - [Data Flow: Real-time Streaming](#data-flow-real-time-streaming)
- [Why LangGraph?](#why-langgraph)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [First-time Setup](#first-time-setup)
  - [With Telegram Bot](#with-telegram-bot)
  - [Demo Mode](#demo-mode)
- [Configuration Reference](#configuration-reference)
- [Features](#features)
  - [Visual Workflow Builder](#visual-workflow-builder)
  - [Agent Management](#agent-management)
  - [Real-time Execution Monitor](#real-time-execution-monitor)
  - [Messaging Channels](#messaging-channels)
  - [Pre-built Templates](#pre-built-templates)
- [Demo Walkthrough](#demo-walkthrough)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Extending the Platform](#extending-the-platform)
  - [Add a Workflow Template](#add-a-workflow-template)
  - [Add a Messaging Channel](#add-a-messaging-channel)
  - [Add an Agent Tool](#add-an-agent-tool)
- [Tradeoffs & Production Notes](#tradeoffs--production-notes)

---

## Overview

AgentFlow is a full-stack AI agent orchestration platform built for a production engineering challenge. It covers the complete lifecycle:

| Capability | What it does |
|---|---|
| **Visual Builder** | Drag-and-drop canvas to wire agents together with conditional routing |
| **LangGraph Runtime** | Compiles the visual graph into a real, executable StateGraph with checkpointing |
| **Async Task Queue** | Celery workers run LLM chains without blocking the API; Beat handles scheduled triggers |
| **Live Log Streaming** | Every token, tool call, and routing decision streams to the browser via WebSocket |
| **Messaging Channels** | Telegram (built-in); Slack extension point documented; webhook trigger built-in |
| **Memory** | Per-agent ChromaDB vector store persists context across executions |
| **Guardrails** | Input/output keyword blocking and length limits on every agent node |

---

## Architecture

### System Diagram

![AgentFlow Architecture](docs/architecture.png)

| Layer | Components |
|---|---|
| **Browser** | Workflow Builder (React Flow), Execution Logs (WebSocket), Agent Manager |
| **FastAPI** | REST API v1, WebSocket monitor → Redis SUBSCRIBE, API-Key middleware |
| **Celery** | `run_workflow_task`, `run_agent_direct_task`, Beat scheduler (scheduled triggers + HITL timeouts) |
| **LangGraph** | `graph_compiler.py` → StateGraph, per-node guardrails → LLM → tools → Redis PUBLISH |
| **Data stores** | Redis (pub/sub, broker, rate limit), SQLite (app data + checkpoints), ChromaDB (vectors) |
| **Telegram** | Isolated docker-compose service; message → Celery task → bot.reply() |

### Execution Flow

![Execution Flow](docs/execution-flow.png)

### Data Flow: Real-time Streaming

![Data Flow](docs/data-flow.png)

---

## Why LangGraph?

LangGraph was chosen over CrewAI, AutoGen, and a hand-rolled async executor.

### Decision matrix

| Criterion | **LangGraph** ✅ | CrewAI | AutoGen | Custom |
|---|---|---|---|---|
| **Graph topology** | Arbitrary DAG + cycles + fan-out + conditionals | Fixed crew→task | Conversation chains | Unlimited |
| **Visual mapping** | 1:1 with React Flow nodes/edges | Hard to serialize | N/A | Complex |
| **Checkpointing** | Built-in `SqliteSaver` / `PostgresSaver` | External only | External only | Build it yourself |
| **Streaming** | Native `astream()` (events via Redis pub/sub) | Limited | Limited | Build it yourself |
| **State management** | Typed `TypedDict`, persisted per `thread_id` | Per-crew memory | Per-conversation | Build it yourself |
| **HITL (approval)** | Native `interrupt()` + `Command(resume=…)` | Not supported | Not supported | Build it yourself |
| **Conditional routing** | `add_conditional_edges()` with routing function | Manual | N/A | Build it yourself |
| **Maturity** | LangChain-backed, production usage | Growing | Microsoft-backed | N/A |

### The core insight

The visual canvas (React Flow) and the execution runtime (LangGraph) share the same mental model: **nodes and edges**. A node in the UI becomes a LangGraph node. A conditional edge in the UI becomes `add_conditional_edges()`. This zero-impedance mapping means:

- `graph_compiler.py` converts a DB `Workflow` → `CompiledStateGraph` in ~270 lines (nodes, edges, approval gates, conditional routing)
- Every visual change a user makes immediately reflects in runtime behaviour
- No translation layer, no "export to YAML then re-parse" step

---

## Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Agent Runtime** | LangGraph 0.2 + LangChain 0.3 | Graph execution, streaming, HITL, checkpoints |
| **LLM Providers** | OpenAI GPT-4o · Anthropic Claude | Per-agent model selection |
| **Backend API** | FastAPI + Uvicorn | WebSocket-native, async, auto-OpenAPI |
| **Task Queue** | Celery 5 + Redis | Async execution, retries, Beat scheduling |
| **Database** | SQLite → PostgreSQL (SQLAlchemy 2.0 async) | Zero-config locally; one env var to upgrade |
| **Vector Memory** | ChromaDB (embedded) | No extra service for local dev |
| **Real-time** | WebSockets + Redis pub/sub | Decoupled streaming between worker and browser |
| **Telegram** | python-telegram-bot 21 (asyncio) | Fully async; polling for dev, webhook-ready |
| **Frontend** | React 18 + TypeScript + Vite | Type-safe, fast HMR |
| **Workflow UI** | React Flow 11 | Purpose-built node-edge canvas |
| **UI Components** | shadcn/ui + Tailwind CSS | Accessible, composable, zero-config dark mode |
| **State (client)** | TanStack Query + Zustand | Server state + WebSocket store |
| **Containers** | Docker + Compose v2 | Single-command startup, profile-based optional services |

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Docker | 24+ | |
| Docker Compose | v2 (`docker compose`) | Not v1 `docker-compose` |
| OpenAI API key | — | Required for LLM calls |
| Anthropic API key | — | Optional; enables Claude models |
| Telegram Bot Token | — | Optional; enables bot integration |

### First-time Setup

```bash
# 1. Clone
git clone <repo-url>
cd agent-orchestration-platform

# 2. Configure
cp .env.example .env
# Open .env and set OPENAI_API_KEY (required)
# Optionally set ANTHROPIC_API_KEY, TELEGRAM_BOT_TOKEN

# 3. Build and start (first run takes ~2 min to pull images)
make setup   # builds images
make dev     # starts all services
```

Services started by `make dev`:

| Service | Port | Description |
|---|---|---|
| `frontend` | 3002 | React UI |
| `backend` | 8000 | FastAPI + WebSocket server |
| `worker` | — | Celery worker (4 concurrent slots) |
| `beat` | — | Celery Beat (scheduled tasks) |
| `redis` | 6380 | Broker + pub/sub |

**Open the UI:** http://localhost:3002  
**API Docs (Swagger):** http://localhost:8000/docs  
**Health check:** http://localhost:8000/api/v1/health

```bash
# Useful commands
make logs    # tail all service logs
make stop    # stop all containers
make clean   # stop + remove volumes + delete ./backend/data
```

### With Telegram Bot

```bash
# Add to .env:
TELEGRAM_BOT_TOKEN=<your-token-from-BotFather>

make telegram
# Equivalent: docker compose --profile telegram up
```

Then message your bot `/start` to retrieve your chat ID. Configure a workflow with **Trigger type = telegram** in the workflow settings.

### Demo Mode

Seeds two pre-built workflows then opens the UI:

```bash
make demo
```

Creates:
- **Research + Summarizer Pipeline** — web search → summarise
- **Customer Support Triage** — classify → route to specialist

---

## Configuration Reference

All settings live in `.env`. Pydantic-settings validates them at startup.

```bash
# ── LLM Providers ──────────────────────────────────────────────────
OPENAI_API_KEY=sk-...             # Required for GPT-4o / GPT-4o-mini
ANTHROPIC_API_KEY=sk-ant-...      # Optional — enables Claude models

# ── Messaging Channels ─────────────────────────────────────────────
TELEGRAM_BOT_TOKEN=               # From @BotFather; leave empty to skip

# ── Storage ────────────────────────────────────────────────────────
# SQLite (default, zero-config)
DATABASE_URL=sqlite+aiosqlite:///./data/agentflow.db

# PostgreSQL (production) — change this one line, nothing else
# DATABASE_URL=postgresql+asyncpg://user:pass@host/agentflow

CHECKPOINTER_DB_PATH=./data/checkpointer.db   # LangGraph checkpoint store
CHROMA_PERSIST_DIR=./data/chroma               # ChromaDB vectors

# ── Redis ──────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# ── Security ───────────────────────────────────────────────────────
API_KEY=                          # Set to require X-API-Key header; empty = open

# ── Behaviour ──────────────────────────────────────────────────────
APPROVAL_TIMEOUT_MINUTES=60       # Auto-fail HITL nodes after this duration
TRIGGER_RATE_LIMIT=30             # Max triggers per minute per workflow
DEBUG=false
```

**Messaging channel tokens** (Telegram, Slack, etc.) are stored in the `platform_settings` database table and can be configured at runtime through **Settings → Messaging Channels** in the UI — no restart required.

---

## Features

### Visual Workflow Builder

- **Drag-and-drop canvas** — drag agents from the sidebar onto the React Flow canvas
- **Connect agents** — draw edges; LangGraph nodes and edges are compiled 1:1
- **Conditional routing** — add a condition string on any edge; a router agent (JSON output mode) determines the branch at runtime
- **Human-in-the-loop nodes** — add an Approval node; execution pauses until approved or rejected via the UI (backed by LangGraph `interrupt()`)
- **Run inline** — trigger and navigate to live logs without leaving the builder

### Agent Management

| Setting | Options |
|---|---|
| **Model** | `gpt-4o`, `gpt-4o-mini`, `claude-3-5-sonnet`, `claude-3-haiku`, and any model name |
| **Provider** | `openai`, `anthropic` |
| **Temperature** | 0.0 – 2.0 |
| **Max iterations** | Tool call loop limit |
| **Output format** | `text` (default) or `json` (forces structured output — ideal for router agents) |
| **Memory** | Per-agent ChromaDB collection, persisted across runs |
| **Tools** | `web_search`, `web_scraper`, `calculator`, `get_current_datetime`, `send_telegram_message`, `http_request`, `json_parser`, `text_summarizer`, custom HTTP webhooks |
| **Input guardrails** | Block inputs containing specific keywords; enforce max length |
| **Output guardrails** | Block responses containing specific keywords; enforce max length |
| **Test** | Run any prompt against the agent inline without a full workflow |

### Real-time Execution Monitor

Every execution streams log events live via WebSocket:

| Event type | Colour | Example |
|---|---|---|
| `llm_start` | Blue | `[Research Agent] starting (gpt-4o-mini)` |
| `tool_call` | Yellow | `[Research Agent] Calling tool: web_search` |
| `llm_end` | Green | `[Research Agent] completed — 512 in / 280 out tokens ($0.0003)` |
| `approval` | Amber | `⏸ [Human Review] Waiting for human approval` |
| `info` | Grey | `Router: condition 'billing' exact-matched JSON 'category'` |
| `error` | Red | `[Agent] Output blocked by guardrail: keyword found` |

Execution history is persisted; past logs are paginated from the database.

### Messaging Channels

Configure tokens at runtime via **Settings → Messaging Channels**:

| Channel | Status | Trigger type |
|---|---|---|
| **Telegram** | Built-in | `telegram` |
| **Slack** | Extension point documented | `slack` |
| **Webhook** | Built-in (any HTTP caller) | `webhook` |

### Pre-built Templates

**1. Research + Summarizer Pipeline** *(beginner)*
```
[Start] ──► [Researcher] ──► [Summarizer] ──► [End]
                 │
           tools: web_search, web_scraper
```
Researcher gathers information from the web; Summarizer produces a concise executive summary.

**2. Customer Support Triage** *(intermediate)*
```
                         ┌──billing──► [Billing Specialist] ──► [End]
[Start] ──► [Triage] ────┤
                         ├──technical► [Tech Support]       ──► [End]
                         └──general──► [General Support]    ──► [End]
```
Triage outputs `{"category": "billing"|"technical"|"general"}`. `graph_compiler.py` wires `add_conditional_edges()` from the edge condition strings automatically.

**3. Content Marketing Pipeline** *(beginner)*
```
[Start] ──► [Topic Researcher] ──► [Content Writer] ──► [Senior Editor] ──► [End]
```
Researcher gathers source material; Writer drafts; Editor polishes for publication.

**4. Data Intelligence Report** *(intermediate)*
```
[Start] ──► [Data Collector] ──► [Data Analyst] ──► [Report Generator] ──► [End]
```
Gathers raw data from the web, identifies trends, produces an executive-ready intelligence brief.

**5. Content with Human Approval** *(advanced — HITL)*
```
[Start] ──► [Brief Researcher] ──► [Content Drafter] ──► [Human Review ⏸] ──► [Publisher] ──► [End]
                                                                │
                                                      rejected ─┘ (loops back to Drafter with feedback)
```
Execution pauses at the Approval node. Reviewer approves (continues to Publisher) or rejects with feedback (Drafter revises and re-submits).

---

## Demo Walkthrough

```bash
make demo
# Opens http://localhost:3002
```

**Step 1 — Research a topic**

1. Go to **Workflows** → open "Research + Summarizer Pipeline"
2. Click **Run Workflow** → enter:
   ```
   What are the top 5 AI breakthroughs of 2024?
   ```
3. Watch the Executions tab: Research Agent calls `web_search`, `web_scraper`, then passes findings to Summarizer Agent

**Step 2 — Conditional routing**

1. Go to **Workflows** → open "Customer Support Triage"
2. Click **Run Workflow** → enter:
   ```
   My invoice shows an incorrect charge from last month
   ```
3. Watch Triage Agent output `{"category": "billing"}` → graph routes to Billing Specialist

**Step 3 — Telegram** *(if token configured)*

Message your bot:
```
What are the top 5 AI breakthroughs of 2024?
```
The same workflow runs and replies in ~30–60 s.

**Step 4 — Build your own**

1. **Agents** → Create new agent (give it a system prompt and tools)
2. **Workflows** → Create new → drag your agent onto the canvas → connect Start → Agent → End
3. **Run Workflow** — live logs appear immediately

---

## Project Structure

```
agent-orchestration-platform/
├── Makefile                          # setup / dev / demo / telegram / stop / clean / logs
├── docker-compose.yml                # 6 services (redis, backend, worker, beat, telegram_bot, frontend)
├── .env.example                      # All config vars with documentation
│
├── backend/
│   └── app/
│       ├── main.py                   # FastAPI app, lifespan (init_db), CORS, auth middleware
│       ├── config.py                 # Pydantic BaseSettings — reads from .env
│       ├── database.py               # SQLAlchemy async engine + session factory
│       ├── dependencies.py           # FastAPI Depends helpers
│       │
│       ├── models/                   # SQLAlchemy ORM models
│       │   ├── agent.py              # Agent (tools, guardrails, memory, telegram config)
│       │   ├── workflow.py           # Workflow + WorkflowNode + WorkflowEdge
│       │   ├── execution.py          # Execution + ExecutionLog
│       │   ├── message.py            # Chat message history
│       │   ├── memory.py             # ChromaDB collection metadata
│       │   ├── custom_tool.py        # User-defined HTTP webhook tools
│       │   ├── workflow_template.py  # Template registry
│       │   └── platform_setting.py   # Key-value store for channel tokens
│       │
│       ├── schemas/                  # Pydantic request/response models
│       │
│       ├── api/
│       │   ├── v1/
│       │   │   ├── agents.py         # CRUD + test + memory endpoints
│       │   │   ├── workflows.py      # CRUD + graph save + trigger + scheduling
│       │   │   ├── executions.py     # List + logs + approve/reject HITL
│       │   │   ├── templates.py      # Gallery + instantiate
│       │   │   ├── custom_tools.py   # User webhook tool CRUD
│       │   │   ├── settings.py       # Platform settings (channel tokens) GET/PUT/DELETE
│       │   │   └── health.py         # Health check + tool list
│       │   └── ws/
│       │       └── monitor.py        # WebSocket endpoint → Redis SUBSCRIBE → stream logs
│       │
│       ├── core/
│       │   ├── state.py              # AgentFlowState TypedDict (shared graph state)
│       │   ├── agent_builder.py      # DB Agent → async LangGraph callable (tools + memory wired)
│       │   ├── graph_compiler.py     # DB Workflow → CompiledStateGraph (nodes + edges + conditions)
│       │   ├── log_emitter.py        # Redis PUBLISH helper used by every agent node
│       │   ├── memory_manager.py     # ChromaDB retrieval + storage per agent collection
│       │   └── cost_calculator.py    # Token usage → USD cost estimate
│       │
│       ├── tools/                    # LangChain @tool functions
│       │   ├── web_search.py         # DuckDuckGo search
│       │   ├── web_scraper.py        # URL → clean text (httpx + BeautifulSoup)
│       │   ├── calculator.py         # Safe math expression evaluator
│       │   ├── datetime_tool.py      # Current date/time in any timezone
│       │   ├── http_request.py       # Generic HTTP webhook tool
│       │   ├── send_telegram.py      # Send message to Telegram chat mid-execution
│       │   └── text_tools.py         # Summarise, extract, transform
│       │
│       ├── workers/
│       │   ├── celery_app.py         # Celery app + config
│       │   ├── execution_tasks.py    # run_workflow_task / run_agent_direct_task / resume_workflow_task
│       │   └── scheduled_tasks.py    # check_scheduled_workflows / check_approval_timeouts (Beat)
│       │
│       ├── integrations/
│       │   └── telegram/
│       │       ├── bot.py            # ApplicationBuilder + polling loop (standalone process)
│       │       ├── handlers.py       # /start /help /agents + plain message → Celery task
│       │       └── router.py         # chat_id ↔ workflow_id mapping
│       │
│       └── templates/
│           ├── research_pipeline.py  # Research + Summarizer template factory
│           ├── customer_support.py   # Triage + three specialist agents template
│           └── …                     # Add new templates here
│
└── frontend/
    └── src/
        ├── api/
        │   ├── client.ts             # Axios instance (base URL, auth header)
        │   ├── agents.ts             # Agent CRUD + test + memory hooks
        │   ├── workflows.ts          # Workflow CRUD + trigger
        │   ├── executions.ts         # Execution list + logs
        │   ├── templates.ts          # Template gallery + instantiate
        │   ├── custom_tools.ts       # Webhook tool CRUD
        │   ├── settings.ts           # Platform settings (channel tokens)
        │   └── types.ts              # Shared TypeScript types
        │
        ├── stores/
        │   └── executionStore.ts     # Zustand: WebSocket connection + live log buffer
        │
        ├── components/
        │   ├── layout/
        │   │   ├── Layout.tsx        # h-screen fixed sidebar + scrollable main
        │   │   └── Sidebar.tsx       # Nav items + Settings link
        │   ├── workflows/
        │   │   ├── WorkflowBuilder.tsx # React Flow canvas + node toolbar
        │   │   └── AgentNode.tsx     # Custom node component (agent card)
        │   ├── executions/
        │   │   └── LogStream.tsx     # Live WebSocket log terminal
        │   └── ui/                   # shadcn/ui primitives
        │
        └── pages/
            ├── DashboardPage.tsx     # Stats + recent executions
            ├── AgentsPage.tsx        # Agent list + create/edit dialog
            ├── WorkflowsPage.tsx     # Workflow list + settings drawer
            ├── ExecutionsPage.tsx    # Execution history + log viewer
            ├── TemplatesPage.tsx     # Template gallery
            ├── ToolsPage.tsx         # Custom HTTP webhook tools
            └── SettingsPage.tsx      # System status + messaging channel config
```

---

## API Reference

**Base URL:** `http://localhost:8000/api/v1`  
**Auth:** Set `X-API-Key: <your-key>` header when `API_KEY` is configured in `.env`  
**Interactive docs:** http://localhost:8000/docs

### Agents

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/agents` | List all agents |
| `POST` | `/agents` | Create agent |
| `GET` | `/agents/{id}` | Get agent |
| `PATCH` | `/agents/{id}` | Update agent |
| `DELETE` | `/agents/{id}` | Delete agent |
| `POST` | `/agents/{id}/test` | Test agent with `{"prompt": "..."}` |
| `GET` | `/agents/{id}/memory` | View stored memory |
| `DELETE` | `/agents/{id}/memory` | Clear agent memory |

### Workflows

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/workflows` | List all workflows |
| `POST` | `/workflows` | Create workflow |
| `GET` | `/workflows/{id}` | Get workflow with nodes + edges |
| `PATCH` | `/workflows/{id}` | Update metadata |
| `DELETE` | `/workflows/{id}` | Delete workflow |
| `POST` | `/workflows/{id}/graph` | Save visual graph `{nodes, edges}` |
| `POST` | `/workflows/{id}/trigger` | Start execution `{"prompt": "..."}` |

### Executions

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/executions` | List executions (filterable by workflow) |
| `GET` | `/executions/{id}` | Get execution detail |
| `GET` | `/executions/{id}/logs` | Paginated log entries |
| `POST` | `/executions/{id}/approve` | Approve or reject HITL node `{"decision": "approve"\|"reject", "comment": "..."}` |
| `WS` | `/ws/executions/{id}/logs` | Real-time log stream |

### Templates & Tools

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/templates` | List available templates |
| `POST` | `/templates/{slug}/instantiate` | Create workflow from template |
| `GET` | `/tools` | List all available tools (built-in + custom) |
| `GET/POST` | `/custom-tools` | List / create webhook tool |
| `PATCH/DELETE` | `/custom-tools/{id}` | Update / delete webhook tool |

### Settings

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/settings` | All saved settings (secrets masked) |
| `PUT` | `/settings/{key}` | Save or update a setting `{"value": "..."}` |
| `DELETE` | `/settings/{key}` | Clear a setting |

---

## Extending the Platform

### Add a Workflow Template

1. Create `backend/app/templates/my_template.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.agent import Agent
from app.models.workflow import Workflow, WorkflowNode, WorkflowEdge

async def create_my_template(db: AsyncSession) -> dict:
    # 1. Create agents
    agent = Agent(name="My Agent", system_prompt="You are …", model="gpt-4o-mini", ...)
    db.add(agent)
    await db.flush()

    # 2. Create workflow
    workflow = Workflow(name="My Workflow", ...)
    db.add(workflow)
    await db.flush()

    # 3. Add nodes and edges
    db.add(WorkflowNode(workflow_id=workflow.id, agent_id=agent.id, node_type="agent", ...))
    db.add(WorkflowEdge(workflow_id=workflow.id, source_id="start", target_id=agent.id))
    await db.commit()
    return {"workflow_id": workflow.id, "message": "Created"}
```

2. Register in `backend/app/api/v1/templates.py`:

```python
TEMPLATES["my-template"] = {
    "slug": "my-template", "name": "My Workflow",
    "description": "What it does.", "icon": "zap",
    "category": "productivity", "agent_count": 1,
}

# In instantiate_template():
elif slug == "my-template":
    from app.templates.my_template import create_my_template
    result = await create_my_template(db)
```

The template appears in the gallery automatically — no other changes needed.

### Add a Messaging Channel

Pattern demonstrated by Telegram. All channel tokens are stored in `platform_settings` and configurable via Settings UI.

**Step 1 — Add the UI card** (frontend only)

In `frontend/src/pages/SettingsPage.tsx`, append to the `CHANNELS` array:

```typescript
{
  id: 'slack',
  label: 'Slack',
  icon: Hash,
  color: 'green',
  description: 'Post agent outputs to Slack channels.',
  fields: [
    { key: 'slack_bot_token',      label: 'Bot Token',      placeholder: 'xoxb-…', secret: true },
    { key: 'slack_signing_secret', label: 'Signing Secret', placeholder: 'a1b2…',  secret: true },
  ],
  instructions: [
    'Go to api.slack.com/apps → create a new app.',
    'OAuth & Permissions → add bot scope chat:write → install to workspace.',
    'Copy Bot Token + Signing Secret → paste above → Save.',
    'Add the Slack integration handler to the backend.',
    'Set trigger type = slack on any workflow.',
  ],
}
```

The token card and instructions appear in the UI immediately.

**Step 2 — Backend integration**

```
backend/app/integrations/slack/
├── bot.py        # socket mode / polling loop (separate docker-compose service)
├── handlers.py   # receive message → create Execution → celery.delay(run_workflow_task)
└── router.py     # slack_channel_id ↔ workflow_id
```

Read the token from the database at startup:

```python
from sqlalchemy import select
from app.models.platform_setting import PlatformSetting

result = await db.execute(select(PlatformSetting).where(PlatformSetting.key == "slack_bot_token"))
token = result.scalar_one_or_none()
```

**Step 3 — Add a send tool** (optional — lets agents push mid-flow messages)

```python
# backend/app/tools/send_slack.py
@tool
def send_slack_message(channel: str, message: str) -> str:
    """Send a message to a Slack channel."""
    ...
```

Register in `backend/app/core/tool_registry.py`.

**Step 4 — Docker Compose service**

```yaml
slack_bot:
  build: ./backend
  command: python -m app.integrations.slack.bot
  environment: *backend-env
  volumes: *backend-volumes
  depends_on:
    backend:
      condition: service_healthy
  profiles: ["slack"]
```

Start with: `docker compose --profile slack up`

### Add an Agent Tool

1. Create `backend/app/tools/my_tool.py`:

```python
from langchain.tools import tool

@tool
def my_tool(query: str) -> str:
    """One-line description shown to the LLM when deciding to use this tool."""
    # implementation
    return result
```

2. Register in `backend/app/core/tool_registry.py`:

```python
from app.tools.my_tool import my_tool

TOOL_REGISTRY = {
    …
    "my_tool": my_tool,
}
```

The tool is immediately available in the Agent editor tool selector.

---

## Engineering Decisions

Each decision below was made deliberately for this context. The upgrade path for each is isolated and documented — the architecture is designed so that no single swap ripples across the codebase.

### Database: SQLite with a one-line PostgreSQL upgrade

**Decision:** SQLite for local development via `sqlite+aiosqlite`.  
**Why:** Zero-config startup — no database service to provision, no credentials to manage, no migration to run before `make dev` works. This removes an entire class of "works on my machine" friction.  
**Production upgrade:** One environment variable:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/agentflow
```

SQLAlchemy 2.0 async abstracts the driver completely. The LangGraph checkpointer has a drop-in `AsyncPostgresSaver` that activates in the same `_get_checkpointer()` function in `graph_compiler.py`. No application code changes.

### Task Queue: Celery over FastAPI BackgroundTasks

**Decision:** Celery 5 + Redis as the execution backbone, not FastAPI `BackgroundTasks`.  
**Why:** LLM workflow executions are long-running (10–120 s), stateful, and must survive API server restarts. Celery gives this for free:

- **Retries** with exponential backoff — transient LLM API failures recover automatically
- **Persistence** — in-flight tasks survive a worker restart via Redis
- **Scheduling** — Celery Beat runs `check_scheduled_workflows` and `check_approval_timeouts` without an external cron service
- **Observability** — every task has a result backend entry; `make logs` shows exactly what each worker is processing
- **Horizontal scale** — add workers with `docker compose scale worker=4`, no code change

`BackgroundTasks` provides none of these. The ~10 ms event-loop bridge cost (`asyncio.new_event_loop()`) is the only tradeoff — negligible against LLM latencies of seconds.

### Vector Memory: ChromaDB with a single-file swap path

**Decision:** ChromaDB running embedded (in-process, no extra service).  
**Why:** Eliminates a service dependency during development and evaluation. ChromaDB persists to disk (`./data/chroma`) so memory survives container restarts without any infrastructure.  
**Production upgrade:** `memory_manager.py` is the single file that touches the vector store. Replacing the ChromaDB client with Qdrant, Pinecone, or Weaviate is fully contained there — nothing else in the codebase references the vector store directly.

### Telegram: Isolated process, not embedded in the API

**Decision:** Telegram bot runs as a separate docker-compose service (`python -m app.integrations.telegram.bot`), not as a background thread inside Uvicorn.  
**Why:** `python-telegram-bot` manages its own asyncio event loop and signal handlers. Running it inside a Uvicorn process causes signal conflicts that silently drop messages under load. The separate process model means:

- The bot can restart independently without taking down the API
- Both processes share state through the database and Celery tasks — no direct coupling
- Adding another channel (Slack, WhatsApp) follows the same pattern: one new service, no API changes

### Rate Limiting: Redis sliding window, configurable per deployment

**Decision:** Enforce `TRIGGER_RATE_LIMIT` (default: 30 triggers/minute/workflow) via a Redis counter.  
**Why:** Prevents runaway automations from exhausting LLM API quotas. Redis makes the counter shared across all worker instances, so the limit holds even under horizontal scaling. Set to `0` to disable for trusted internal deployments.

### Authentication: Opt-in API key, designed for layered security

**Decision:** `API_KEY` is empty by default; authentication is a single env var away.  
**Why:** A challenge evaluation environment should not require secret management setup to run `make dev`. When set, every request passes through the auth middleware before reaching any router. The next layer — per-user JWT / OAuth2 — is a standard FastAPI `Depends()` pattern that can be added without touching any existing route logic.
