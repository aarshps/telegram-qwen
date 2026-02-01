# Telegram-Qwen Bridge

A Python bot that connects Telegram with the Qwen AI model, allowing you to interact with your computer through Telegram messages. The bot can execute commands, perform agentic tasks, and maintain conversation history.

## Features

- **Telegram Bot Integration**: Control your computer remotely via Telegram
- **Qwen AI Integration**: Leverage the power of Qwen for intelligent command execution
- **Command Execution**: Run shell commands securely with authorization
- **Agentic Capabilities**: Qwen can perform multi-step tasks autonomously
- **Web Reading**: Built-in web reader tool for research
- **Chat History**: Persistent conversation history
- **Audit Logging**: Track all bot activities

## Prerequisites

- Python 3.8+
- Telegram Bot Token (get one from [@BotFather](https://t.me/BotFather))
- Qwen CLI installed and accessible from command line (install with `pip install qwen`)
- Windows, macOS, or Linux system

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/telegram-qwen.git
   cd telegram-qwen
   ```

2. **Run the setup script:**
   - On Windows:
     ```bash
     setup.bat
     ```
   - On macOS/Linux:
     ```bash
     chmod +x setup.sh
     ./setup.sh
     ```

3. **Configure your environment:**
   Edit the `.env` file and add your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
   TELEGRAM_ADMIN_ID=your_telegram_chat_id
   ```

   To get your Telegram Chat ID:
   - Start the bot and send `/id` command
   - Or use any Telegram bot that provides chat ID information

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from [@BotFather](https://t.me/BotFather)
- `TELEGRAM_ADMIN_ID`: Your Telegram chat ID (to restrict bot access to authorized users only)

### Security Notes

⚠️ **Important**: This bot executes commands on your computer. Only grant access to trusted users by setting the `TELEGRAM_ADMIN_ID` environment variable.

## Usage

1. **Start the bot:**
   ```bash
   python telegram_qwen_bridge.py
   ```

2. **Interact with the bot:**
   - Send `/start` to get started
   - Send `/id` to get your chat ID
   - Send `/exec <command>` to execute shell commands
   - Send `/reset` to clear chat history
   - Simply send messages to interact with Qwen AI

### Available Commands

- `/start` - Display welcome message and usage instructions
- `/id` - Get your Telegram chat ID
- `/exec <command>` - Execute a shell command on the host computer
- `/reset` - Clear the chat history and reset memory

### Agentic Capabilities

The bot supports agentic behavior where Qwen can:
- Execute shell commands using `[EXEC]command[/EXEC]` format
- Read web pages using the web reader tool
- Perform multi-step tasks autonomously
- Maintain context across conversations

Example of agentic behavior:
```
Can you list the files in my home directory and then show me the content of a specific file?
```

Qwen might respond with:
```
[EXEC]ls ~[/EXEC]
```

After receiving the output, it might follow up with:
```
[EXEC]cat ~/specific_file.txt[/EXEC]
```

## Tools Available to Qwen

The bot provides these tools to Qwen:

1. **Shell Commands**: `[EXEC]command[/EXEC]` - Execute any shell command
2. **Web Reader**: `[EXEC]python tools/web_reader.py <URL>[/EXEC]` - Read and extract text from web pages
3. **Python Scripts**: `[EXEC]python -c "..."[/EXEC]` - Run Python code snippets

## Web Reader Tool

The web reader tool (`tools/web_reader.py`) allows Qwen to read and extract text content from web pages. It handles:
- HTML parsing and text extraction
- Common HTML tags filtering (scripts, styles, etc.)
- UTF-8 encoding handling
- Content length limiting to prevent overload

Usage within Qwen prompts:
```
[EXEC]python tools/web_reader.py https://example.com[/EXEC]
```

## Security Considerations

- Only authorize trusted users by setting `TELEGRAM_ADMIN_ID`
- Be cautious with the commands you allow the bot to execute
- Monitor the audit logs regularly
- The bot stores chat history in `chat_history.json` - ensure this is secure
- Regularly update dependencies to address security vulnerabilities

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check that your bot token is correct and the bot is added to a chat
2. **Command execution fails**: Ensure the commands are valid for your operating system
3. **Qwen not found**: Make sure Qwen CLI is installed and accessible from your PATH
4. **Permission errors**: Check that the bot has necessary permissions to execute commands

### Logs

- Chat history is stored in `chat_history.json`
- Audit logs are stored in `audit.log`
- Application logs are printed to the console

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Project Structure

```
telegram-qwen/
├── telegram_qwen_bridge.py    # Main bot application
├── tools/
│   └── web_reader.py         # Web content extraction tool
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Disclaimer

This tool executes commands on your computer. Use responsibly and only grant access to trusted individuals. The authors are not responsible for any damage caused by misuse of this tool.