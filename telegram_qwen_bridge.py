"""
Telegram-Qwen Autonomous Agent — Entry Point

Start via watchdog for auto-restart:
    python watchdog.py

Or directly:
    python telegram_qwen_bridge.py
"""

import logging
from bot.config import Config, logger
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bot.handlers import (
    cmd_start,
    cmd_help,
    cmd_reset,
    cmd_status,
    cmd_tasks,
    cmd_resume,
    cmd_selfupdate,
    cmd_dashboard,
    handle_message,
)
from bot.dashboard import start_dashboard
import threading


def main() -> None:
    """Start the Telegram-Qwen Agent."""
    Config.ensure_dirs()

    token = Config.TELEGRAM_BOT_TOKEN
    if not token or token == "your_token_here":
        print("ERROR: Set TELEGRAM_BOT_TOKEN in .env file")
        return

    if not Config.TELEGRAM_ADMIN_ID or Config.TELEGRAM_ADMIN_ID == "your_chat_id_here":
        print("WARNING: TELEGRAM_ADMIN_ID not set. Bot will accept messages from anyone.")

    try:
        app = ApplicationBuilder().token(token).build()

        # Register command handlers
        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("help", cmd_help))
        app.add_handler(CommandHandler("reset", cmd_reset))
        app.add_handler(CommandHandler("status", cmd_status))
        app.add_handler(CommandHandler("tasks", cmd_tasks))
        app.add_handler(CommandHandler("resume", cmd_resume))
        app.add_handler(CommandHandler("selfupdate", cmd_selfupdate))
        app.add_handler(CommandHandler("dashboard", cmd_dashboard))

        # Register message handler
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

        # Start Dashboard in background thread
        dash_thread = threading.Thread(target=start_dashboard, daemon=True)
        dash_thread.start()

        logger.info("Telegram-Qwen Autonomous Agent v2.0 starting...")
        logger.info(f"Max tool turns: {Config.MAX_TOOL_TURNS}")
        logger.info(f"Qwen timeout: {Config.QWEN_TIMEOUT}s")
        logger.info(f"Max retries: {Config.MAX_RETRIES}")
        print("Bot is running. Press Ctrl+C to stop.")
        print("For auto-restart support, use: python watchdog.py")
        app.run_polling()

    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()