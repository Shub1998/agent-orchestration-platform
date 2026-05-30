# AgentFlow — User Handbook

A practical guide for anyone trying AgentFlow for the first time. Follow it top-to-bottom for a complete tour, or jump to any section.

---

## Table of Contents

1. [Before You Start](#1-before-you-start)
2. [Starting the Platform](#2-starting-the-platform)
3. [The 5-Minute Quick Win — Run a Template](#3-the-5-minute-quick-win--run-a-template)
4. [Creating Your First Agent](#4-creating-your-first-agent)
5. [Testing an Agent Inline](#5-testing-an-agent-inline)
6. [Building a Workflow from Scratch](#6-building-a-workflow-from-scratch)
7. [Running a Workflow and Watching Live Logs](#7-running-a-workflow-and-watching-live-logs)
8. [Human-in-the-Loop Approval](#8-human-in-the-loop-approval)
9. [Conditional Routing (Router Nodes)](#9-conditional-routing-router-nodes)
10. [Custom Webhook Tools](#10-custom-webhook-tools)
11. [Scheduling a Workflow](#11-scheduling-a-workflow)
12. [Telegram Integration](#12-telegram-integration)
13. [Managing Agent Memory](#13-managing-agent-memory)
14. [The Settings Page](#14-the-settings-page)
15. [Execution History and Logs](#15-execution-history-and-logs)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Before You Start

**You need:**

| Requirement | Where to get it |
|---|---|
| Docker Desktop (running) | docker.com/get-started |
| Docker Compose v2 | Bundled with Docker Desktop |
| OpenAI API key | platform.openai.com/api-keys |
| *(Optional)* Anthropic API key | console.anthropic.com |
| *(Optional)* Telegram bot token | Message `@BotFather` on Telegram |

**Check Docker is running:**
```bash
docker compose version
# Should print: Docker Compose version v2.x.x
```

---

## 2. Starting the Platform

```bash
# Clone and enter the repo
git clone <repo-url>
cd agent-orchestration-platform

# First-time setup — creates .env and builds images (~2 min)
make setup

# Open .env and fill in your API key
# OPENAI_API_KEY=sk-...
```

Then start everything:

```bash
make dev
```

Wait ~30 seconds for all services to be healthy, then open:

| URL | What it is |
|---|---|
| http://localhost:3002 | The UI (start here) |
| http://localhost:8000/docs | Swagger API explorer |
| http://localhost:8000/api/v1/health | Health check |

> **Tip:** If you want demo data pre-loaded, run `make demo` instead of `make dev`. It seeds the Research + Summarizer Pipeline and Customer Support Triage workflows automatically.

---

## 3. The 5-Minute Quick Win — Run a Template

The fastest way to see AgentFlow working end-to-end.

**Step 1 — Open Templates**

Click **Templates** in the left sidebar. You'll see five ready-made workflows:

| Template | What it does | Complexity |
|---|---|---|
| Research + Summarizer | Web search → executive summary | Beginner |
| Customer Support Triage | Classifies issue → routes to specialist | Intermediate |
| Content Marketing Pipeline | Research → Draft → Edit | Beginner |
| Data Intelligence Report | Collect → Analyse → Report | Intermediate |
| Content with Human Approval | Research → Draft → Human review → Publish | Advanced |

**Step 2 — Instantiate a template**

Click **Use Template** on "Research + Summarizer". This creates real agents and a pre-wired workflow in one click.

**Step 3 — Run it**

You'll land on the Workflows page with the new workflow selected. Click **Run Workflow**, enter a prompt:

```
What are the most important AI developments from the past 6 months?
```

Click **Run**. You'll be taken to the live execution view.

**Step 4 — Watch it work**

The **Live Logs** panel streams every event in real time:
- `[Research Agent]` calls `web_search` and `web_scraper`
- Results appear as tool call events (yellow)
- The Summarizer Agent receives the research and writes a summary
- Token count and cost appear at completion (e.g. `1,200 in / 450 out tokens ($0.0008)`)

Click **Messages** tab to see a clean view of each agent's output in conversation format.

---

## 4. Creating Your First Agent

Go to **Agents → New Agent**.

### Required fields

| Field | What to put |
|---|---|
| **Name** | A short descriptive name, e.g. `Price Monitor` |
| **System Prompt** | The agent's personality and job description (see examples below) |
| **Model** | Start with `GPT-4o Mini` — fast and cheap |

### System prompt examples

**A researcher:**
```
You are an expert research analyst. When given a topic, search the web for
the latest information, synthesise the key findings, and present them as
a structured brief with bullet points. Always include your sources.
```

**A classifier (for routing):**
```
You classify customer messages. Respond ONLY with JSON in this exact format:
{"category": "billing" | "technical" | "general", "priority": "low" | "high"}
Do not add any other text outside the JSON object.
```

**A writer:**
```
You are a professional content writer. You receive a research brief and
produce a well-structured article with a compelling headline, clear body
paragraphs, and a call-to-action. Write for a professional audience.
```

### Optional but recommended settings

**Tools** — Click the tool pills to toggle them on. Available tools:

| Tool | Use it when... |
|---|---|
| `web_search` | Agent needs to find current information |
| `web_scraper` | Agent needs to read a full webpage |
| `calculator` | Agent does any maths |
| `get_current_datetime` | Agent needs to know today's date/time |
| `http_request` | Agent calls an external API |
| `send_telegram_message` | Agent should notify you mid-execution |

**Memory** — Leave enabled. The agent will remember context from previous runs and use it to give better answers over time.

**Guardrails** (in the orange section):
- *Max output tokens* — caps how long the response can be
- *Max input length* — truncates overly long inputs before they reach the LLM
- *Blocked output keywords* — words that, if found in the response, cause it to be replaced with a block message
- *Blocked input keywords* — words that, if found in the user's message, block the agent before it calls the LLM at all
- *Output format* — set to **JSON** if this agent is used as a router; forces structured output

Click **Save Agent**.

---

## 5. Testing an Agent Inline

Before wiring an agent into a workflow, test it directly.

1. On the Agents page, click the **chat bubble icon** on any agent card
2. A chat panel opens — type a message and press Enter (or click Send)
3. The agent responds using its real system prompt, tools, and model
4. Each message carries the full conversation history, so you can have a multi-turn dialogue

This is the fastest way to tune a system prompt without running a full workflow.

---

## 6. Building a Workflow from Scratch

Go to **Workflows → New Workflow** → enter a name → **Create Workflow**.

The workflow builder opens with a canvas containing a **Start** node and an **End** node.

### Adding agents to the canvas

Click the panel icon (top-left of the canvas toolbar) to open the node panel. You'll see:
- **Agent nodes** — one for each agent you've created
- **Router node** — a branching point
- **Approval node** — a human-review gate

Drag any agent onto the canvas. Repeat for each agent you want in the pipeline.

### Connecting nodes

Hover over the right edge of a node until a small circle handle appears. Click and drag to the left edge of the next node. A line (edge) connects them.

**Every workflow must follow this pattern:**
```
Start ──► [Agent(s)] ──► End
```

A workflow without a path from Start to End will not compile.

### Saving the layout

Click **Save** in the canvas toolbar after every change. Unsaved layouts are lost on navigation.

### Example: Two-agent research pipeline

1. Drag **Research Agent** onto canvas, connect `Start → Research Agent`
2. Drag **Summarizer Agent** onto canvas, connect `Research Agent → Summarizer Agent`
3. Connect `Summarizer Agent → End`
4. Click **Save**

---

## 7. Running a Workflow and Watching Live Logs

From the workflow builder, click **Run Workflow** (top-right button) or go to **Executions → Run**.

Enter your prompt:
```
Summarise the latest trends in renewable energy investment.
```

Click **Run**. The page redirects to the execution detail view.

### The Live Logs panel

Events stream in real time, colour-coded:

| Colour | Meaning |
|---|---|
| Blue | LLM starting (model name shown) |
| Yellow | Tool being called or returning a result |
| Green | LLM finished (with token count and cost) |
| Amber | Waiting for human approval |
| Grey | Routing decisions and info messages |
| Red | Error or guardrail triggered |

### The Messages tab

Click **Messages** (next to Live Logs) for a cleaner view. Each agent's final output is shown as a chat bubble with its name, timestamp, and token usage. This is what you'd show in a demo.

### Stat cards

Above the logs you'll see five cards:
- **Trigger** — the prompt that started the run
- **Started** — wall-clock start time
- **Duration** — total seconds (populated on completion)
- **Tokens** — input / output token counts across all agents
- **Cost** — estimated USD cost

---

## 8. Human-in-the-Loop Approval

The **Approval node** pauses a workflow mid-execution and waits for a human decision before continuing.

### Setting it up

1. In the workflow builder, drag an **Approval** node onto the canvas
2. Connect it between two agents: `Agent A → Approval → Agent B`
3. Save the workflow

### What happens at runtime

When the workflow reaches the Approval node:
- Execution pauses and status changes to **Awaiting Approval** (pulsing amber badge)
- The output from the previous agent is shown in the output panel
- Two buttons appear: **Approve — Continue** and **Reject with Feedback**

**If you Approve:** the workflow resumes and Agent B runs next.

**If you Reject:** a dialog asks for your feedback comment (e.g. *"Too brief — add more statistics"*). The previous agent receives your feedback and re-runs, producing a revised output. The Approval gate activates again, so you review the revision before continuing.

### Telegram approval

If the workflow was triggered via Telegram, the approval prompt is also sent directly to your Telegram chat as an inline keyboard with Approve / Reject buttons — no need to open the UI.

### Timeout

Workflows stuck in approval for longer than `APPROVAL_TIMEOUT_MINUTES` (default: 60 minutes) are automatically marked as failed. Configure this in `.env`.

---

## 9. Conditional Routing (Router Nodes)

A **Router node** branches the workflow based on what the previous agent output.

### When to use it

Use a Router when one agent's output should determine which agent runs next. Classic example: a Triage agent classifies an issue, and a Router sends it to the right specialist.

### Setting it up

1. Drag a **Router** node onto the canvas after your classifier agent
2. Draw multiple edges out of the Router — one per branch
3. Click any edge label to set its **condition** (a keyword or JSON value to match)
4. Leave one edge with no condition — it becomes the **default** (fallback) branch

**Example for a support triage:**
```
Triage Agent ──► Router ──billing──► Billing Specialist
                         ──technical► Tech Support
                         ──(no label)► General Support   ← default
```

### How conditions are matched

The router checks the previous agent's output in this priority order:

1. **Exact JSON value match** — if output is `{"category": "billing"}` and condition is `billing`, it matches
2. **JSON substring match** — condition appears anywhere in a JSON key or value
3. **Plain text match** — condition appears anywhere in the output text
4. **Default edge** — taken if no condition matched

**Best practice:** Set your classifier agent's Output Format to **JSON** (in the Guardrails section of the agent form). This produces deterministic, structured output that the router can match reliably. Example system prompt for a classifier:

```
Respond ONLY with valid JSON: {"category": "billing" | "technical" | "general"}
```

---

## 10. Custom Webhook Tools

You can give any agent the ability to call your own HTTP APIs.

Go to **Tools → New Tool**.

| Field | What to enter |
|---|---|
| **Name** | Lowercase letters/numbers/underscores, e.g. `weather_api` |
| **Display Name** | Human-readable, e.g. `Weather Lookup` |
| **Description** | One sentence — this is shown to the LLM when deciding to call the tool |
| **URL** | Your endpoint, e.g. `https://api.example.com/weather` |
| **Method** | GET, POST, PUT, PATCH, or DELETE |
| **Headers** | JSON object, e.g. `{"Authorization": "Bearer your-token"}` |
| **Body Template** | Request body with `{{input}}` as the placeholder for agent input |

**Body template example:**
```json
{"location": "{{input}}", "units": "metric"}
```

When the agent calls this tool, it passes whatever string it wants to look up and `{{input}}` is replaced automatically.

**Activating the tool:**
- Toggle the tool's **Active** switch on
- Open the agent you want to use it → tick the tool name in the Tools section → Save

The tool is immediately available to that agent in the next execution.

---

## 11. Scheduling a Workflow

Any workflow can be triggered automatically on a cron schedule.

1. Open **Workflows**, click on any workflow
2. Click **Settings** (top-right of the builder toolbar)
3. Set **Trigger Type** to `Scheduled (Cron)`
4. Choose a preset or enter a custom cron expression:

| Preset | Cron expression |
|---|---|
| Every hour | `0 * * * *` |
| Every day at 9am | `0 9 * * *` |
| Every Monday 9am | `0 9 * * 1` |
| Every 6 hours | `0 */6 * * *` |

5. Click **Save Settings**

The Celery Beat service (running alongside the worker) checks every 60 seconds and fires any workflows whose cron tick is due. No external cron setup needed.

> **Note:** Scheduled runs require the `beat` service to be running. If you started with `make dev`, it's already running. Check with `docker compose ps`.

---

## 12. Telegram Integration

Connect a workflow so users can trigger it by sending a message to a Telegram bot, and receive the agent's response directly in chat.

### Step 1 — Create a bot

1. Open Telegram and message `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the token (format: `123456789:ABCdef...`)

### Step 2 — Add the token

Two ways:

**Option A — Settings UI (no restart needed for existing containers)**

1. Go to **Settings → Telegram**
2. Paste your token → **Save**

**Option B — .env file**

```bash
# In .env:
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
```

### Step 3 — Start the Telegram service

```bash
make telegram
# or: docker compose --profile telegram up
```

### Step 4 — Get your chat ID

Message your bot `/start`. It replies with your chat ID.

### Step 5 — Link a workflow to Telegram

1. Open a workflow → **Settings** → set Trigger Type to `Telegram Message`
2. Enter your chat ID in **Allowed Chat IDs** (leave blank to accept all)
3. Save

### Using it

Send any message to your bot. The workflow runs and the final agent output is sent back to you in Telegram — typically within 30–60 seconds for a two-agent pipeline.

**Tip:** You can also message the bot directly without a linked workflow. Send `/agents` to see all available agents, then interact with them directly.

---

## 13. Managing Agent Memory

Every agent has its own ChromaDB vector store that persists across executions.

**How it works:**
- After each execution, the agent's input and output are stored as a vector embedding
- On the next execution, the 3 most semantically similar past interactions are retrieved and injected as context
- This lets agents remember previous conversations and build on them

**Viewing memory:**

Go to **Agents**, click any agent → view the memories from previous sessions shown on the agent card, or call `GET /api/v1/agents/{id}/memory` from the API.

**Clearing memory:**

If you want the agent to start fresh:
1. Click the memory icon on the agent card
2. Click **Clear Memory**

Or via API: `DELETE /api/v1/agents/{id}/memory`

**Disabling memory:**

In the agent form, uncheck **Enable Memory**. The agent will not retrieve or store any context.

---

## 14. The Settings Page

Go to **Settings** to manage:

### System status

Live health indicators for all backend services:
- **API** — FastAPI server
- **Redis** — message broker and pub/sub
- **Database** — SQLite connection

### Messaging Channels

Each channel has a token form and step-by-step setup instructions built in. Currently configured:

- **Telegram** — enter your bot token and follow the instructions panel

Token changes take effect immediately (stored in the `platform_settings` table). You still need to restart the channel's docker service after saving a new token.

---

## 15. Execution History and Logs

Go to **Executions** to see every past and current run.

### List view

Each row shows:
- The trigger prompt (first 80 characters)
- When it ran
- Current status with a colour-coded badge:

| Badge | Meaning |
|---|---|
| Pending | Queued, not yet started |
| Running (spinning) | Actively executing |
| Awaiting Approval | Paused at an approval gate |
| Completed (green) | Finished successfully |
| Failed (red) | Error — click to see the error message |
| Cancelled | Stopped manually |

### Detail view

Click any execution to open the detail view:

**Left panel — Live Logs / Messages tabs**
- *Live Logs*: raw event stream (terminal-style, monospace)
- *Messages*: agent outputs shown as chat bubbles — cleaner for sharing

**Right panel — Output**
- Final output from the last agent in the workflow
- If status is Awaiting Approval, the output and Approve/Reject buttons appear here

### Deleting executions

Click the trash icon to delete an execution and all its logs. If the execution is still running, it is cancelled first.

---

## 16. Troubleshooting

### "No agents yet" after setup
Run `make demo` to seed pre-built agents and workflows automatically.

### Workflow runs but agents produce no output
Check that your `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) is set in `.env` and not expired. The demo templates use `provider: demo` by default — switch to `openai` and set a real key.

### Router always takes the default branch
Your classifier agent's output doesn't match any condition. Two fixes:
1. Set the agent's Output Format to **JSON** and update its system prompt to output `{"category": "value"}`
2. Check that the condition string on the edge exactly matches the value (e.g. edge condition `billing` matches JSON `{"category": "billing"}`)

### WebSocket logs not streaming
The execution is running but the browser isn't receiving log events. Try:
1. Hard-refresh the page (`Cmd+Shift+R` / `Ctrl+Shift+R`)
2. Check Redis is healthy: `docker compose ps redis`
3. Click **Refresh** in the log panel header

### Telegram bot not responding
1. Confirm `TELEGRAM_BOT_TOKEN` is set in `.env`
2. Check the telegram_bot service is running: `docker compose ps telegram_bot`
3. Restart it: `docker compose restart telegram_bot`
4. The bot uses polling — no public URL or webhook setup required

### Approval workflow stuck forever
Executions in `awaiting_approval` for longer than `APPROVAL_TIMEOUT_MINUTES` (default 60) are auto-failed by the Beat scheduler. To change the timeout:
```bash
# In .env:
APPROVAL_TIMEOUT_MINUTES=30
```
Then restart: `docker compose restart beat`

### Port conflicts
If ports 3002 or 8000 are in use:
```bash
# Check what's using the port
lsof -i :3002
# Then either stop that process or edit docker-compose.yml port mappings
```

### Starting fresh
```bash
make clean    # stops containers, removes volumes, deletes ./backend/data
make dev      # start again with a clean slate
```

---

## Quick Reference

### Make commands

| Command | What it does |
|---|---|
| `make setup` | First-time: copies `.env.example` and builds images |
| `make dev` | Starts all services |
| `make telegram` | Starts all services + Telegram bot |
| `make demo` | Seeds demo data then starts |
| `make logs` | Tails all service logs |
| `make stop` | Stops all containers |
| `make clean` | Stops + removes all volumes and data |

### Key URLs

| URL | What |
|---|---|
| http://localhost:3002 | Main UI |
| http://localhost:8000/docs | Swagger API explorer |
| http://localhost:8000/api/v1/health | Health check |

### Agent configuration cheatsheet

| Setting | Recommended value | Notes |
|---|---|---|
| Model | `gpt-4o-mini` | Fast and cheap for most tasks |
| Temperature | `0.1–0.3` | For classifiers/routers that need consistency |
| Temperature | `0.6–0.8` | For writers/researchers that benefit from creativity |
| Max iterations | `5–10` | Higher for complex tool-using agents |
| Output format | `json` | For any agent used as a router |
| Memory | Enabled | Disable only for stateless classifier agents |

---

*For architecture details and how to extend the platform, see the [README](README.md).*
