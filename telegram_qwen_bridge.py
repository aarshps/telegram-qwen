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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text('Hello! Send me a message and I will forward it to Qwen CLI.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and forward to Qwen CLI."""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    # Log the received message
    logger.info(f"Received message from chat {chat_id}: {user_message}")

    try:
        # Run Qwen CLI as a subprocess
        # We use asyncio.create_subprocess_exec for non-blocking execution
        process = await asyncio.create_subprocess_exec(
            'qwen', '-p', user_message,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Wait for the command to finish with a timeout
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
            
            response = stdout.decode().strip()
            error = stderr.decode().strip()

            if process.returncode != 0:
                response = f"Error: {error if error else 'Unknown error'}"
            elif not response:
                response = "Qwen returned an empty response."

            # Send the response back to the user
            # Telegram message limit is 4096 chars
            for i in range(0, len(response), 4096):
                await update.message.reply_text(response[i:i+4096])

        except asyncio.TimeoutExpired:
            process.kill()
            await update.message.reply_text("Sorry, the Qwen CLI took too long to respond.")
        
    except FileNotFoundError:
        await update.message.reply_text("Error: Qwen CLI not found. Please ensure it's installed and in PATH.")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await update.message.reply_text(f"An error occurred: {str(e)}")

def main() -> None:
    """Start the bot."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get the token from environment variable
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        print("\nERROR: TELEGRAM_BOT_TOKEN not found.")
        print("Please create a .env file with your token: TELEGRAM_BOT_TOKEN=your_token_here\n")
        return
    
    # Create the Application
    application = ApplicationBuilder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling()

if __name__ == '__main__':
    main()