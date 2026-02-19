"""
Qwen CLI integration with retry logic, improved prompting, and multi-turn tool loop.
"""

import asyncio
import logging
import json
from typing import Optional

from bot.config import Config
from bot.tools import TOOL_DESCRIPTIONS

logger = logging.getLogger("telegram-qwen.qwen")


def build_system_prompt() -> str:
    """Build the system prompt for Qwen with tool descriptions."""
    return (
        "You are Qwen, a powerful autonomous AI agent running on a Windows machine. "
        "You have full admin access to the system. You can execute commands, read/write files anywhere, "
        "browse the web, run Python code, and even modify your own source code and restart yourself.\n\n"
        "You are persistent and determined. For complex tasks:\n"
        "- Break them into clear steps\n"
        "- Execute each step using tools\n"
        "- Verify results before moving to the next step\n"
        "- If something fails, diagnose the error and retry with a corrected approach\n"
        "- Never give up on the first failure — analyze and adapt\n\n"
        "### ROOT DIRECTORY HYGIENE (STRICT RULE):\n"
        "- **NEVER** create files, scripts, or folders in the root directory: `c:\\Users\\Aarsh\\Source\\telegram-qwen\\`.\n"
        "- **ALWAYS** use the `workspace/` directory for all temporary files, helper scripts, tests, or output files.\n"
        "- The root directory is reserved ONLY for core application code. If you must create a new script to test something, it BELONGS in `workspace/`.\n\n"
        "You are talking to your admin via Telegram. Be concise but thorough in your final responses.\n\n"
        f"{TOOL_DESCRIPTIONS}"
    )


async def call_qwen(prompt: str) -> str:
    """
    Call the Qwen CLI with retry logic.
    Returns the raw response text.
    """
    last_error = None

    for attempt in range(1, Config.MAX_RETRIES + 1):
        try:
            logger.info(f"Qwen call attempt {attempt}/{Config.MAX_RETRIES}")

            process = await asyncio.create_subprocess_shell(
                "qwen -y",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=prompt.encode("utf-8")),
                timeout=Config.QWEN_TIMEOUT,
            )

            if stderr:
                stderr_text = stderr.decode("utf-8", errors="replace").strip()
                if stderr_text:
                    logger.warning(f"Qwen stderr: {stderr_text}")

            if stdout:
                response = stdout.decode("utf-8", errors="replace").strip()
                if response:
                    return response

            logger.warning(f"Qwen returned empty response (attempt {attempt})")
            last_error = "Empty response from Qwen"

        except asyncio.TimeoutError:
            logger.warning(f"Qwen timed out after {Config.QWEN_TIMEOUT}s (attempt {attempt})")
            last_error = f"Qwen timed out after {Config.QWEN_TIMEOUT}s"

        except Exception as e:
            logger.error(f"Qwen call failed (attempt {attempt}): {e}")
            last_error = str(e)

        # Exponential backoff between retries: 5s, 15s, 45s
        if attempt < Config.MAX_RETRIES:
            wait = 5 * (3 ** (attempt - 1))
            logger.info(f"Waiting {wait}s before retry...")
            await asyncio.sleep(wait)

    return f"❌ Qwen failed after {Config.MAX_RETRIES} attempts. Last error: {last_error}"


async def call_qwen_with_context(
    user_input: str,
    conversation_history: str,
    task_context: str = "",
) -> str:
    """
    Build the full prompt with system instructions, history, and user input,
    then call Qwen.
    """
    system_prompt = build_system_prompt()

    parts = [system_prompt, ""]

    if task_context:
        parts.append(f"TASK CONTEXT (resumed from checkpoint):\n{task_context}\n")

    if conversation_history:
        parts.append(f"CONVERSATION HISTORY:\n{conversation_history}\n")

    parts.append(f"USER: {user_input}\n\nASSISTANT:")

    full_prompt = "\n".join(parts)

    return await call_qwen(full_prompt)
