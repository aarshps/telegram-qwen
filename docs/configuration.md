# Configuration

Learn how to configure the Telegram-Qwen Bridge for your specific needs.

## Environment Variables

The application uses environment variables stored in a `.env` file. Copy `.env.example` to create your own `.env` file:

```bash
cp .env.example .env
```

### Required Variables

#### TELEGRAM_BOT_TOKEN
- **Purpose**: The authentication token for your Telegram bot
- **How to obtain**: Get it from [@BotFather](https://t.me/BotFather) on Telegram
- **Format**: A string like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`

#### TELEGRAM_ADMIN_ID
- **Purpose**: Restricts bot access to authorized users only
- **How to obtain**: Send `/id` command to your running bot, or use other methods to get your Telegram chat ID
- **Format**: A numeric string like `123456789`

### Optional Variables

The application doesn't currently use additional environment variables, but you could extend it to include:

- `LOG_LEVEL`: Set to DEBUG, INFO, WARNING, or ERROR (defaults to INFO)
- `COMMAND_TIMEOUT`: Maximum time (in seconds) for command execution (defaults to 60)
- `QWEN_TIMEOUT`: Maximum time (in seconds) for Qwen responses (defaults to 120)

## Code Configuration

Several constants can be adjusted in the main script (`telegram_qwen_bridge.py`):

### Timeout Settings
- `COMMAND_TIMEOUT`: Time limit for command execution (default: 60 seconds)
- `QWEN_TIMEOUT`: Time limit for Qwen responses (default: 120 seconds)

### Message Limits
- `MAX_MESSAGE_LENGTH`: Maximum length of messages sent to Telegram (default: 4096 characters)
- `MAX_OUTPUT_LENGTH`: Maximum length of command output stored (default: 8000 characters)
- `MAX_HISTORY_MESSAGES`: Number of messages kept in conversation history (default: 20)

### Loop Settings
- `MAX_TURN_COUNT`: Maximum number of turns in the ReAct loop (default: 10)

## Security Configuration

### Authorization
The bot implements a simple authorization mechanism:
- Only users whose chat ID matches `TELEGRAM_ADMIN_ID` can interact with the bot
- Unauthorized users receive a "🔒 Access denied" message

### Command Execution
- The bot executes commands with the privileges of the user running it
- Be cautious about which commands the bot can execute
- Consider using a limited user account to run the bot

## File Locations

### Persistent Data
- `chat_history.json`: Stores conversation history between sessions
- `audit.log`: Records all bot activities for security review

### Configuration Files
- `.env`: Contains sensitive configuration values
- `requirements.txt`: Lists Python dependencies

## Customization Options

### Modifying the System Prompt
The system prompt that guides Qwen's behavior is located in the `handle_message` function. You can customize it to:

- Change the tools available to Qwen
- Modify the output format expectations
- Adjust the behavior for specific use cases

### Adding New Commands
You can extend the bot by adding new command handlers in the `main()` function:

```python
app.add_handler(CommandHandler("newcommand", new_command_function))
```

### Changing the Web Reader Tool
The web reader tool in `tools/web_reader.py` can be customized to:
- Change content extraction rules
- Add support for different encodings
- Modify the maximum content length processed