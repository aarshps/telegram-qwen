# Telegram-Qwen Bridge

A Python bot that connects Telegram with the Qwen AI model, allowing you to interact with Qwen through Telegram messages. The bot includes agent capabilities for web browsing, file operations, and command execution.

## Features

- **Telegram Bot Integration**: Interact with Qwen AI via Telegram
- **Qwen AI Integration**: Leverage the power of Qwen for intelligent responses
- **Agent Capabilities**: Web browsing, file operations, and command execution
- **Fresh Sessions**: Clean slate on each restart, no persistent memory
- **Authorization**: Restrict access to authorized users only

## Prerequisites

- Python 3.8+
- Telegram Bot Token (get one from [@BotFather](https://t.me/BotFather))
- Qwen CLI installed and accessible from command line (install with `npm install -g @qwen-code/qwen-code`)
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

1. **Activate the virtual environment:**
   - **CMD:** `venv\Scripts\activate`
   - **PowerShell:** `.\venv\Scripts\Activate.ps1`
   - **Linux/macOS:** `source venv/bin/activate`

2. **Start the bot:**
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

The bot responds to all text messages by forwarding them to Qwen with agent capabilities.

## Security Considerations

- Only authorize trusted users by setting `TELEGRAM_ADMIN_ID`
- Be cautious with the commands you allow the bot to execute
- Monitor the audit logs regularly
- The bot stores chat history in `chat_history.json` - ensure this is secure
- Regularly update dependencies to address security vulnerabilities

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check that your bot token is correct and the bot is added to a chat
2. **Qwen not found**: Make sure Qwen CLI is installed and accessible from your PATH
3. **Tool execution fails**: Check that the requested file paths or URLs are accessible and properly formatted

### Logs

- No chat history is stored between sessions
- Application logs are printed to the console

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Getting Started](docs/getting-started.md) - Quick start guide
- [Installation Guide](docs/installation-guide.md) - Detailed setup instructions
- [Configuration](docs/configuration.md) - How to configure the bot
- [Usage Guide](docs/usage-guide.md) - Complete usage instructions
- [Security Considerations](docs/security.md) - Important security information
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Advanced Features](docs/advanced-features.md) - Advanced capabilities
- [FAQ](docs/faq.md) - Frequently asked questions
- [Contributing](docs/contributing.md) - How to contribute to the project

## Development

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

See the [Contributing Guide](docs/contributing.md) for detailed information on how to participate in the project.

### Project Structure

```
telegram-qwen/
├── telegram_qwen_bridge.py    # Main bot application
├── docs/                     # Documentation files
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .gitignore              # Git ignore rules
├── setup.bat                # Windows setup script
├── setup.sh                 # Unix setup script
└── README.md               # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

See the [Contributing Guide](docs/contributing.md) for detailed information on how to participate in the project.

## Disclaimer

This tool connects Telegram to Qwen AI with agent capabilities including file system access and command execution. Use responsibly and only grant access to trusted individuals. The authors are not responsible for any damage caused by misuse of this tool.