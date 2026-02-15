# Contributing

How to contribute to the Telegram-Qwen agent.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/telegram-qwen.git
   cd telegram-qwen
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate    # or .\venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

1. **Make your changes** — Follow the existing code patterns
2. **Add tests** — Maintain 100% coverage
3. **Run the test suite:**
   ```bash
   pytest
   ```
4. **Verify coverage** — Check `htmlcov/index.html` for any gaps
5. **Commit and push:**
   ```bash
   git add -A
   git commit -m "Add: description of your change"
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request** on GitHub

## Code Style

- Follow PEP 8 conventions
- Use type hints where practical
- Use `async/await` for all I/O operations
- Return structured dicts from tool functions: `{"status": "success"|"error", "output": "..."}`
- Log important operations with Python's `logging` module

## Project Structure

```
telegram-qwen/
├── bot/                    # Core package
│   ├── __init__.py
│   ├── config.py           # Configuration
│   ├── memory.py           # Conversation memory
│   ├── qwen.py             # Qwen CLI integration
│   ├── tools.py            # Tool implementations
│   ├── task_engine.py      # Task state machine
│   └── handlers.py         # Telegram handlers
├── tests/                  # Test suite (100% coverage)
│   ├── conftest.py         # Shared fixtures
│   ├── test_config.py
│   ├── test_memory.py
│   ├── test_qwen.py
│   ├── test_tools.py
│   ├── test_task_engine.py
│   ├── test_handlers.py
│   └── test_watchdog.py
├── docs/                   # Documentation
├── watchdog.py             # Auto-restart wrapper
├── telegram_qwen_bridge.py # Entry point
├── pytest.ini              # Test configuration
└── requirements.txt        # Dependencies
```

## Adding a New Tool

1. Add the function to `bot/tools.py`:
   ```python
   async def tool_your_tool(param: str) -> dict:
       try:
           # Implementation
           return _result("success", "output here")
       except Exception as e:
           return _result("error", str(e))
   ```
2. Add its description to `TOOL_DESCRIPTIONS`
3. Add dispatch logic in `task_engine.py`
4. Add comprehensive tests in `tests/test_tools.py`

## Adding a New Command

1. Add the handler to `bot/handlers.py`:
   ```python
   async def cmd_yourcommand(update, context):
       await _send_safe(update, "Response here")
   ```
2. Register in `telegram_qwen_bridge.py`:
   ```python
   app.add_handler(CommandHandler("yourcommand", cmd_yourcommand))
   ```
3. Add tests in `tests/test_handlers.py`