"""
Telegram bot handlers — menu-driven UX.

Session modes per chat_id (in-memory):
  {"mode": "idle"}
  {"mode": "agent",    "agent_id": str,    "agent_name": str}
  {"mode": "workflow", "workflow_id": str, "workflow_name": str}
"""

import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.integrations.telegram.router import (
    list_agents_sync,
    list_workflows_sync,
    create_execution,
    get_workflow_sync,
    get_execution_workflow_sync,
)

def _esc(text: str) -> str:
    """Escape Markdown v1 special chars in user-supplied text."""
    return re.sub(r'([_*`\[])', r'\\\1', text or "")


# Per-chat session state (process-lifetime; fine for a single bot process)
_sessions: dict[int, dict] = {}

# ── Keyboards ──────────────────────────────────────────────────────────────────

def _main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 Chat with Agent", callback_data="list_agents"),
            InlineKeyboardButton("⚙️ Run Workflow",    callback_data="list_workflows"),
        ],
        [
            InlineKeyboardButton("📊 My Status", callback_data="status"),
            InlineKeyboardButton("❓ Help",       callback_data="help"),
        ],
    ])


def _agents_keyboard(agents: list[dict]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"🤖 {a['name']}", callback_data=f"connect_agent:{a['id']}")] for a in agents]
    rows.append([InlineKeyboardButton("← Back to Menu", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


def _workflows_keyboard(workflows: list[dict]) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(f"⚙️ {w['name']}", callback_data=f"connect_workflow:{w['id']}")] for w in workflows]
    rows.append([InlineKeyboardButton("← Back to Menu", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("← Back to Menu", callback_data="menu")]])


# ── Session helpers ────────────────────────────────────────────────────────────

def _session(chat_id: int) -> dict:
    return _sessions.setdefault(chat_id, {"mode": "idle"})


def _set_idle(chat_id: int):
    _sessions[chat_id] = {"mode": "idle"}


def _set_agent(chat_id: int, agent_id: str, agent_name: str):
    _sessions[chat_id] = {"mode": "agent", "agent_id": agent_id, "agent_name": agent_name}


def _set_workflow(chat_id: int, workflow_id: str, workflow_name: str):
    _sessions[chat_id] = {"mode": "workflow", "workflow_id": workflow_id, "workflow_name": workflow_name}


def _set_rejection(chat_id: int, execution_id: str, workflow_id: str):
    _sessions[chat_id] = {"mode": "rejection", "execution_id": execution_id, "workflow_id": workflow_id}


# ── Command handlers ───────────────────────────────────────────────────────────

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    _set_idle(chat_id)
    await update.message.reply_text(
        "👋 *Welcome to AgentFlow!*\n\n"
        "I can connect you to AI agents for direct chat or trigger your automated workflows.\n\n"
        f"Your chat ID: `{chat_id}`\n\n"
        "What would you like to do?",
        parse_mode="Markdown",
        reply_markup=_main_menu_keyboard(),
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*AgentFlow Bot — Commands*\n\n"
        "/start — Main menu\n"
        "/agents — List agents and connect\n"
        "/workflows — List workflows and connect\n"
        "/status — Show current connection\n"
        "/disconnect — Return to idle\n"
        "/help — This message\n\n"
        "While connected to an *agent*, just type your message — it goes directly to the AI.\n"
        "While connected to a *workflow*, type your input to trigger a run.",
        parse_mode="Markdown",
        reply_markup=_back_keyboard(),
    )


async def handle_agents_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agents = list_agents_sync()
    if not agents:
        await update.message.reply_text(
            "No agents found. Create agents in the AgentFlow UI first.",
            reply_markup=_back_keyboard(),
        )
        return
    await update.message.reply_text(
        f"🤖 *Available Agents* ({len(agents)})\n\nSelect an agent to start chatting:",
        parse_mode="Markdown",
        reply_markup=_agents_keyboard(agents),
    )


async def handle_workflows_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    workflows = list_workflows_sync()
    if not workflows:
        await update.message.reply_text(
            "No active workflows found. Create workflows in the AgentFlow UI first.",
            reply_markup=_back_keyboard(),
        )
        return
    await update.message.reply_text(
        f"⚙️ *Available Workflows* ({len(workflows)})\n\nSelect a workflow to connect:",
        parse_mode="Markdown",
        reply_markup=_workflows_keyboard(workflows),
    )


async def handle_status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sess = _session(chat_id)
    mode = sess["mode"]
    if mode == "agent":
        text = f"📡 *Connected to agent:* {_esc(sess['agent_name'])}\n\nSend any message to chat. /disconnect to exit."
    elif mode == "workflow":
        text = f"📡 *Connected to workflow:* {_esc(sess['workflow_name'])}\n\nSend any message to trigger a run. /disconnect to exit."
    else:
        text = "💤 *Idle* — not connected to anything.\n\nUse /agents or /workflows to connect."
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=_back_keyboard())


async def handle_skip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Submit a rejection without feedback (used in the rejection comment flow)."""
    chat_id = update.effective_chat.id
    sess = _session(chat_id)
    if sess["mode"] != "rejection":
        await update.message.reply_text("Nothing to skip right now.")
        return
    execution_id = sess["execution_id"]
    workflow_id = sess["workflow_id"]
    _set_idle(chat_id)
    await update.message.reply_text("❌ Rejected (no feedback). Resuming workflow…")
    from app.workers.execution_tasks import resume_workflow_task
    resume_workflow_task.delay(workflow_id, execution_id, "rejected", "")


async def handle_disconnect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    sess = _session(chat_id)
    if sess["mode"] == "idle":
        await update.message.reply_text("You are not connected to anything.", reply_markup=_main_menu_keyboard())
        return
    name = sess.get("agent_name") or sess.get("workflow_name", "")
    _set_idle(chat_id)
    await update.message.reply_text(
        f"✅ Disconnected from *{_esc(name)}*. Back to idle.",
        parse_mode="Markdown",
        reply_markup=_main_menu_keyboard(),
    )


# ── Callback query handler ─────────────────────────────────────────────────────

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    data = query.data or ""

    # ── Main menu ──
    if data == "menu":
        _set_idle(chat_id)
        await query.edit_message_text(
            "👋 *AgentFlow — Main Menu*\n\nWhat would you like to do?",
            parse_mode="Markdown",
            reply_markup=_main_menu_keyboard(),
        )
        return

    # ── Help ──
    if data == "help":
        await query.edit_message_text(
            "*AgentFlow Bot — Commands*\n\n"
            "/start — Main menu\n"
            "/agents — List & connect to an agent\n"
            "/workflows — List & connect to a workflow\n"
            "/status — Show current connection\n"
            "/disconnect — Return to idle\n\n"
            "While connected to an *agent*, just type your message.\n"
            "While connected to a *workflow*, type your input to trigger a run.",
            parse_mode="Markdown",
            reply_markup=_back_keyboard(),
        )
        return

    # ── Status ──
    if data == "status":
        sess = _session(chat_id)
        mode = sess["mode"]
        if mode == "agent":
            text = f"📡 *Connected to agent:* {_esc(sess['agent_name'])}\n\nSend any message to chat."
        elif mode == "workflow":
            text = f"📡 *Connected to workflow:* {_esc(sess['workflow_name'])}\n\nSend any message to trigger a run."
        else:
            text = "💤 *Idle* — use the buttons below to connect."
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=_back_keyboard())
        return

    # ── List agents ──
    if data == "list_agents":
        agents = list_agents_sync()
        if not agents:
            await query.edit_message_text(
                "No agents found. Create agents in the AgentFlow UI first.",
                reply_markup=_back_keyboard(),
            )
            return
        await query.edit_message_text(
            f"🤖 *Available Agents* ({len(agents)})\n\nSelect an agent to start chatting:",
            parse_mode="Markdown",
            reply_markup=_agents_keyboard(agents),
        )
        return

    # ── List workflows ──
    if data == "list_workflows":
        workflows = list_workflows_sync()
        if not workflows:
            await query.edit_message_text(
                "No active workflows found. Create workflows in the AgentFlow UI first.",
                reply_markup=_back_keyboard(),
            )
            return
        await query.edit_message_text(
            f"⚙️ *Available Workflows* ({len(workflows)})\n\nSelect a workflow to connect:",
            parse_mode="Markdown",
            reply_markup=_workflows_keyboard(workflows),
        )
        return

    # ── Connect to agent ──
    if data.startswith("connect_agent:"):
        agent_id = data.split(":", 1)[1]
        agents = list_agents_sync()
        agent = next((a for a in agents if a["id"] == agent_id), None)
        if not agent:
            await query.edit_message_text("Agent not found.", reply_markup=_back_keyboard())
            return
        _set_agent(chat_id, agent_id, agent["name"])
        role_line = f"*Role:* {_esc(agent['role'])}\n" if agent.get("role") else ""
        desc_line = f"_{_esc(agent['description'])}_\n\n" if agent.get("description") else "\n"
        await query.edit_message_text(
            f"✅ *Connected to {_esc(agent['name'])}*\n\n"
            f"{role_line}{desc_line}"
            "Just send me a message and I'll pass it to this agent.\n"
            "Use /disconnect when you're done.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔌 Disconnect", callback_data="disconnect_confirm"),
                InlineKeyboardButton("← Menu", callback_data="menu"),
            ]]),
        )
        return

    # ── Connect to workflow ──
    if data.startswith("connect_workflow:"):
        workflow_id = data.split(":", 1)[1]
        workflow = get_workflow_sync(workflow_id)
        if not workflow:
            await query.edit_message_text("Workflow not found.", reply_markup=_back_keyboard())
            return
        _set_workflow(chat_id, workflow_id, workflow["name"])
        desc_line = f"_{_esc(workflow['description'])}_\n\n" if workflow.get("description") else "\n"
        await query.edit_message_text(
            f"✅ *Connected to workflow: {_esc(workflow['name'])}*\n\n"
            f"{desc_line}"
            "Send me any message to trigger a run with that as the input.\n"
            "Use /disconnect when you're done.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔌 Disconnect", callback_data="disconnect_confirm"),
                InlineKeyboardButton("← Menu", callback_data="menu"),
            ]]),
        )
        return

    # ── Disconnect confirm ──
    if data == "disconnect_confirm":
        sess = _session(chat_id)
        name = sess.get("agent_name") or sess.get("workflow_name", "")
        _set_idle(chat_id)
        await query.edit_message_text(
            f"✅ Disconnected{f' from *{_esc(name)}*' if name else ''}. Back to idle.",
            parse_mode="Markdown",
            reply_markup=_main_menu_keyboard(),
        )
        return

    # ── Workflow approval: Approve ──
    if data.startswith("approve_wf:"):
        execution_id = data.split(":", 1)[1]
        rec = get_execution_workflow_sync(execution_id)
        if not rec:
            await query.edit_message_text("❌ Execution not found or already resolved.")
            return
        await query.edit_message_text(
            "✅ Approved — resuming workflow…",
        )
        from app.workers.execution_tasks import resume_workflow_task
        resume_workflow_task.delay(rec["workflow_id"], execution_id, "approved", "")
        return

    # ── Workflow approval: Reject ──
    if data.startswith("reject_wf:"):
        execution_id = data.split(":", 1)[1]
        rec = get_execution_workflow_sync(execution_id)
        if not rec:
            await query.edit_message_text("❌ Execution not found or already resolved.")
            return
        _set_rejection(chat_id, execution_id, rec["workflow_id"])
        await query.edit_message_text(
            "❌ Rejected.\n\n"
            "Please type your reason for rejection (or /skip to reject without feedback):",
        )
        return


# ── Message handler ────────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()
    sess = _session(chat_id)

    # ── Idle — nudge user ──
    if sess["mode"] == "idle":
        await update.message.reply_text(
            "I'm not connected to anything yet.\n\nUse the menu to connect to an agent or workflow:",
            reply_markup=_main_menu_keyboard(),
        )
        return

    # ── Rejection comment ──
    if sess["mode"] == "rejection":
        execution_id = sess["execution_id"]
        workflow_id = sess["workflow_id"]
        comment = text
        _set_idle(chat_id)
        await update.message.reply_text(
            f"❌ Rejected with feedback: \"{comment}\"\n\nResuming workflow with rejection…",
        )
        from app.workers.execution_tasks import resume_workflow_task
        resume_workflow_task.delay(workflow_id, execution_id, "rejected", comment)
        return

    # ── Agent direct chat ──
    if sess["mode"] == "agent":
        agent_id = sess["agent_id"]
        agent_name = sess["agent_name"]
        await update.message.reply_text(
            f"💬 Sending to *{_esc(agent_name)}*… please wait.",
            parse_mode="Markdown",
        )
        from app.workers.execution_tasks import run_agent_direct_task
        run_agent_direct_task.delay(agent_id, chat_id, text)
        return

    # ── Workflow run ──
    if sess["mode"] == "workflow":
        workflow_id = sess["workflow_id"]
        workflow_name = sess["workflow_name"]
        execution_id = create_execution(workflow_id, chat_id, text)
        if not execution_id:
            await update.message.reply_text("❌ Failed to start workflow. Please try again.")
            return
        await update.message.reply_text(
            f"⚙️ Running *{_esc(workflow_name)}*…\n\nI'll reply when done (usually 30-60 seconds).",
            parse_mode="Markdown",
        )
        from app.workers.execution_tasks import run_workflow_task
        run_workflow_task.delay(workflow_id, execution_id, {"prompt": text, "chat_id": chat_id})
        return
