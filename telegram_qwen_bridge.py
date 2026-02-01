"""
Telegram-Qwen Bridge
A Python bot that connects Telegram with the Qwen AI model, allowing you to interact with your computer through Telegram messages.
"""

import os
import subprocess
import logging
import asyncio
import json
import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Constants
CHAT_HISTORY_FILE = "chat_history.json"
MAX_MESSAGE_LENGTH = 4096
COMMAND_TIMEOUT = 60
QWEN_TIMEOUT = 120
MAX_HISTORY_MESSAGES = 20
MAX_OUTPUT_LENGTH = 8000
MAX_TURN_COUNT = 10

# Utility to escape markdown characters
def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Hello! I am your Qwen PC Controller.\n\n"
        "Available commands:\n"
        "/id - Get your Chat ID\n"
        "/exec <command> - Execute a shell command\n"
        "/reset - Clear chat history\n\n"
        "Simply send me a message to interact with Qwen AI."
    )
    await update.message.reply_text(welcome_message)

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Returns the user's Chat ID."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your Chat ID is: `{chat_id}`", parse_mode='Markdown')
    logger.info(f"User {update.effective_user.username} requested ID: {chat_id}")

async def exec_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Execute a shell command on the PC (Owner only)."""
    # Authorization check
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID')
    user_id = str(update.effective_chat.id)

    if admin_id and user_id != admin_id:
        await update.message.reply_text("⛔ Access Denied. You are not the authorized admin.")
        return

    command = ' '.join(context.args)
    if not command:
        await update.message.reply_text("Usage: /exec <command>")
        return

    logger.info(f"User {update.effective_user.id} executing command: {command}")
    msg = await update.message.reply_text(f"Executing: `{command}`...", parse_mode='Markdown')

    try:
        # Fix for "command not recognized" on Windows for manual /exec
        full_command = command
        if os.name == 'nt' and not (command.lower().startswith('cmd') or command.lower().startswith('powershell')):
            full_command = f'cmd /c {command}'

        process = await asyncio.create_subprocess_shell(
            full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=COMMAND_TIMEOUT)

        output = stdout.decode().strip()
        error = stderr.decode().strip()

        full_response = ""
        if output:
            full_response += f"**Output:**\n```\n{output}\n```"
        if error:
            full_response += f"\n**Error:**\n```\n{error}\n```"

        if not full_response:
            full_response = "Command executed with no output."

        # Split long messages and send
        for i in range(0, len(full_response), MAX_MESSAGE_LENGTH):
            chunk = full_response[i:i+MAX_MESSAGE_LENGTH]
            await update.message.reply_text(chunk, parse_mode='Markdown')

    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ Command timed out after 60 seconds.")
    except Exception as e:
        logger.error(f"Command execution failed: {str(e)}")
        await update.message.reply_text(f"Execution failed: {str(e)}")
# Global Memory
CHAT_HISTORY: List[str] = []

def load_history():
    """Load chat history from file."""
    global CHAT_HISTORY
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                CHAT_HISTORY = json.load(f)
            logger.info(f"Loaded {len(CHAT_HISTORY)} messages from history.")
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            CHAT_HISTORY = []

def save_history():
    """Save chat history to file."""
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(CHAT_HISTORY, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save history: {e}")

async def reset_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset chat history."""
    global CHAT_HISTORY
    CHAT_HISTORY = []
    save_history()
    await update.message.reply_text("🧹 Memory wiped! I am a blank slate.")

# Thread-safe logging
audit_lock = asyncio.Lock()

async def write_audit_log(content: str):
    """Write audit log entry safely."""
    async with audit_lock:
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("audit.log", "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {content}\n")
        except Exception as e:
            logger.error(f"Audit log write failed: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and forward to Qwen CLI."""
    user_message = update.message.text
    chat_id = update.effective_chat.id

    # Authorization check for chat execution
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID')
    if admin_id and str(chat_id) != admin_id:
        await update.message.reply_text("🔒 Access denied. You are not authorized to use this bot.")
        return

    logger.info(f"Processing message from user {update.effective_user.id}: {user_message}")

    # Inject instruction for Agentic behavior
    base_system_instruction = (
        "TASK: You are a Command Line tool with Agentic capabilities.\n"
        "INPUT: Chat History + New Request\n"
        "OUTPUT: Standard [EXEC] formatted command OR Final Answer.\n\n"
        "AVAILABLE TOOLS:\n"
        "1. List Files: [EXEC]ls[/EXEC] (Linux/Mac) or [EXEC]dir[/EXEC] (Windows)\n"
        "2. Web Research: [EXEC]python tools/web_reader.py <URL>[/EXEC]\n"
        "   - Use this to read website content.\n"
        "   - NOTE: You CANNOT interact (comment/post) with websites, only read them.\n"
        "3. Run Python: [EXEC]python -c \"...\"[/EXEC] (For simple scripts)\n"
        "   - You can use 'requests', 'json', etc.\n"
        "RULES:\n"
        "1. Output [EXEC]...[/EXEC] for actions.\n"
        "2. Completed? Output Final Answer as text.\n"
        "3. No chatter during execution.\n\n"
    )

    # Initialize chat history if not already done
    global CHAT_HISTORY

    # Update History with new User Message
    CHAT_HISTORY.append(f"USER: {user_message}")
    save_history()

    # Context Pruning for Prompt (keep last few messages for context window)
    recent_history = CHAT_HISTORY[-MAX_HISTORY_MESSAGES:]
    session_history = "\n".join(recent_history) + "\n"

    # ReAct Loop
    for turn in range(MAX_TURN_COUNT):
        await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)

        full_prompt = base_system_instruction + "Here is the conversation history:\n" + session_history + "OUTPUT: "

        try:
            logger.info(f"Starting turn {turn + 1}")

            # Start Qwen process
            process = await asyncio.create_subprocess_shell(
                "qwen",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=full_prompt.encode()),
                    timeout=QWEN_TIMEOUT
                )

                # Check if stderr has content which might indicate an error
                if stderr:
                    stderr_content = stderr.decode().strip()
                    if stderr_content:
                        logger.warning(f"Qwen process stderr: {stderr_content}")

                if not stdout:
                    logger.error("Qwen process returned empty stdout")
                    if turn == 0:
                        await update.message.reply_text("❌ Qwen returned an empty response. Please try again.")
                    continue  # Continue to next turn or break if needed

                response = stdout.decode().strip()

            except asyncio.TimeoutError:
                process.kill()
                if turn == 0:
                    await update.message.reply_text("⏰ Qwen took too long to respond.")
                logger.warning("Qwen process timed out")
                return
            except Exception as e:
                logger.error(f"Error communicating with Qwen: {e}")
                if turn == 0:
                    await update.message.reply_text(f"❌ Error communicating with Qwen: {e}")
                return

            # Audit Log
            await write_audit_log(f"TURN {turn+1} - Response: {response[:200]}...")

            # Parse Output for [EXEC] blocks
            import re
            exec_blocks = re.findall(r'\[EXEC\](.*?)\[/EXEC\]', response, re.DOTALL)

            # CASE A: Final Answer (No Commands to execute)
            if not exec_blocks:
                logger.info("Received final answer from Qwen")

                # Send response to user
                if response:
                    # Split long messages
                    for i in range(0, len(response), MAX_MESSAGE_LENGTH):
                        chunk = response[i:i+MAX_MESSAGE_LENGTH]
                        await update.message.reply_text(chunk, parse_mode=None)
                else:
                    await update.message.reply_text("Received empty response from Qwen.")

                # Save Agent Response to History
                CHAT_HISTORY.append(f"QWEN: {response}")
                save_history()
                break

            # CASE B: Execute Commands (Intermediate Step)
            for cmd in exec_blocks:
                cmd = cmd.strip().strip('"').strip("'")
                logger.info(f"Executing command: {cmd}")

                await update.message.reply_text(f"⚙️ Executing step {turn+1}: `{cmd}`", parse_mode='Markdown')

                # Run Shell Command
                full_command = cmd
                # Handle Windows-specific command execution
                if os.name == 'nt' and not (cmd.lower().startswith('cmd') or cmd.lower().startswith('powershell')):
                    full_command = f'cmd /c {cmd}'

                logger.info(f"Executing command: {full_command}")

                try:
                    # For Python scripts, we might need to ensure output is flushed
                    proc = await asyncio.create_subprocess_shell(
                        full_command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    out, err = await proc.communicate()

                    # Check the return code to see if the command succeeded
                    if proc.returncode != 0:
                        logger.warning(f"Command '{full_command}' exited with code {proc.returncode}")

                except Exception as cmd_error:
                    logger.error(f"Failed to execute command '{full_command}': {cmd_error}")
                    cmd_output = f"Command execution failed: {cmd_error}"
                    out, err = None, None

                # Decode Output
                if out is not None or err is not None:
                    try:
                        cmd_output = out.decode('utf-8').strip() if out else ""
                        cmd_error = err.decode('utf-8').strip() if err else ""
                        cmd_output = cmd_output + "\n" + cmd_error if cmd_error else cmd_output

                        # If the output is empty but the command was a Python script,
                        # it might be because print statements weren't flushed
                        if not cmd_output and 'python' in cmd.lower():
                            logger.warning(f"Python command '{cmd}' returned empty output - this might be due to buffering")

                    except UnicodeDecodeError:
                        cmd_output = out.decode('cp850', errors='replace').strip() if out else ""
                        cmd_error = err.decode('cp850', errors='replace').strip() if err else ""
                        cmd_output = cmd_output + "\n" + cmd_error if cmd_error else cmd_output
                else:
                    # This case occurs when command execution failed completely
                    cmd_output = "Command execution failed and produced no output"

                # Truncate output if too long
                truncated_output = cmd_output[:MAX_OUTPUT_LENGTH]
                if len(cmd_output) > MAX_OUTPUT_LENGTH:
                    truncated_output += "\n...[Output Truncated]..."

                # Update Loop History
                session_history += f"OUTPUT: [EXEC]{cmd}[/EXEC]\nRESULT: {truncated_output}\n"

                # Update Global History
                CHAT_HISTORY.append(f"QWEN ACTION: {cmd}\nRESULT: {truncated_output[:500]}...")
                save_history()

                # Send OUTPUT to User (with fallback for long messages)
                try:
                    display_text = f"**Result:**\n```\n{cmd_output[:2000]}\n```"
                    if len(cmd_output) > 2000:
                        display_text = f"**Result:**\n```\n{cmd_output[:2000]}\n```\n...[Truncated - see full output in logs]"

                    # Split if still too long
                    for i in range(0, len(display_text), MAX_MESSAGE_LENGTH):
                        chunk = display_text[i:i+MAX_MESSAGE_LENGTH]
                        await update.message.reply_text(chunk, parse_mode='Markdown')

                except Exception as e:
                    logger.warning(f"Markdown formatting failed: {e}")
                    # Fallback to plain text
                    msg_content = f"Result:\n{cmd_output[:2000]}"
                    if len(cmd_output) > 2000:
                        msg_content += "... (truncated)"

                    for i in range(0, len(msg_content), MAX_MESSAGE_LENGTH):
                        chunk = msg_content[i:i+MAX_MESSAGE_LENGTH]
                        await update.message.reply_text(chunk, parse_mode=None)

                # Log Result
                await write_audit_log(f"CMD '{cmd}' RESULT: {truncated_output[:500]}...")

        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error in turn {turn}: {e}")
            await update.message.reply_text(f"❌ Subprocess error: {str(e)}")
            break
        except Exception as e:
            logger.error(f"Error in turn {turn}: {e}")
            await update.message.reply_text(f"❌ Error: {str(e)}")
            break

def main() -> None:
    """Main function to start the Telegram bot."""
    load_dotenv()

    # Load Memory
    load_history()

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
        app.add_handler(CommandHandler("reset", reset_history))
        app.add_handler(CommandHandler("id", get_id))
        app.add_handler(CommandHandler("exec", exec_command))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

        logger.info("Telegram-Qwen Bridge Bot Starting...")
        print("Bot is running. Press Ctrl+C to stop.")
        app.run_polling()

    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.critical(f"Critical startup error: {e}")
        print(f"Critical error at startup: {e}")

        # Fallback event loop for older Python versions
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            main()
        except Exception as fallback_error:
            logger.critical(f"Fallback also failed: {fallback_error}")
            print(f"Fallback also failed: {fallback_error}")