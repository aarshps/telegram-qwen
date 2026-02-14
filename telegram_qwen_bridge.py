"""
Simple Telegram-Qwen Bridge with General Agent Capabilities
A bot that connects Telegram with the Qwen AI model with basic agent capabilities.
"""

import os
import subprocess
import logging
import asyncio
import json
import re
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
MAX_MESSAGE_LENGTH = 4096
MAX_OUTPUT_LENGTH = 2000
QWEN_TIMEOUT = 300  # Increased to 5 minutes for longer processing


def extract_tool_calls(text):
    """Extract tool calls from text."""
    patterns = {
        'WEB_READ': r'\\[WEB_READ\\](.*?)\\[/WEB_READ\\]',
        'FILE_READ': r'\\[FILE_READ\\](.*?)\\[/FILE_READ\\]',
        'FILE_WRITE': r'\\[FILE_WRITE\\](.*?)\\[/FILE_WRITE\\]',
        'LIST_FILES': r'\\[LIST_FILES\\](.*?)\\[/LIST_FILES\\]',
        'EXEC': r'\\[EXEC\\](.*?)\\[/EXEC\\]'
    }
    
    for tool_name, pattern in patterns.items():
        matches = re.findall(pattern, text, re.DOTALL)  # Added re.DOTALL to match across newlines
        if matches:
            return tool_name, matches
    
    return None, []


async def execute_tool(tool_name, tool_params):
    """Execute a tool with given parameters."""
    if tool_name == 'WEB_READ':
        import urllib.request
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text = []
                self.ignore_tags = {'script', 'style', 'head', 'title', 'meta', '[document]'}
        
            def handle_data(self, data):
                if self.current_tag not in self.ignore_tags:
                    content = data.strip()
                    if content:
                        self.text.append(content)
        
            def get_text(self):
                return '\\n'.join(self.text)
        
        try:
            url = tool_params[0]
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                html_content = response.read().decode('utf-8', errors='ignore')

                parser = TextExtractor()
                parser.feed(html_content)
                text_content = parser.get_text()
                
                # Limit content to prevent overload
                if len(text_content) > 10000:
                    text_content = text_content[:10000] + "\\n...[Content Truncated]"
                    
                return text_content
        except Exception as e:
            return f"Error fetching URL: {e}"
    
    elif tool_name == 'FILE_READ':
        try:
            filepath = tool_params[0]
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content) > 10000:
                    content = content[:10000] + "\\n...[Content Truncated]"
                return content
        except Exception as e:
            return f"Error reading file: {e}"
    
    elif tool_name == 'FILE_WRITE':
        try:
            param_str = tool_params[0]
            parts = param_str.split('|', 1)
            if len(parts) != 2:
                return "Error: FILE_WRITE requires 'filepath|content' format"
            
            filepath, content = parts
            filepath = filepath.strip()
            content = content.strip()
            
            # Ensure directory exists
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            return f"Error writing file: {e}"
    
    elif tool_name == 'LIST_FILES':
        try:
            directory = tool_params[0] if tool_params else "."
            if not os.path.exists(directory):
                return f"Directory does not exist: {directory}"
            
            if not os.path.isdir(directory):
                return f"Path is not a directory: {directory}"
            
            files = os.listdir(directory)
            if not files:
                return f"No files in directory: {directory}"
            
            return "\\n".join(files)
        except Exception as e:
            return f"Error listing files: {e}"
    
    elif tool_name == 'EXEC':
        try:
            command = tool_params[0]
            # Handle Windows-specific command execution
            full_command = command
            if os.name == 'nt' and not (command.lower().startswith('cmd') or command.lower().startswith('powershell')):
                full_command = f'cmd /c {command}'

            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # Increased timeout to 5 minutes

            output = stdout.decode().strip() if stdout else ""
            error = stderr.decode().strip() if stderr else ""

            result = ""
            if output:
                result += output
            if error:
                result += f"\\nERROR: {error}"

            if not result:
                result = "Command executed with no output."

            # Truncate if too long
            if len(result) > MAX_OUTPUT_LENGTH:
                result = result[:MAX_OUTPUT_LENGTH] + "\\n...[Output Truncated]"

            return result
        except asyncio.TimeoutError:
            return "Command execution timed out after 5 minutes."
        except Exception as e:
            return f"Command execution failed: {e}"
    
    return f"Unknown tool: {tool_name}"


async def call_qwen_with_tools(user_input: str, history: list) -> str:
    """Call the Qwen CLI with tools available."""
    # Format the conversation history for Qwen (only include recent exchanges)
    formatted_history = "\\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history[-4:]])  # Only last 4 exchanges
    
    # Enhanced system prompt with tool directives
    system_prompt = (
        "You are Qwen AI with general agent capabilities. You can use these tools when needed:\\n\\n"
        "1. [WEB_READ]URL[/WEB_READ] - Read and extract text from a webpage\\n"
        "2. [FILE_READ]filepath[/FILE_READ] - Read content from a file\\n"
        "3. [FILE_WRITE]filepath|content[/FILE_WRITE] - Write content to a file (format: filepath|content)\\n"
        "4. [LIST_FILES]directory[/LIST_FILES] - List files in a directory\\n"
        "5. [EXEC]command[/EXEC] - Execute a shell command\\n\\n"
        "USAGE NOTES:\\n"
        "- Use these tools when you need to perform actions\\n"
        "- [EXEC] can run any command including API calls with curl or Python scripts\\n"
        "- [FILE_WRITE] can save data, create scripts, or store information\\n"
        "- [WEB_READ] can fetch information from online sources\\n\\n"
        "EXAMPLES:\\n"
        "- To make an API call: [EXEC]curl -X GET https://api.example.com/data[/EXEC]\\n"
        "- To create a script: [FILE_WRITE]script.py|import requests\\nresponse = requests.get('https://api.example.com')[/FILE_WRITE]\\n"
        "- To run the script: [EXEC]python script.py[/EXEC]\\n\\n"
        "When you need to use a tool, respond with the appropriate tag format.\\n"
        "After receiving tool results, analyze them and respond to the user.\\n"
        "If you don't need tools, respond normally.\\n\\n"
    )
    
    # Create the full prompt
    full_prompt = f"{system_prompt}You are running in a secure environment where these tools are fully enabled.\\n\\nCONTEXT:\\n{formatted_history}\\n\\nUSER_INPUT: {user_input}\\n\\nASSISTANT:"
    
    try:
        # Start Qwen process with YOLO mode (-y) to auto-approve tools
        process = await asyncio.create_subprocess_shell(
            "qwen -y",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=full_prompt.encode()),
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


async def send_typing_indicator(context, chat_id):
    """Continuously send typing indicator until stopped."""
    try:
        while True:
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
            await asyncio.sleep(3)  # Send typing indicator every 3 seconds (well under the 5-second timeout)
    except asyncio.CancelledError:
        # When cancelled, send one final typing indicator to ensure it's visible
        try:
            await context.bot.send_chat_action(chat_id=chat_id, action=constants.ChatAction.TYPING)
        except:
            pass  # Ignore errors when cancelling
        raise  # Re-raise the cancellation


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and forward to Qwen with tool support."""
    user_message = update.message.text
    chat_id = update.effective_chat.id
    
    # Authorization check
    admin_id = os.environ.get('TELEGRAM_ADMIN_ID')
    if admin_id and str(chat_id) != admin_id:
        await update.message.reply_text("🔒 Access denied. You are not authorized to use this bot.")
        return

    logger.info(f"Processing message from user {update.effective_user.id}: {user_message}")

    # Start with a fresh history for each message (no persistent memory)
    history = []
    
    # Add user message to history
    history.append({"role": "user", "content": user_message})
    
    max_turns = 3  # Maximum number of tool calls per request
    current_input = user_message
    
    # Start continuous typing indicator
    typing_task = asyncio.create_task(send_typing_indicator(context, chat_id))

    try:
        for turn in range(max_turns):
            # Call Qwen with the current context
            qwen_response = await call_qwen_with_tools(current_input, history)
            
            # Check if Qwen wants to use a tool
            tool_name, tool_params = extract_tool_calls(qwen_response)
            
            if tool_name and turn < max_turns - 1:  # Process tool call if not the last turn
                # Execute the tool
                tool_result = await execute_tool(tool_name, tool_params)
                
                # Add tool call and result to history
                history.append({"role": "assistant", "content": qwen_response})
                history.append({"role": "tool_result", "content": tool_result})
                
                # Prepare for next iteration with tool result
                current_input = f"Tool result: {tool_result}"
            else:
                # No tool call or final turn, send response to user
                if not tool_name:
                    # No tool was called, send the response as-is
                    final_response = qwen_response
                else:
                    # This is the last turn, send whatever response we have
                    final_response = qwen_response
                
                # Send response back to user (split if too long)
                if len(final_response) <= MAX_MESSAGE_LENGTH:
                    await update.message.reply_text(final_response)
                else:
                    # Split long messages
                    for i in range(0, len(final_response), MAX_MESSAGE_LENGTH):
                        chunk = final_response[i:i+MAX_MESSAGE_LENGTH]
                        await update.message.reply_text(chunk)
                break
    finally:
        # Cancel the typing indicator task when done
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass  # Expected when cancelling the task


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    welcome_message = (
        "👋 Hello! I am Qwen AI with general agent capabilities.\n\n"
        "I can help you with:\n"
        "- Reading and writing files\n"
        "- Browsing the web\n"
        "- Executing shell commands\n"
        "- Making API calls\n"
        "- General conversation\n\n"
        "Just send me a message and I'll do my best to assist!"
    )
    await update.message.reply_text(welcome_message)


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

        logger.info("Simple Telegram-Qwen Bridge with General Agent Capabilities Bot Starting...")
        print("Bot is running. Press Ctrl+C to stop.")
        app.run_polling()

    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()