# Testing

The project has a comprehensive test suite achieving **100% code coverage** across all modules.

## Running Tests

```bash
# Activate virtual environment
.\venv\Scripts\activate    # Windows
source venv/bin/activate   # Linux/macOS

# Run all tests with coverage
pytest

# Quick run (no coverage)
pytest --no-cov -q

# Run a specific test file
pytest tests/test_tools.py -q

# Run a specific test
pytest tests/test_tools.py::TestToolExec::test_echo -q

# Verbose output
pytest -v --tb=long
```

## Coverage Report

```
Name                 Stmts   Miss  Cover
─────────────────────────────────────────
bot\__init__.py          2      0   100%
bot\config.py           29      0   100%
bot\handlers.py        198      0   100%
bot\memory.py           82      0   100%
bot\qwen.py             47      0   100%
bot\task_engine.py     183      0   100%
bot\tools.py           211      0   100%
watchdog.py             52      0   100%
─────────────────────────────────────────
TOTAL                  804      0   100%
```

An HTML coverage report is generated at `htmlcov/index.html` after each run.

## Test Files

| File | Module | Tests |
|------|--------|-------|
| `test_config.py` | `bot/config.py` | Environment loading, defaults, directory creation |
| `test_memory.py` | `bot/memory.py` | CRUD operations, persistence, trimming, edge cases |
| `test_qwen.py` | `bot/qwen.py` | Success, retries, timeouts, backoff, error handling |
| `test_tools.py` | `bot/tools.py` | Each tool's success, error, and edge-case paths |
| `test_task_engine.py` | `bot/task_engine.py` | Task lifecycle, checkpoints, resume, corruption |
| `test_handlers.py` | `bot/handlers.py` | Auth, rate limiting, all commands, message handling |
| `test_watchdog.py` | `watchdog.py` | Restart logic, crash recovery, cooldown, main() |

## Test Configuration

Tests are configured in `pytest.ini`:

```ini
[pytest]
testpaths = tests
asyncio_mode = auto

filterwarnings =
    error
    ignore::coverage.exceptions.CoverageWarning
    ignore::ResourceWarning
    ignore:coroutine.*was never awaited:RuntimeWarning

addopts = --cov=bot --cov=watchdog --cov-report=html --cov-report=term-missing
```

Key points:
- **`asyncio_mode = auto`** — All async tests run automatically without `@pytest.mark.asyncio`
- **`filterwarnings = error`** — Treats warnings as errors by default, with targeted ignores
- **Coverage** — Automatically measures `bot/` and `watchdog.py` coverage

## Fixtures

Common fixtures are in `tests/conftest.py`:

- **`temp_data_dirs`** — Creates temporary `data/tasks/` and `data/conversations/` directories, cleaned up after each test
- **`make_update()`** — Creates mock Telegram `Update` objects
- **`make_context()`** — Creates mock Telegram `CallbackContext` objects

## Writing New Tests

1. Add your test to the appropriate `test_*.py` file
2. Use `temp_data_dirs` fixture for tests that touch the filesystem
3. Use `unittest.mock.patch` for external dependencies (Qwen CLI, httpx, etc.)
4. Follow the existing pattern: one test class per module/feature, one method per behavior
5. Run `pytest` and verify coverage stays at 100%
