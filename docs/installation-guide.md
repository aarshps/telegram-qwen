# Installation Guide

Detailed steps to install and set up the Telegram-Qwen Bridge on different platforms.

## System Requirements

- Operating System: Windows, macOS, or Linux
- Python: Version 3.8 or higher
- RAM: At least 1GB free
- Storage: At least 50MB free space
- Internet connection

## Installing Python Dependencies

The project uses several Python packages. Install them using pip:

```bash
pip install -r requirements.txt
```

Or install individually:

```bash
pip install python-telegram-bot python-dotenv qwen-cli
```

## Setting Up Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather and use the `/newbot` command
3. Follow the prompts to name your bot and get a bot token
4. Save the bot token in your `.env` file as `TELEGRAM_BOT_TOKEN`

## Installing Qwen CLI

The bridge requires the Qwen CLI tool. Install it with pip:

```bash
pip install qwen-cli
```

Verify the installation by running:

```bash
qwen --help
```

## Platform-Specific Instructions

### Windows

1. Download and install Python from [python.org](https://www.python.org/downloads/)
2. Verify installation: `python --version`
3. Clone the repository: `git clone https://github.com/aarshps/telegram-qwen.git`
4. Navigate to the directory: `cd telegram-qwen`
5. Run setup: `setup.bat`
6. Configure `.env` file with your credentials
7. Start the bot: `python telegram_qwen_bridge.py`

### macOS

1. Install Python using Homebrew:
   ```bash
   brew install python
   ```
2. Clone the repository:
   ```bash
   git clone https://github.com/aarshps/telegram-qwen.git
   ```
3. Navigate to the directory:
   ```bash
   cd telegram-qwen
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install qwen-cli
   ```
5. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
6. Edit `.env` with your credentials
7. Start the bot:
   ```bash
   python telegram_qwen_bridge.py
   ```

### Linux (Ubuntu/Debian)

1. Install Python:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip
   ```
2. Clone the repository:
   ```bash
   git clone https://github.com/aarshps/telegram-qwen.git
   ```
3. Navigate to the directory:
   ```bash
   cd telegram-qwen
   ```
4. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   pip3 install qwen-cli
   ```
5. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
6. Edit `.env` with your credentials
7. Start the bot:
   ```bash
   python3 telegram_qwen_bridge.py
   ```

## Docker Installation (Alternative)

If you prefer using Docker, you can build and run the bot in a container:

1. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   RUN pip install qwen-cli
   
   COPY . .
   
   CMD ["python", "telegram_qwen_bridge.py"]
   ```

2. Build the image:
   ```bash
   docker build -t telegram-qwen-bridge .
   ```

3. Run the container:
   ```bash
   docker run -it --env-file .env telegram-qwen-bridge
   ```

## Verification

After installation, verify everything works:

1. Ensure the bot starts without errors
2. Send `/start` to your bot on Telegram
3. Verify you receive the welcome message
4. Test the `/id` command to confirm bot functionality