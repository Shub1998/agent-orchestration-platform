from telegram import Update
from telegram.ext import ContextTypes
from app.integrations.telegram.router import find_workflow_for_chat, create_execution


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"👋 Hello! I'm AgentFlow's AI assistant.\n\n"
        f"Your chat ID is: `{chat_id}`\n\n"
        f"Send me a message and I'll route it to the appropriate AI workflow!\n\n"
        f"Use this chat ID when configuring Telegram-enabled workflows in the AgentFlow UI.",
        parse_mode="Markdown"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    workflow = find_workflow_for_chat(chat_id)
    if not workflow:
        await update.message.reply_text(
            "No active workflow is configured for this chat. "
            "Please configure a Telegram-enabled workflow in AgentFlow."
        )
        return

    execution_id = create_execution(workflow["id"], chat_id, text)
    if not execution_id:
        await update.message.reply_text("Failed to start workflow. Please try again.")
        return

    await update.message.reply_text(
        f"Processing your request with workflow: *{workflow['name']}*\n"
        f"I'll reply when done (usually 30-60 seconds).",
        parse_mode="Markdown"
    )

    from app.workers.execution_tasks import run_workflow_task
    run_workflow_task.delay(workflow["id"], execution_id, {"prompt": text, "chat_id": chat_id})


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*AgentFlow Bot Help*\n\n"
        "/start - Get your chat ID and info\n"
        "/help - Show this help message\n\n"
        "Just send any message to trigger the configured AI workflow!",
        parse_mode="Markdown"
    )
