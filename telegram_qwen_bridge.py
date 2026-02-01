import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hello! Send me a message and I will forward it to Qwen CLI.')

def handle_message(update: Update, context: CallbackContext) -> None:
    """Handle incoming messages and forward to Qwen CLI."""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    # Log the received message
    logger.info(f"Received message from chat {chat_id}: {user_message}")

    try:
        # Execute Qwen CLI with the user's message as input
        # Note: This assumes Qwen CLI accepts input via stdin
        result = subprocess.run(
            ['qwen', 'chat'],  # Adjust this command based on how your CLI works
            input=user_message,
            text=True,
            capture_output=True,
            timeout=30  # Timeout after 30 seconds
        )

        # Get the output from Qwen CLI
        response = result.stdout

        # If there's an error, include stderr
        if result.returncode != 0:
            response = f"Error: {result.stderr}"

        # Send the response back to the user
        update.message.reply_text(response[:4096])  # Telegram message limit is 4096 chars
        
    except subprocess.TimeoutExpired:
        update.message.reply_text("Sorry, the Qwen CLI took too long to respond.")
    except FileNotFoundError:
        update.message.reply_text("Error: Qwen CLI not found. Please ensure it's installed and in PATH.")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        update.message.reply_text(f"An error occurred: {str(e)}")

def main() -> None:
    """Start the bot."""
    # Get the token from environment variable
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Create the Updater
    updater = Updater(token)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Start the bot
    logger.info("Starting bot...")
    updater.start_polling()
    
    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()