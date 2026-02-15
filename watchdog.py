"""
Watchdog — Auto-restart wrapper for the Telegram-Qwen Agent.
Handles intentional restarts (exit code 42) and crash recovery.

Usage:
    python watchdog.py
"""

import subprocess
import sys
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    format="%(asctime)s - WATCHDOG - %(levelname)s - %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("watchdog")

RESTART_EXIT_CODE = 42
MAX_RAPID_RESTARTS = 5
RAPID_RESTART_WINDOW = 60  # seconds
COOLDOWN_WAIT = 120  # seconds to wait after too many rapid restarts
CRASH_WAIT = 5  # seconds to wait after a crash before restarting

BOT_SCRIPT = str(Path(__file__).parent / "telegram_qwen_bridge.py")


def run_watchdog():
    """Run the bot in a loop with auto-restart logic."""
    restart_times: list[float] = []

    log.info("=" * 60)
    log.info("Watchdog starting")
    log.info(f"Bot script: {BOT_SCRIPT}")
    log.info(f"Python: {sys.executable}")
    log.info("=" * 60)

    while True:
        now = time.time()

        # Check for rapid restart loop
        restart_times = [t for t in restart_times if now - t < RAPID_RESTART_WINDOW]
        if len(restart_times) >= MAX_RAPID_RESTARTS:
            log.warning(
                f"Too many restarts ({MAX_RAPID_RESTARTS}) in {RAPID_RESTART_WINDOW}s. "
                f"Cooling down for {COOLDOWN_WAIT}s..."
            )
            time.sleep(COOLDOWN_WAIT)
            restart_times.clear()

        # Launch the bot
        log.info("Starting bot process...")
        try:
            result = subprocess.run(
                [sys.executable, BOT_SCRIPT],
                cwd=str(Path(BOT_SCRIPT).parent),
            )
            exit_code = result.returncode
        except KeyboardInterrupt:
            log.info("Watchdog stopped by user (Ctrl+C)")
            break
        except Exception as e:
            log.error(f"Failed to start bot: {e}")
            exit_code = 1

        # Handle exit
        if exit_code == 0:
            log.info("Bot exited cleanly (code 0). Shutting down watchdog.")
            break

        elif exit_code == RESTART_EXIT_CODE:
            log.info(f"Bot requested restart (code {RESTART_EXIT_CODE}). Restarting immediately...")
            restart_times.append(time.time())
            # Brief pause to allow file writes to complete
            time.sleep(1)

        else:
            log.warning(f"Bot crashed (exit code {exit_code}). Restarting in {CRASH_WAIT}s...")
            restart_times.append(time.time())
            time.sleep(CRASH_WAIT)


def main():
    """Entry point for the watchdog script."""
    try:
        run_watchdog()
    except KeyboardInterrupt:
        log.info("Watchdog stopped.")


if __name__ == "__main__":  # pragma: no cover
    main()
