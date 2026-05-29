import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.config import settings
from app.integrations.telegram.handlers import handle_start, handle_message, handle_help


def main():
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN not set. Telegram bot will not start.")
        return

    print("Starting AgentFlow Telegram bot...")
    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Telegram bot polling started. Press Ctrl+C to stop.")
    # run_polling() in PTB >= 20 manages its own event loop — do NOT wrap in asyncio.run()
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
