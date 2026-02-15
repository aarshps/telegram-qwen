"""
Tests for bot.tools — All 9 tools, extract_tool_calls, execute_tool dispatcher.
"""

import asyncio
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from bot.tools import (
    _result,
    _truncate,
    tool_web_search,
    tool_web_read,
    tool_file_read,
    tool_file_write,
    tool_list_files,
    tool_exec,
    tool_python,
    tool_self_modify,
    tool_self_restart,
    extract_tool_calls,
    execute_tool,
    TOOL_DESCRIPTIONS,
)
from bot.config import Config


# ── Helper Functions ─────────────────────────────────────────────────────────

class TestResult:
    def test_result_structure(self):
        r = _result("success", "hello", False)
        assert r["status"] == "success"
        assert r["output"] == "hello"
        assert r["truncated"] is False

    def test_result_truncated(self):
        r = _result("error", "err", True)
        assert r["truncated"] is True


class TestTruncate:
    def test_short_text(self):
        text, truncated = _truncate("hello", 100)
        assert text == "hello"
        assert truncated is False

    def test_exact_limit(self):
        text, truncated = _truncate("abc", 3)
        assert text == "abc"
        assert truncated is False

    def test_over_limit(self):
        text, truncated = _truncate("abcdef", 3)
        assert truncated is True
        assert "[Output Truncated]" in text

    def test_default_max_len(self):
        text, truncated = _truncate("x" * 5000)
        assert truncated is True


# ── Tool: WEB_SEARCH ────────────────────────────────────────────────────────

class TestToolWebSearch:
    @pytest.mark.asyncio
    async def test_success(self):
        """Should return formatted search results."""
        mock_results = [
            {"title": "Bitcoin Price", "href": "https://example.com", "body": "$50,000"},
        ]
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = mock_results

        with patch("bot.tools.DDGS", return_value=mock_ddgs) if hasattr(__import__('bot.tools', fromlist=['DDGS']), 'DDGS') else patch.dict("sys.modules", {}):
            # Directly mock the internal function
            pass

        # Simpler approach: patch the entire function's internals
        with patch("bot.tools.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value="1. **Bitcoin Price**\n   https://example.com\n   $50,000\n")
            result = await tool_web_search("bitcoin price")
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_exception(self):
        """Should handle exceptions gracefully."""
        with patch("bot.tools.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(side_effect=Exception("Search failed"))
            result = await tool_web_search("fail query")
            assert result["status"] == "error"
            assert "failed" in result["output"].lower()

    @pytest.mark.asyncio
    async def test_search_with_results(self):
        """Should format DuckDuckGo results into structured output (covers L47-57)."""
        mock_results = [
            {"title": "Result 1", "href": "https://example.com", "body": "Body 1"},
            {"title": "Result 2", "href": "https://test.com", "body": "Body 2"},
        ]
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = mock_results

        with patch.dict("sys.modules", {"duckduckgo_search": MagicMock(DDGS=MagicMock(return_value=mock_ddgs))}):
            # Need to call the inner _search synchronously via run_in_executor
            # Instead, mock run_in_executor to call the function inline
            async def run_inline(executor, fn):
                return fn()

            with patch("bot.tools.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = run_inline
                result = await tool_web_search("test query")
                assert result["status"] == "success"
                assert "Result 1" in result["output"]
                assert "Result 2" in result["output"]

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Should return 'No results found' when empty (covers L49-50)."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = MagicMock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = MagicMock(return_value=False)
        mock_ddgs.text.return_value = []

        with patch.dict("sys.modules", {"duckduckgo_search": MagicMock(DDGS=MagicMock(return_value=mock_ddgs))}):
            async def run_inline(executor, fn):
                return fn()

            with patch("bot.tools.asyncio.get_event_loop") as mock_loop:
                mock_loop.return_value.run_in_executor = run_inline
                result = await tool_web_search("empty query")
                assert result["status"] == "success"
                assert "No results" in result["output"]


# ── Tool: WEB_READ ──────────────────────────────────────────────────────────

class TestToolWebRead:
    @pytest.mark.asyncio
    async def test_success(self):
        """Should fetch and parse HTML content (covers L88 with nav/footer)."""
        mock_response = MagicMock()
        mock_response.text = "<html><body><nav>Menu</nav><p>Hello World</p><footer>Footer</footer></body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        # httpx is imported inside tool_web_read, so we patch it as a module-level import
        import httpx as httpx_mod
        mock_httpx = MagicMock(wraps=httpx_mod)
        mock_httpx.AsyncClient = MagicMock(return_value=mock_client)
        with patch.dict("sys.modules", {"httpx": mock_httpx}):
            result = await tool_web_read("https://example.com")
            assert result["status"] == "success"
            assert "Hello World" in result["output"]
            assert "Menu" not in result["output"]
            assert "Footer" not in result["output"]

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Should handle connection errors gracefully."""
        result = await tool_web_read("http://nonexistent.invalid.test")
        assert result["status"] == "error"
        assert "Failed to fetch URL" in result["output"]


# ── Tool: FILE_READ ─────────────────────────────────────────────────────────

class TestToolFileRead:
    @pytest.mark.asyncio
    async def test_read_existing_file(self, temp_data_dirs):
        test_file = temp_data_dirs / "test.txt"
        test_file.write_text("Hello World", encoding="utf-8")
        result = await tool_file_read(str(test_file))
        assert result["status"] == "success"
        assert "Hello World" in result["output"]

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        result = await tool_file_read("/nonexistent/path/file.txt")
        assert result["status"] == "error"
        assert "File not found" in result["output"]

    @pytest.mark.asyncio
    async def test_read_directory(self, temp_data_dirs):
        result = await tool_file_read(str(temp_data_dirs))
        assert result["status"] == "error"
        assert "Not a file" in result["output"]

    @pytest.mark.asyncio
    async def test_read_large_file_truncated(self, temp_data_dirs):
        test_file = temp_data_dirs / "large.txt"
        test_file.write_text("x" * 20000, encoding="utf-8")
        result = await tool_file_read(str(test_file))
        assert result["truncated"] is True

    @pytest.mark.asyncio
    async def test_read_permission_error(self, temp_data_dirs):
        """Should handle file read errors gracefully (covers L113-115)."""
        # File must exist to pass the exists() check
        test_file = temp_data_dirs / "exists_but_unreadable.txt"
        test_file.write_text("data", encoding="utf-8")
        with patch("pathlib.Path.read_text", side_effect=PermissionError("access denied")):
            result = await tool_file_read(str(test_file))
            assert result["status"] == "error"
            assert "Failed to read file" in result["output"]


# ── Tool: FILE_WRITE ────────────────────────────────────────────────────────

class TestToolFileWrite:
    @pytest.mark.asyncio
    async def test_write_new_file(self, temp_data_dirs):
        target = temp_data_dirs / "output.txt"
        result = await tool_file_write(str(target), "test content")
        assert result["status"] == "success"
        assert target.read_text(encoding="utf-8") == "test content"

    @pytest.mark.asyncio
    async def test_write_creates_directories(self, temp_data_dirs):
        target = temp_data_dirs / "sub" / "dir" / "file.txt"
        result = await tool_file_write(str(target), "nested")
        assert result["status"] == "success"
        assert target.exists()

    @pytest.mark.asyncio
    async def test_write_overwrite(self, temp_data_dirs):
        target = temp_data_dirs / "overwrite.txt"
        target.write_text("old", encoding="utf-8")
        result = await tool_file_write(str(target), "new")
        assert result["status"] == "success"
        assert target.read_text(encoding="utf-8") == "new"

    @pytest.mark.asyncio
    async def test_write_permission_error(self, temp_data_dirs):
        """Should handle write errors gracefully."""
        with patch("pathlib.Path.write_text", side_effect=PermissionError("permission denied")):
            result = await tool_file_write(str(temp_data_dirs / "no_access.txt"), "data")
            assert result["status"] == "error"
            assert "Failed to write file" in result["output"]


# ── Tool: LIST_FILES ────────────────────────────────────────────────────────

class TestToolListFiles:
    @pytest.mark.asyncio
    async def test_list_directory(self, temp_data_dirs):
        (temp_data_dirs / "file1.txt").write_text("a", encoding="utf-8")
        (temp_data_dirs / "file2.txt").write_text("b", encoding="utf-8")
        result = await tool_list_files(str(temp_data_dirs))
        assert result["status"] == "success"
        assert "file1.txt" in result["output"]
        assert "file2.txt" in result["output"]

    @pytest.mark.asyncio
    async def test_list_nonexistent(self):
        result = await tool_list_files("/nonexistent/path")
        assert result["status"] == "error"
        assert "Directory not found" in result["output"]

    @pytest.mark.asyncio
    async def test_list_file_not_dir(self, temp_data_dirs):
        f = temp_data_dirs / "afile.txt"
        f.write_text("x", encoding="utf-8")
        result = await tool_list_files(str(f))
        assert result["status"] == "error"
        assert "Not a directory" in result["output"]

    @pytest.mark.asyncio
    async def test_list_empty_directory(self, temp_data_dirs):
        empty = temp_data_dirs / "empty_dir"
        empty.mkdir()
        result = await tool_list_files(str(empty))
        assert result["status"] == "success"
        assert "Empty directory" in result["output"]

    @pytest.mark.asyncio
    async def test_list_shows_small_file_sizes(self, temp_data_dirs):
        """Small files should show bytes."""
        (temp_data_dirs / "small.txt").write_text("x", encoding="utf-8")
        result = await tool_list_files(str(temp_data_dirs))
        assert result["status"] == "success"
        assert "📄" in result["output"]

    @pytest.mark.asyncio
    async def test_list_shows_kb_sizes(self, temp_data_dirs):
        """Files > 1KB should show KB."""
        (temp_data_dirs / "medium.txt").write_text("x" * 2048, encoding="utf-8")
        result = await tool_list_files(str(temp_data_dirs))
        assert result["status"] == "success"
        assert "KB" in result["output"]

    @pytest.mark.asyncio
    async def test_list_shows_mb_sizes(self, temp_data_dirs):
        """Files > 1MB should show MB."""
        (temp_data_dirs / "big.bin").write_bytes(b"x" * (1024 * 1024 + 1))
        result = await tool_list_files(str(temp_data_dirs))
        assert result["status"] == "success"
        assert "MB" in result["output"]

    @pytest.mark.asyncio
    async def test_list_shows_dirs(self, temp_data_dirs):
        (temp_data_dirs / "subdir").mkdir()
        result = await tool_list_files(str(temp_data_dirs))
        assert result["status"] == "success"
        assert "📁" in result["output"]

    @pytest.mark.asyncio
    async def test_list_permission_error(self, temp_data_dirs):
        """Should handle permission errors."""
        with patch("pathlib.Path.iterdir", side_effect=PermissionError("no access")):
            result = await tool_list_files(str(temp_data_dirs))
            assert result["status"] == "error"
            assert "Failed to list directory" in result["output"]


# ── Tool: EXEC ──────────────────────────────────────────────────────────────

class TestToolExec:
    @pytest.mark.asyncio
    async def test_successful_command(self):
        result = await tool_exec("echo hello")
        assert result["status"] == "success"
        assert "hello" in result["output"]

    @pytest.mark.asyncio
    async def test_failing_command(self):
        result = await tool_exec("cmd /c exit 1")
        assert result["status"] == "error"
        assert "Exit code:" in result["output"]

    @pytest.mark.asyncio
    async def test_timeout(self, monkeypatch):
        import bot.tools
        monkeypatch.setattr(bot.tools, "TOOL_TIMEOUT", 1)
        result = await tool_exec("ping -n 10 127.0.0.1")
        assert result["status"] == "error"
        assert "timed out" in result["output"]

    @pytest.mark.asyncio
    async def test_exec_general_exception(self):
        """Should handle unexpected exceptions."""
        with patch("asyncio.create_subprocess_shell", side_effect=OSError("cannot execute")):
            result = await tool_exec("any command")
            assert result["status"] == "error"
            assert "Command execution failed" in result["output"]

    @pytest.mark.asyncio
    async def test_cmd_prefixed_commands(self):
        """Commands starting with cmd/powershell should not be double-wrapped."""
        result = await tool_exec("cmd /c echo direct")
        assert result["status"] == "success"
        assert "direct" in result["output"]

    @pytest.mark.asyncio
    async def test_exec_unix(self):
        """Should cover the Unix path in tool_exec (L181)."""
        with patch("os.name", "posix"):
            with patch("asyncio.create_subprocess_shell") as mock_create:
                mock_proc = AsyncMock()
                mock_proc.communicate.return_value = (b"unix ok", b"")
                mock_proc.returncode = 0
                mock_create.return_value = mock_proc
                result = await tool_exec("ls -la")
                assert result["status"] == "success"
                assert "unix ok" in result["output"]
                # Verify it didn't use cmd /c
                mock_create.assert_called_with("ls -la", stdout=-1, stderr=-1)


# ── Tool: PYTHON ─────────────────────────────────────────────────────────────

class TestToolPython:
    @pytest.mark.asyncio
    async def test_simple_code(self, temp_data_dirs):
        result = await tool_python("print('hello from python')")
        assert result["status"] == "success"
        assert "hello from python" in result["output"]

    @pytest.mark.asyncio
    async def test_error_code(self, temp_data_dirs):
        result = await tool_python("raise ValueError('test error')")
        assert result["status"] == "error"
        assert "test error" in result["output"]

    @pytest.mark.asyncio
    async def test_cleanup_temp_file(self, temp_data_dirs):
        """Script file should be cleaned up after execution."""
        result = await tool_python("print('cleanup test')")
        scripts = list(Config.SCRIPTS_DIR.glob("_exec_*.py"))
        assert len(scripts) == 0

    @pytest.mark.asyncio
    async def test_no_output(self, temp_data_dirs):
        """Code that produces no output."""
        result = await tool_python("x = 42")
        assert result["status"] == "success"
        assert "Code executed with no output" in result["output"] or "Exit code: 0" in result["output"]

    @pytest.mark.asyncio
    async def test_timeout(self, temp_data_dirs, monkeypatch):
        """Python timeout should be handled."""
        import bot.tools
        monkeypatch.setattr(bot.tools, "TOOL_TIMEOUT", 1)
        result = await tool_python("import time; time.sleep(10)")
        assert result["status"] == "error"
        assert "timed out" in result["output"]

    @pytest.mark.asyncio
    async def test_general_exception(self, temp_data_dirs):
        """Should handle unexpected errors."""
        with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
            result = await tool_python("print('test')")
            assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_python_unlink_error(self, temp_data_dirs):
        """Should cover L253-254 exception handler during cleanup."""
        # Patch Path.unlink to raise OSError on the temp script
        original_unlink = Path.unlink
        def mock_unlink(self, *args, **kwargs):
            if "_exec_" in self.name:
                raise OSError("Cleanup failed")
            return original_unlink(self, *args, **kwargs)

        with patch.object(Path, "unlink", autospec=True, side_effect=mock_unlink):
            result = await tool_python("print('loop')")
            assert result["status"] == "success"
            assert "loop" in result["output"]


# ── Tool: SELF_MODIFY ───────────────────────────────────────────────────────

class TestToolSelfModify:
    @pytest.mark.asyncio
    async def test_modify_file(self, temp_data_dirs):
        result = await tool_self_modify("test_file.py", "# modified content")
        assert result["status"] == "success"
        target = Config.BOT_ROOT / "test_file.py"
        assert target.read_text(encoding="utf-8") == "# modified content"

    @pytest.mark.asyncio
    async def test_modify_creates_dirs(self, temp_data_dirs):
        result = await tool_self_modify("new_dir/new_file.py", "content")
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_modify_write_error(self, temp_data_dirs):
        """Should handle write errors."""
        with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
            result = await tool_self_modify("broken.py", "content")
            assert result["status"] == "error"
            assert "Self-modification failed" in result["output"]

    @pytest.mark.asyncio
    async def test_path_traversal_blocked(self, temp_data_dirs):
        """Paths outside bot root should be blocked."""
        # This depends on how ../ resolves relative to the temp dir
        # The safety check is: str(target).startswith(str(Config.BOT_ROOT))
        # On temp dirs, ../../../etc/passwd would resolve outside
        with patch.object(Path, 'resolve', return_value=Path("/etc/evil")):
            result = await tool_self_modify("../../../etc/passwd", "hacked")
            assert result["status"] == "error"
            assert "Path must be within" in result["output"]


# ── Tool: SELF_RESTART ──────────────────────────────────────────────────────

class TestToolSelfRestart:
    @pytest.mark.asyncio
    async def test_restart_returns_success(self):
        """Should return success before scheduling exit."""
        import warnings
        mock_loop = MagicMock()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            with patch("bot.tools.asyncio.get_event_loop", return_value=mock_loop):
                result = await tool_self_restart()
                assert result["status"] == "success"
                assert "restart" in result["output"].lower()
                mock_loop.call_later.assert_called_once()


# ── Extract Tool Calls ──────────────────────────────────────────────────────

class TestExtractToolCalls:
    def test_web_search(self):
        text = "Let me search [WEB_SEARCH]python latest version[/WEB_SEARCH]"
        name, params = extract_tool_calls(text)
        assert name == "WEB_SEARCH"
        assert params == ["python latest version"]

    def test_web_read(self):
        text = "[WEB_READ]https://example.com[/WEB_READ]"
        name, params = extract_tool_calls(text)
        assert name == "WEB_READ"
        assert params == ["https://example.com"]

    def test_file_read(self):
        text = "[FILE_READ]C:/test.txt[/FILE_READ]"
        name, params = extract_tool_calls(text)
        assert name == "FILE_READ"

    def test_file_write(self):
        text = "[FILE_WRITE]test.txt|content here[/FILE_WRITE]"
        name, params = extract_tool_calls(text)
        assert name == "FILE_WRITE"
        assert "content here" in params[0]

    def test_list_files(self):
        text = "[LIST_FILES]./[/LIST_FILES]"
        name, params = extract_tool_calls(text)
        assert name == "LIST_FILES"

    def test_exec(self):
        text = "[EXEC]echo hello[/EXEC]"
        name, params = extract_tool_calls(text)
        assert name == "EXEC"

    def test_python(self):
        text = "[PYTHON]print('hi')[/PYTHON]"
        name, params = extract_tool_calls(text)
        assert name == "PYTHON"

    def test_self_modify(self):
        text = "[SELF_MODIFY]bot/test.py|# new code[/SELF_MODIFY]"
        name, params = extract_tool_calls(text)
        assert name == "SELF_MODIFY"

    def test_self_restart(self):
        text = "[SELF_RESTART][/SELF_RESTART]"
        name, params = extract_tool_calls(text)
        assert name == "SELF_RESTART"

    def test_no_tool_call(self):
        text = "Just a regular message without any tools."
        name, params = extract_tool_calls(text)
        assert name is None
        assert params == []

    def test_multiline_tool(self):
        text = "[PYTHON]\nline1\nline2\nline3\n[/PYTHON]"
        name, params = extract_tool_calls(text)
        assert name == "PYTHON"
        assert "line1" in params[0]

    def test_first_tool_wins(self):
        """When multiple tools of different types are present, dict order determines winner."""
        text = "[WEB_SEARCH]query[/WEB_SEARCH] [PYTHON]code[/PYTHON]"
        name, params = extract_tool_calls(text)
        # WEB_SEARCH comes first in TOOL_PATTERNS dict
        assert name == "WEB_SEARCH"


# ── Execute Tool Dispatcher ─────────────────────────────────────────────────

class TestExecuteTool:
    @pytest.mark.asyncio
    async def test_dispatch_file_read(self, temp_data_dirs):
        f = temp_data_dirs / "dispatch_test.txt"
        f.write_text("dispatched!", encoding="utf-8")
        result = await execute_tool("FILE_READ", [str(f)])
        assert result["status"] == "success"
        assert "dispatched!" in result["output"]

    @pytest.mark.asyncio
    async def test_dispatch_file_write(self, temp_data_dirs):
        target = str(temp_data_dirs / "write_test.txt")
        result = await execute_tool("FILE_WRITE", [f"{target}|written content"])
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_dispatch_file_write_bad_format(self):
        result = await execute_tool("FILE_WRITE", ["no pipe separator"])
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_dispatch_list_files(self, temp_data_dirs):
        result = await execute_tool("LIST_FILES", [str(temp_data_dirs)])
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_dispatch_exec(self):
        result = await execute_tool("EXEC", ["echo dispatch_test"])
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_dispatch_python(self, temp_data_dirs):
        result = await execute_tool("PYTHON", ["print(42)"])
        assert result["status"] == "success"
        assert "42" in result["output"]

    @pytest.mark.asyncio
    async def test_dispatch_self_modify(self, temp_data_dirs):
        result = await execute_tool("SELF_MODIFY", ["test.py|# code"])
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_dispatch_self_modify_bad_format(self):
        result = await execute_tool("SELF_MODIFY", ["bad format no pipe"])
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_dispatch_self_restart(self):
        mock_loop = MagicMock()
        with patch("asyncio.get_event_loop", return_value=mock_loop):
            result = await execute_tool("SELF_RESTART", [])
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_dispatch_web_search(self, temp_data_dirs):
        with patch("bot.tools.asyncio.get_event_loop") as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value="result")
            result = await execute_tool("WEB_SEARCH", ["test"])
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_dispatch_web_read(self):
        result = await execute_tool("WEB_READ", ["http://nonexistent.invalid.test"])
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_dispatch_unknown_tool(self):
        result = await execute_tool("UNKNOWN_TOOL", ["param"])
        assert result["status"] == "error"
        assert "Unknown tool" in result["output"]

    @pytest.mark.asyncio
    async def test_dispatch_empty_params(self):
        result = await execute_tool("LIST_FILES", [])
        assert isinstance(result, dict)


# ── Tool Descriptions ───────────────────────────────────────────────────────

class TestToolDescriptions:
    def test_descriptions_not_empty(self):
        assert len(TOOL_DESCRIPTIONS) > 100

    def test_all_tools_documented(self):
        for tool in ["WEB_SEARCH", "WEB_READ", "FILE_READ", "FILE_WRITE",
                      "LIST_FILES", "EXEC", "PYTHON", "SELF_MODIFY", "SELF_RESTART"]:
            assert tool in TOOL_DESCRIPTIONS
