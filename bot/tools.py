"""
Expanded toolset for the autonomous agent.
No file path restrictions — full system access.
Includes self-modification and self-restart capabilities.
"""

import os
import sys
import asyncio
import json
import re
import logging
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from bot.config import Config

logger = logging.getLogger("telegram-qwen.tools")

# Tool timeout for individual executions (seconds)
TOOL_TIMEOUT = 600  # 10 minutes


def _result(status: str, output: str, truncated: bool = False) -> dict:
    """Create a structured tool result."""
    return {"status": status, "output": output, "truncated": truncated}


def _truncate(text: str, max_len: int = None) -> tuple[str, bool]:
    """Truncate text if it exceeds max length."""
    max_len = max_len or Config.MAX_OUTPUT_LENGTH
    if len(text) > max_len:
        return text[:max_len] + "\n...[Output Truncated]", True
    return text, False


# ─── Tool: WEB_SEARCH ───────────────────────────────────────────────────────

async def tool_web_search(query: str) -> dict:
    """Search the web using DuckDuckGo."""
    try:
        from duckduckgo_search import DDGS

        def _search():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=8))
            if not results:
                return "No results found."
            lines = []
            for i, r in enumerate(results, 1):
                lines.append(f"{i}. **{r.get('title', 'No title')}**")
                lines.append(f"   {r.get('href', '')}")
                lines.append(f"   {r.get('body', '')}")
                lines.append("")
            return "\n".join(lines)

        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, _search)
        output, truncated = _truncate(text)
        return _result("success", output, truncated)

    except Exception as e:
        logger.error(f"WEB_SEARCH error: {e}")
        return _result("error", f"Web search failed: {e}")


# ─── Tool: WEB_READ ─────────────────────────────────────────────────────────

async def tool_web_read(url: str) -> dict:
    """Fetch and extract text from a URL."""
    try:
        import httpx
        from bs4 import BeautifulSoup

        async with httpx.AsyncClient(
            timeout=60,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        output, truncated = _truncate(text, 10000)
        return _result("success", output, truncated)

    except Exception as e:
        logger.error(f"WEB_READ error: {e}")
        return _result("error", f"Failed to fetch URL: {e}")


# ─── Tool: FILE_READ ────────────────────────────────────────────────────────

async def tool_file_read(filepath: str) -> dict:
    """Read any file on the system."""
    try:
        path = Path(filepath).expanduser().resolve()
        if not path.exists():
            return _result("error", f"File not found: {filepath}")
        if not path.is_file():
            return _result("error", f"Not a file: {filepath}")

        content = path.read_text(encoding="utf-8", errors="replace")
        output, truncated = _truncate(content, 10000)
        return _result("success", output, truncated)

    except Exception as e:
        logger.error(f"FILE_READ error: {e}")
        return _result("error", f"Failed to read file: {e}")


# ─── Tool: FILE_WRITE ───────────────────────────────────────────────────────

async def tool_file_write(filepath: str, content: str) -> dict:
    """Write to any file on the system."""
    try:
        path = Path(filepath).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return _result("success", f"Successfully wrote {len(content)} bytes to {path}")

    except Exception as e:
        logger.error(f"FILE_WRITE error: {e}")
        return _result("error", f"Failed to write file: {e}")


# ─── Tool: LIST_FILES ───────────────────────────────────────────────────────

async def tool_list_files(directory: str) -> dict:
    """List files in any directory."""
    try:
        path = Path(directory).expanduser().resolve()
        if not path.exists():
            return _result("error", f"Directory not found: {directory}")
        if not path.is_dir():
            return _result("error", f"Not a directory: {directory}")

        entries = []
        for item in sorted(path.iterdir()):
            prefix = "📁 " if item.is_dir() else "📄 "
            size = ""
            if item.is_file():
                s = item.stat().st_size
                if s < 1024:
                    size = f" ({s}B)"
                elif s < 1024 * 1024:
                    size = f" ({s // 1024}KB)"
                else:
                    size = f" ({s // (1024 * 1024)}MB)"
            entries.append(f"{prefix}{item.name}{size}")

        if not entries:
            return _result("success", f"Empty directory: {directory}")

        output, truncated = _truncate("\n".join(entries))
        return _result("success", output, truncated)

    except Exception as e:
        logger.error(f"LIST_FILES error: {e}")
        return _result("error", f"Failed to list directory: {e}")


# ─── Tool: EXEC ─────────────────────────────────────────────────────────────

async def tool_exec(command: str) -> dict:
    """Execute any shell command with no restrictions."""
    try:
        # Use cmd on Windows, shell on Unix
        if os.name == "nt":
            shell_cmd = command
            # Don't double-wrap if already using cmd/powershell
            if not any(command.lower().startswith(s) for s in ("cmd", "powershell")):
                shell_cmd = f"cmd /c {command}"
        else:
            shell_cmd = command

        process = await asyncio.create_subprocess_shell(
            shell_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=TOOL_TIMEOUT
        )

        output_parts = []
        if stdout:
            output_parts.append(stdout.decode("utf-8", errors="replace").strip())
        if stderr:
            err_text = stderr.decode("utf-8", errors="replace").strip()
            if err_text:
                output_parts.append(f"STDERR: {err_text}")

        result_text = "\n".join(output_parts) if output_parts else "Command executed with no output."
        result_text += f"\n[Exit code: {process.returncode}]"

        output, truncated = _truncate(result_text)
        return _result("success" if process.returncode == 0 else "error", output, truncated)

    except asyncio.TimeoutError:
        return _result("error", f"Command timed out after {TOOL_TIMEOUT}s.")
    except Exception as e:
        logger.error(f"EXEC error: {e}")
        return _result("error", f"Command execution failed: {e}")


# ─── Tool: PYTHON ────────────────────────────────────────────────────────────

async def tool_python(code: str) -> dict:
    """Execute Python code directly. Writes to a temp file, runs it, captures output."""
    try:
        Config.ensure_dirs()
        # Write code to a temp file in scripts/
        script_path = Config.SCRIPTS_DIR / f"_exec_{os.getpid()}.py"
        script_path.write_text(code, encoding="utf-8")

        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, str(script_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=TOOL_TIMEOUT
            )

            output_parts = []
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace").strip())
            if stderr:
                err_text = stderr.decode("utf-8", errors="replace").strip()
                if err_text:
                    output_parts.append(f"STDERR: {err_text}")

            result_text = "\n".join(output_parts) if output_parts else "Code executed with no output."
            result_text += f"\n[Exit code: {process.returncode}]"

            output, truncated = _truncate(result_text)
            return _result("success" if process.returncode == 0 else "error", output, truncated)

        finally:
            # Cleanup temp script
            try:
                script_path.unlink()
            except OSError:
                pass

    except asyncio.TimeoutError:
        return _result("error", f"Python execution timed out after {TOOL_TIMEOUT}s.")
    except Exception as e:
        logger.error(f"PYTHON error: {e}")
        return _result("error", f"Python execution failed: {e}")


# ─── Tool: SELF_MODIFY ──────────────────────────────────────────────────────

async def tool_self_modify(relative_path: str, content: str) -> dict:
    """Modify the bot's own source files. Path is relative to the bot root."""
    try:
        target = (Config.BOT_ROOT / relative_path).resolve()

        # Safety check: must be within bot root
        if not str(target).startswith(str(Config.BOT_ROOT)):
            return _result("error", "Path must be within the bot directory.")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        logger.info(f"SELF_MODIFY: Updated {target}")
        return _result("success", f"Successfully modified {relative_path}. Use SELF_RESTART to apply changes.")

    except Exception as e:
        logger.error(f"SELF_MODIFY error: {e}")
        return _result("error", f"Self-modification failed: {e}")


# ─── Tool: SELF_RESTART ─────────────────────────────────────────────────────

async def tool_self_restart() -> dict:
    """Trigger a bot restart by exiting with the restart exit code."""
    logger.info("SELF_RESTART triggered — exiting with code 42")
    # Schedule the exit slightly in the future so we can return the result first
    loop = asyncio.get_event_loop()
    loop.call_later(2, lambda: os._exit(Config.RESTART_EXIT_CODE))
    return _result("success", "Bot will restart in 2 seconds...")


# ─── Tool Dispatcher ────────────────────────────────────────────────────────

# Tool call patterns — support [TOOL]...[/TOOL] format
TOOL_PATTERNS = {
    "WEB_SEARCH": re.compile(r"\[WEB_SEARCH\](.*?)\[/WEB_SEARCH\]", re.DOTALL),
    "WEB_READ": re.compile(r"\[WEB_READ\](.*?)\[/WEB_READ\]", re.DOTALL),
    "FILE_READ": re.compile(r"\[FILE_READ\](.*?)\[/FILE_READ\]", re.DOTALL),
    "FILE_WRITE": re.compile(r"\[FILE_WRITE\](.*?)\[/FILE_WRITE\]", re.DOTALL),
    "LIST_FILES": re.compile(r"\[LIST_FILES\](.*?)\[/LIST_FILES\]", re.DOTALL),
    "EXEC": re.compile(r"\[EXEC\](.*?)\[/EXEC\]", re.DOTALL),
    "PYTHON": re.compile(r"\[PYTHON\](.*?)\[/PYTHON\]", re.DOTALL),
    "SELF_MODIFY": re.compile(r"\[SELF_MODIFY\](.*?)\[/SELF_MODIFY\]", re.DOTALL),
    "SELF_RESTART": re.compile(r"\[SELF_RESTART\](.*?)\[/SELF_RESTART\]", re.DOTALL),
}


def extract_tool_calls(text: str) -> tuple[str | None, list[str]]:
    """Extract the first tool call from text. Returns (tool_name, [params])."""
    for tool_name, pattern in TOOL_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            return tool_name, [m.strip() for m in matches]
    return None, []


async def execute_tool(tool_name: str, params: list[str]) -> dict:
    """Dispatch and execute a tool call."""
    param = params[0] if params else ""

    if tool_name == "WEB_SEARCH":
        return await tool_web_search(param)

    elif tool_name == "WEB_READ":
        return await tool_web_read(param)

    elif tool_name == "FILE_READ":
        return await tool_file_read(param)

    elif tool_name == "FILE_WRITE":
        # Format: filepath|content
        parts = param.split("|", 1)
        if len(parts) != 2:
            return _result("error", "FILE_WRITE requires 'filepath|content' format")
        return await tool_file_write(parts[0].strip(), parts[1])

    elif tool_name == "LIST_FILES":
        return await tool_list_files(param or ".")

    elif tool_name == "EXEC":
        return await tool_exec(param)

    elif tool_name == "PYTHON":
        return await tool_python(param)

    elif tool_name == "SELF_MODIFY":
        # Format: filepath|content
        parts = param.split("|", 1)
        if len(parts) != 2:
            return _result("error", "SELF_MODIFY requires 'relative_path|content' format")
        return await tool_self_modify(parts[0].strip(), parts[1])

    elif tool_name == "SELF_RESTART":
        return await tool_self_restart()

    else:
        return _result("error", f"Unknown tool: {tool_name}")


# ─── Tool Descriptions (for system prompt) ───────────────────────────────────

TOOL_DESCRIPTIONS = """
You have the following tools available. To use a tool, wrap your call in the appropriate tags.

## Available Tools

1. **[WEB_SEARCH]query[/WEB_SEARCH]** — Search the web using DuckDuckGo
   Example: [WEB_SEARCH]current Bitcoin price USD[/WEB_SEARCH]

2. **[WEB_READ]url[/WEB_READ]** — Fetch and extract text from a URL
   Example: [WEB_READ]https://example.com/article[/WEB_READ]

3. **[FILE_READ]filepath[/FILE_READ]** — Read any file on the system
   Example: [FILE_READ]C:/Users/Aarsh/document.txt[/FILE_READ]

4. **[FILE_WRITE]filepath|content[/FILE_WRITE]** — Write content to any file
   Example: [FILE_WRITE]C:/Users/Aarsh/output.txt|Hello World[/FILE_WRITE]

5. **[LIST_FILES]directory[/LIST_FILES]** — List files in any directory
   Example: [LIST_FILES]C:/Users/Aarsh/Projects[/LIST_FILES]

6. **[EXEC]command[/EXEC]** — Execute any shell command (full admin access)
   Example: [EXEC]pip install requests[/EXEC]

7. **[PYTHON]code[/PYTHON]** — Execute Python code directly
   Example: [PYTHON]
   import math
   print(math.factorial(20))
   [/PYTHON]

8. **[SELF_MODIFY]relative_path|new_content[/SELF_MODIFY]** — Edit the bot's own source files
   Example: [SELF_MODIFY]bot/tools.py|<new file content>[/SELF_MODIFY]

9. **[SELF_RESTART][/SELF_RESTART]** — Restart the bot (use after self-modification)

## Rules
- You can chain multiple tool calls across turns. After each tool result, decide the next step.
- You have up to 15 sequential tool turns per request — use them for complex multi-step tasks.
- For long tasks, break work into steps. Each tool call's result feeds into your next decision.
- You have FULL admin access to this machine. No restrictions on file paths or commands.
- For tasks requiring file creation, you can write anywhere on the system.
- If a tool fails, analyze the error and retry with a corrected approach.
- When done with all tool calls, provide a final summary to the user.
""".strip()
