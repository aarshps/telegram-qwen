@echo off
REM Setup script for Telegram-Qwen Bridge

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Creating .env file if it doesn't exist...
if not exist .env copy .env.example .env

echo.
echo Setup complete! 
echo Please edit the .env file to add your Telegram bot token and admin ID.
echo Then run the bot with: 
echo (CMD)        venv\Scripts\activate
echo (PowerShell) .\venv\Scripts\Activate.ps1
echo python telegram_qwen_bridge.py