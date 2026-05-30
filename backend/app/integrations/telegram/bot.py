import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from app.config import settings
from app.integrations.telegram.handlers import (
    handle_start,
    handle_help,
    handle_agents_cmd,
    handle_workflows_cmd,
    handle_status_cmd,
    handle_disconnect_cmd,
    handle_skip_cmd,
    handle_callback,
    handle_message,
)


def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set. Telegram bot will not start.")
        return

    print("Starting AgentFlow Telegram bot...")
    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",      handle_start))
    app.add_handler(CommandHandler("help",       handle_help))
    app.add_handler(CommandHandler("agents",     handle_agents_cmd))
    app.add_handler(CommandHandler("workflows",  handle_workflows_cmd))
    app.add_handler(CommandHandler("status",     handle_status_cmd))
    app.add_handler(CommandHandler("disconnect", handle_disconnect_cmd))
    app.add_handler(CommandHandler("skip",       handle_skip_cmd))

    # Inline-button callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Plain text messages (must be last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram bot polling started. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
