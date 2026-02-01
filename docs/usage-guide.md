# Usage Guide

Complete guide on how to use the Telegram-Qwen Bridge effectively.

## Basic Commands

### /start
- **Purpose**: Displays a welcome message and available commands
- **Usage**: Simply send `/start` to your bot
- **Response**: Shows available commands and basic usage instructions

### /id
- **Purpose**: Retrieves your Telegram chat ID
- **Usage**: Send `/id` to your bot
- **Response**: Returns your chat ID, useful for configuring `TELEGRAM_ADMIN_ID`

### /exec
- **Purpose**: Executes shell commands directly on the host computer
- **Usage**: `/exec <command>`
- **Example**: `/exec dir` (on Windows) or `/exec ls` (on Linux/macOS)
- **Response**: Returns the output of the executed command

### /reset
- **Purpose**: Clears the conversation history
- **Usage**: Send `/reset` to your bot
- **Response**: Confirms that memory has been wiped

## Interacting with Qwen

### Simple Queries
Send any text message to the bot to interact with Qwen. The bot will:
1. Pass your message to Qwen with conversation history
2. Receive Qwen's response
3. Forward the response back to you

### Agentic Tasks
Qwen can perform multi-step tasks by executing commands. Format your requests to encourage this behavior:

**Example Request**: "What files are in my home directory and what's the content of my README file?"

Qwen might respond with:
```
[EXEC]ls ~[/EXEC]
```

After receiving the output, it might follow up with:
```
[EXEC]cat ~/README.md[/EXEC]
```

## Available Tools

### Shell Commands
- **Format**: `[EXEC]command[/EXEC]`
- **Usage**: Qwen can execute any shell command
- **Examples**:
  - `[EXEC]ls -la[/EXEC]` (list files with details)
  - `[EXEC]pwd[/EXEC]` (show current directory)
  - `[EXEC]whoami[/EXEC]` (show current user)

### Web Reader
- **Format**: `[EXEC]python tools/web_reader.py <URL>[/EXEC]`
- **Usage**: Allows Qwen to read and extract text from web pages
- **Example**: `[EXEC]python tools/web_reader.py https://example.com[/EXEC]`
- **Note**: Qwen can only read content, not interact with websites

### Python Scripts
- **Format**: `[EXEC]python -c "python code here"[/EXEC]`
- **Usage**: Execute Python code snippets
- **Example**: `[EXEC]python -c "print('Hello from Python')"[/EXEC]`
- **Note**: Standard libraries and installed packages are available

## Advanced Usage Patterns

### File Operations
Ask Qwen to help with file management:
- "List all Python files in the current directory"
- "Show the content of config.json"
- "Find all files modified in the last 24 hours"

### System Information
Request system information:
- "What's the current disk usage?"
- "Show running processes"
- "What's the system uptime?"

### Automation Tasks
Chain multiple commands for automation:
- "Get the current date, create a backup folder with today's date, and copy config files there"
- "Download a file from URL X, verify its checksum, and move it to folder Y"

## Best Practices

### Security
- Never share your bot with untrusted users
- Regularly monitor the `audit.log` file
- Be cautious with commands that modify system settings
- Review all commands before allowing execution

### Efficiency
- Keep requests specific and clear
- Use the conversation history to your advantage
- Break complex tasks into smaller, manageable steps

### Error Handling
- If a command fails, Qwen will receive the error message and can adjust accordingly
- Long outputs are automatically truncated
- Commands that take too long will timeout

## Troubleshooting Common Issues

### Command Not Found
- Check if the command exists on the target system
- Verify the command syntax
- Consider platform differences (Windows vs Unix commands)

### Permission Denied
- Ensure the bot has necessary permissions to execute the command
- Run the bot with appropriate user privileges
- Check file/folder permissions

### Timeout Errors
- Simplify the command or break it into smaller parts
- Increase timeout values in the configuration if needed
- Check if the command is hanging or waiting for input

## Examples

### Example 1: File Exploration
**User**: "Show me the files in my home directory and their sizes"

**Qwen might respond with**:
```
[EXEC]ls -lh ~[/EXEC]
```

### Example 2: Web Research
**User**: "Find the latest news about artificial intelligence and summarize them"

**Qwen might respond with**:
```
[EXEC]python tools/web_reader.py https://example-news-site.com/ai-news[/EXEC]
```

### Example 3: System Monitoring
**User**: "Check the disk usage and memory usage"

**Qwen might respond with**:
```
[EXEC]df -h[/EXEC]
[EXEC]free -h[/EXEC]
```