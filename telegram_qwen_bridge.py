"""
Simple Telegram-Qwen Bridge
A minimal bot that connects Telegram with the Qwen AI model.
"""

import os
import subprocess
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Constants
MAX_MESSAGE_LENGTH = 4096
QWEN_TIMEOUT = 120


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Hello! I am Qwen AI.\n\n"
        "Just send me a message and I'll respond!"
    )
    await update.message.reply_text(welcome_message)


async def call_qwen(prompt: str) -> str:
    """Call the Qwen CLI with the given prompt."""
    try:
        # Start Qwen process
        process = await asyncio.create_subprocess_shell(
            "qwen",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=prompt.encode()),
            timeout=QWEN_TIMEOUT
        )

        if stderr:
            stderr_content = stderr.decode().strip()
            if stderr_content:
                logger.warning(f"Qwen process stderr: {stderr_content}")

        if not stdout:
            logger.error("Qwen process returned empty stdout")
            return "Sorry, I couldn't get a response from Qwen."

        response = stdout.decode().strip()
        return response

    except asyncio.TimeoutError:
        logger.warning("Qwen process timed out")
        return "Qwen took too long to respond."
    except Exception as e:
        logger.error(f"Error communicating with Qwen: {e}")
        return f"Error: {str(e)}"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and forward to Qwen."""
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    # Authorization check
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID')
    if admin_id and str(chat_id) != admin_id:
        await update.message.reply_text("🔒 Access denied. You are not authorized to use this bot.")
        return

    logger.info(f"Processing message from user {update.effective_user.id}: {user_message}")

    # Send typing action
    from telegram import constants
    await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

    try:
        # Call Qwen with the user's message
        response = await call_qwen(user_message)
        
        # Send response back to user (split if too long)
        if len(response) <= MAX_MESSAGE_LENGTH:
            await update.message.reply_text(response)
        else:
            # Split long messages
            for i in range(0, len(response), MAX_MESSAGE_LENGTH):
                chunk = response[i:i+MAX_MESSAGE_LENGTH]
                await update.message.reply_text(chunk)
                
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}")


def main() -> None:
    """Main function to start the Telegram bot."""
    load_dotenv()

    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID')

    if not token or token == "your_token_here":
        print("ERROR: Please set TELEGRAM_BOT_TOKEN in .env file")
        return

    if not admin_id or admin_id == "your_chat_id_here":
        print("WARNING: TELEGRAM_ADMIN_ID not set in .env file. Bot will accept messages from any user.")
        print("For security, set TELEGRAM_ADMIN_ID to your Telegram chat ID.")

    try:
        app = ApplicationBuilder().token(token).job_queue(None).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

        logger.info("Simple Telegram-Qwen Bridge Bot Starting...")
        print("Bot is running. Press Ctrl+C to stop.")
        app.run_polling()

    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()