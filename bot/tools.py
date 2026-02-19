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

# Ensure workspace is in sys.path for dynamic imports of agent-created scripts
if str(Config.WORKSPACE_DIR) not in sys.path:
    sys.path.append(str(Config.WORKSPACE_DIR))

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
        # Write code to a temp file in workspace/
        script_path = Config.WORKSPACE_DIR / f"_exec_{os.getpid()}.py"
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


# ─── Tool: MOLTBOOK_POST_COMMENT ────────────────────────────────────────────────

async def tool_moltbook_post_comment(num_comments: str) -> dict:
    """Post comments on other users' posts on Moltbook."""
    try:
        from moltbook_api import post_comment_on_other_posts
        
        num = int(num_comments) if num_comments.isdigit() else 5
        api_key = os.getenv('MOLTBOOK_API_KEY')
        
        if not api_key:
            return _result("error", "MOLTBOOK_API_KEY environment variable is not set")
        
        results = post_comment_on_other_posts(api_key, num)
        
        success_count = sum(1 for r in results if r['success'])
        output = f"Attempted to post {num} comments, {success_count} succeeded:\n\n"
        for result in results:
            if result['success']:
                output += f"✓ Commented on '{result['post_title']}' (Post ID: {result['post_id']})\n"
            else:
                output += f"✗ Failed to comment on '{result['post_title']}': {result['error']}\n"
        
        return _result("success", output)

    except Exception as e:
        logger.error(f"MOLTBOOK_POST_COMMENT error: {e}")
        return _result("error", f"Failed to post comments on Moltbook: {e}")


# ─── Tool: MOLTBOOK_UPVOTE ──────────────────────────────────────────────────────

async def tool_moltbook_upvote(post_count: str, comment_count: str) -> dict:
    """Upvote posts and comments on Moltbook."""
    try:
        from moltbook_api import upvote_content
        
        post_num = int(post_count) if post_count.isdigit() else 5
        comment_num = int(comment_count) if comment_count.isdigit() else 10
        api_key = os.getenv('MOLTBOOK_API_KEY')
        
        if not api_key:
            return _result("error", "MOLTBOOK_API_KEY environment variable is not set")
        
        results = upvote_content(api_key, post_num, comment_num)
        
        post_success_count = sum(1 for r in results['post_upvotes'] if r['success'])
        comment_success_count = sum(1 for r in results['comment_upvotes'] if r['success'])
        
        output = f"Attempted to upvote {post_num} posts and {comment_num} comments\n"
        output += f"Posts: {post_success_count}/{post_num} succeeded\n"
        output += f"Comments: {comment_success_count}/{comment_num} succeeded\n\n"
        
        output += "Post upvotes:\n"
        for result in results['post_upvotes']:
            if result['success']:
                output += f"✓ Upvoted '{result['post_title']}' (Post ID: {result['post_id']})\n"
            else:
                output += f"✗ Failed to upvote '{result['post_title']}': {result['error']}\n"
        
        output += "\nComment upvotes:\n"
        for result in results['comment_upvotes']:
            if result['success']:
                output += f"✓ Upvoted comment (ID: {result['comment_id']})\n"
            else:
                output += f"✗ Failed to upvote comment (ID: {result['comment_id']}): {result['error']}\n"
        
        return _result("success", output)

    except Exception as e:
        logger.error(f"MOLTBOOK_UPVOTE error: {e}")
        return _result("error", f"Failed to upvote content on Moltbook: {e}")


# ─── Tool: MOLTBOOK_DOWNVOTE ────────────────────────────────────────────────────

async def tool_moltbook_downvote(post_count: str, comment_count: str) -> dict:
    """Downvote posts and comments on Moltbook."""
    try:
        from moltbook_api import downvote_content
        
        post_num = int(post_count) if post_count.isdigit() else 5
        comment_num = int(comment_count) if comment_count.isdigit() else 10
        api_key = os.getenv('MOLTBOOK_API_KEY')
        
        if not api_key:
            return _result("error", "MOLTBOOK_API_KEY environment variable is not set")
        
        results = downvote_content(api_key, post_num, comment_num)
        
        post_success_count = sum(1 for r in results['post_downvotes'] if r['success'])
        comment_success_count = sum(1 for r in results['comment_downvotes'] if r['success'])
        
        output = f"Attempted to downvote {post_num} posts and {comment_num} comments\n"
        output += f"Posts: {post_success_count}/{post_num} succeeded\n"
        output += f"Comments: {comment_success_count}/{comment_num} succeeded\n\n"
        
        output += "Post downvotes:\n"
        for result in results['post_downvotes']:
            if result['success']:
                output += f"✓ Downvoted '{result['post_title']}' (Post ID: {result['post_id']})\n"
            else:
                output += f"✗ Failed to downvote '{result['post_title']}': {result['error']}\n"
        
        output += "\nComment downvotes:\n"
        for result in results['comment_downvotes']:
            if result['success']:
                output += f"✓ Downvoted comment (ID: {result['comment_id']})\n"
            else:
                output += f"✗ Failed to downvote comment (ID: {result['comment_id']}): {result['error']}\n"
        
        return _result("success", output)

    except Exception as e:
        logger.error(f"MOLTBOOK_DOWNVOTE error: {e}")
        return _result("error", f"Failed to downvote content on Moltbook: {e}")


# ─── Tool: MOLTBOOK_CREATE_POST ─────────────────────────────────────────────────

async def tool_moltbook_create_post(num_posts: str) -> dict:
    """Create new posts on Moltbook."""
    try:
        from moltbook_api import create_new_posts
        
        num = int(num_posts) if num_posts.isdigit() else 5
        api_key = os.getenv('MOLTBOOK_API_KEY')
        
        if not api_key:
            return _result("error", "MOLTBOOK_API_KEY environment variable is not set")
        
        results = create_new_posts(api_key, num)
        
        success_count = sum(1 for r in results if r['success'])
        output = f"Attempted to create {num} posts, {success_count} succeeded:\n\n"
        for result in results:
            if result['success']:
                output += f"✓ Created post '{result['title']}'\n"
            else:
                output += f"✗ Failed to create post '{result['title']}': {result['error']}\n"
        
        return _result("success", output)

    except Exception as e:
        logger.error(f"MOLTBOOK_CREATE_POST error: {e}")
        return _result("error", f"Failed to create posts on Moltbook: {e}")


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
    "MOLTBOOK_POST_COMMENT": re.compile(r"\[MOLTBOOK_POST_COMMENT\](.*?)\[/MOLTBOOK_POST_COMMENT\]", re.DOTALL),
    "MOLTBOOK_UPVOTE": re.compile(r"\[MOLTBOOK_UPVOTE\](.*?)\[/MOLTBOOK_UPVOTE\]", re.DOTALL),
    "MOLTBOOK_DOWNVOTE": re.compile(r"\[MOLTBOOK_DOWNVOTE\](.*?)\[/MOLTBOOK_DOWNVOTE\]", re.DOTALL),
    "MOLTBOOK_CREATE_POST": re.compile(r"\[MOLTBOOK_CREATE_POST\](.*?)\[/MOLTBOOK_CREATE_POST\]", re.DOTALL),
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

    elif tool_name == "MOLTBOOK_POST_COMMENT":
        return await tool_moltbook_post_comment(param)

    elif tool_name == "MOLTBOOK_UPVOTE":
        # Format: post_count|comment_count
        parts = param.split("|", 1)
        post_count = parts[0].strip() if parts else "5"
        comment_count = parts[1].strip() if len(parts) > 1 else "10"
        return await tool_moltbook_upvote(post_count, comment_count)

    elif tool_name == "MOLTBOOK_DOWNVOTE":
        # Format: post_count|comment_count
        parts = param.split("|", 1)
        post_count = parts[0].strip() if parts else "5"
        comment_count = parts[1].strip() if len(parts) > 1 else "10"
        return await tool_moltbook_downvote(post_count, comment_count)

    elif tool_name == "MOLTBOOK_CREATE_POST":
        return await tool_moltbook_create_post(param)

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

10. **[MOLTBOOK_POST_COMMENT]num_comments[/MOLTBOOK_POST_COMMENT]** — Post comments on other users' posts on Moltbook
    Example: [MOLTBOOK_POST_COMMENT]5[/MOLTBOOK_POST_COMMENT]

11. **[MOLTBOOK_UPVOTE]post_count|comment_count[/MOLTBOOK_UPVOTE]** — Upvote posts and comments on Moltbook
    Example: [MOLTBOOK_UPVOTE]5|10[/MOLTBOOK_UPVOTE]

12. **[MOLTBOOK_DOWNVOTE]post_count|comment_count[/MOLTBOOK_DOWNVOTE]** — Downvote posts and comments on Moltbook
    Example: [MOLTBOOK_DOWNVOTE]5|10[/MOLTBOOK_DOWNVOTE]

13. **[MOLTBOOK_CREATE_POST]num_posts[/MOLTBOOK_CREATE_POST]** — Create new posts on Moltbook
    Example: [MOLTBOOK_CREATE_POST]5[/MOLTBOOK_CREATE_POST]

## Rules
- You can chain multiple tool calls across turns. After each tool result, decide the next step.
- You have up to 15 sequential tool turns per request — use them for complex multi-step tasks.
- For long tasks, break work into steps. Each tool call's result feeds into your next decision.
- **STRICT DIRECTORY HYGIENE**: You have FULL admin access, but you MUST NOT clutter the root directory.
- **ALWAYS** use the `workspace/` directory for all temporary files, helper scripts, data processing, and test outputs.
- Never create new files in the root folder unless you are explicitly modifying the bot's core logic with `SELF_MODIFY`.
- For any tasks requiring temporary file creation or script execution, use `workspace/path/to/file`.
- If a tool fails, analyze the error and retry with a corrected approach.
- When done with all tool calls, provide a final summary to the user.
""".strip()
