"""
Tests for watchdog.py — Auto-restart wrapper.
"""

import time
import pytest
from unittest.mock import patch, MagicMock

from watchdog import (
    run_watchdog,
    main,
    RESTART_EXIT_CODE,
    MAX_RAPID_RESTARTS,
    RAPID_RESTART_WINDOW,
    COOLDOWN_WAIT,
    CRASH_WAIT,
    BOT_SCRIPT,
)


class TestWatchdogConstants:
    def test_restart_exit_code(self):
        assert RESTART_EXIT_CODE == 42

    def test_max_rapid_restarts(self):
        assert MAX_RAPID_RESTARTS >= 1

    def test_rapid_restart_window(self):
        assert RAPID_RESTART_WINDOW > 0

    def test_cooldown_wait(self):
        assert COOLDOWN_WAIT > 0

    def test_crash_wait(self):
        assert CRASH_WAIT > 0

    def test_bot_script_path(self):
        assert "telegram_qwen_bridge" in BOT_SCRIPT


class TestRunWatchdog:
    def test_clean_exit(self):
        """Bot exiting with code 0 should stop the watchdog."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            run_watchdog()  # Should return (not loop forever)

    def test_crash_restart(self):
        """Bot crashing should trigger restart after wait."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.returncode = 1  # Crash
            else:
                result.returncode = 0  # Clean exit on second run
            return result

        with patch("subprocess.run", side_effect=mock_run):
            with patch("time.sleep") as mock_sleep:
                run_watchdog()
                # Should have waited CRASH_WAIT seconds between crash and restart
                mock_sleep.assert_any_call(CRASH_WAIT)
                assert call_count == 2

    def test_intentional_restart(self):
        """Exit code 42 should trigger immediate restart."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.returncode = RESTART_EXIT_CODE  # Intentional restart
            else:
                result.returncode = 0  # Clean exit
            return result

        with patch("subprocess.run", side_effect=mock_run):
            with patch("time.sleep") as mock_sleep:
                run_watchdog()
                # Should have a brief 1s wait, not the crash wait
                mock_sleep.assert_any_call(1)
                assert call_count == 2

    def test_rapid_restart_cooldown(self):
        """Too many rapid restarts should trigger cooldown."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count <= MAX_RAPID_RESTARTS + 1:
                result.returncode = RESTART_EXIT_CODE
            else:
                result.returncode = 0
            return result

        sleep_calls = []

        def mock_sleep(seconds):
            sleep_calls.append(seconds)

        # Mock time.time to make all restarts appear within the window
        time_val = [1000.0]

        def mock_time():
            t = time_val[0]
            time_val[0] += 0.1  # Tiny increment = all within window
            return t

        with patch("subprocess.run", side_effect=mock_run):
            with patch("time.sleep", side_effect=mock_sleep):
                with patch("time.time", side_effect=mock_time):
                    run_watchdog()
                    # Should have triggered cooldown
                    assert COOLDOWN_WAIT in sleep_calls

    def test_keyboard_interrupt_stops(self):
        """Ctrl+C should stop the watchdog cleanly."""
        with patch("subprocess.run", side_effect=KeyboardInterrupt()):
            run_watchdog()  # Should return without error

    def test_subprocess_exception(self):
        """Exception while starting bot should be handled."""
        call_count = 0

        def mock_run(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("Process failed")
            result = MagicMock()
            result.returncode = 0
            return result

        with patch("subprocess.run", side_effect=mock_run):
            with patch("time.sleep"):
                run_watchdog()
                assert call_count == 2

    def test_main_runs_watchdog(self):
        """main() should call run_watchdog (L87-88)."""
        with patch("watchdog.run_watchdog") as mock_run:
            main()
            mock_run.assert_called_once()

    def test_main_catches_keyboard_interrupt(self):
        """main() should catch KeyboardInterrupt (L89-90)."""
        with patch("watchdog.run_watchdog", side_effect=KeyboardInterrupt()):
            # Should not raise
            main()

