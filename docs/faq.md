# Frequently Asked Questions (FAQ)

Answers to common questions about the Telegram-Qwen Bridge.

## General Questions

### What is the Telegram-Qwen Bridge?

The Telegram-Qwen Bridge is a Python application that connects Telegram messaging with the Qwen AI model, allowing you to control your computer through Telegram messages. It enables you to execute commands, perform agentic tasks, and interact with your system remotely.

### How does it work?

The bridge works by:
1. Receiving messages from your Telegram bot
2. Checking if the sender is authorized
3. Passing your request to the Qwen AI with conversation history
4. If Qwen responds with executable commands, running them on your system
5. Sending the results back to your Telegram chat

### Is it secure?

Security is a primary concern. The bridge includes:
- Authorization system that restricts access to a specific user
- Environment variables for sensitive configuration
- Audit logging of all activities
However, since it executes commands on your system, follow the security best practices outlined in the documentation.

## Installation Questions

### What are the system requirements?

- Python 3.8 or higher
- A Telegram account to create a bot
- Qwen CLI installed (`pip install qwen-cli`)
- Windows, macOS, or Linux operating system
- Internet connection

### Do I need to install Qwen separately?

Yes, you need to install the Qwen CLI separately using:
```bash
pip install qwen-cli
```

### Why isn't my bot responding?

Common causes:
1. Invalid bot token in `.env` file
2. Network connectivity issues
3. Incorrect `TELEGRAM_ADMIN_ID`
4. Missing dependencies

Check the console for error messages and verify your configuration.

## Usage Questions

### How do I get my Telegram chat ID?

Send the `/id` command to your running bot, or use the `/id` command in your bot's chat.

### Can multiple people use the bot?

By default, only the user with the chat ID specified in `TELEGRAM_ADMIN_ID` can use the bot. You can modify the code to support multiple administrators if needed.

### What commands can I run?

You can run any command that the user running the bot has permissions to execute. The bot supports all shell commands available on your system.

### How does the [EXEC] syntax work?

When Qwen responds with `[EXEC]command[/EXEC]`, the bridge executes that command on your system and returns the output. This allows Qwen to perform multi-step tasks.

### Can I run Python scripts?

Yes, you can run Python scripts using:
```
[EXEC]python -c "your python code here"[/EXEC]
```

## Security Questions

### How is access controlled?

Access is controlled through the `TELEGRAM_ADMIN_ID` environment variable. Only users with the matching chat ID can interact with the bot.

### What commands are safe to run?

Be cautious with commands that:
- Modify system settings
- Delete files
- Install software
- Access sensitive data
Always review commands before allowing execution.

### Can the bot access my personal files?

The bot can access any files that the user running it has permissions to access. Run the bot under a user account with limited privileges to minimize risk.

## Technical Questions

### Why does the bot timeout on some commands?

Commands that take longer than `COMMAND_TIMEOUT` (default 60 seconds) will timeout. You can increase this value in the code if needed.

### How is conversation history managed?

Conversation history is stored in `chat_history.json` and maintained in memory during runtime. The `/reset` command clears the history.

### Can I modify the system prompt?

Yes, you can modify the system prompt in the `handle_message` function to change how Qwen behaves.

### What happens to my data?

- Conversation history is stored locally in `chat_history.json`
- Audit logs are stored in `audit.log`
- No data is sent to external servers except Telegram API and Qwen service

## Troubleshooting Questions

### The bot says "Access denied" even though I'm the admin

Verify that:
1. Your `TELEGRAM_ADMIN_ID` is correct
2. The value in your `.env` file matches your actual chat ID
3. You've restarted the bot after updating the environment file

### Commands are failing with "command not found"

This usually happens on Windows. The bot automatically prefixes commands with `cmd /c`, but you might need to:
- Use full paths to executables
- Check that the command exists in your PATH
- Verify the command syntax

### How do I debug issues?

Enable debug logging by changing the logging level in the code, and check:
- Console output for error messages
- `audit.log` for activity records
- System logs for related errors

### The bot stops responding suddenly

Possible causes:
- Network connectivity issues
- Process killed due to resource constraints
- Unhandled exception in the code
Check the console for error messages when this happens.

## Advanced Questions

### Can I extend the bot's functionality?

Yes, you can add new commands by creating handler functions and registering them with the application. You can also add new tools for Qwen to use.

### How do I backup my data?

Backup the following files:
- `chat_history.json` - Conversation history
- `.env` - Configuration (keep this secure!)
- Any custom scripts or modifications you've made

### Can I run this in a container?

Yes, the application can run in Docker containers. See the installation guide for Docker instructions.

### How do I update the bot?

1. Pull the latest changes from the repository
2. Update dependencies if needed: `pip install -r requirements.txt`
3. Restart the bot

## Support Questions

### Where can I get help?

- Check the documentation in the `docs/` directory
- Look for similar issues in the GitHub repository
- Review the troubleshooting guide
- Examine the audit logs for clues

### How do I report bugs?

Include the following information:
- Operating system and Python version
- Error messages from the console
- Steps to reproduce the issue
- Your configuration (without sensitive data)
- Recent changes made to the code or configuration

### Can I contribute to the project?

Yes! Contributions are welcome. Please follow the contribution guidelines in the repository.