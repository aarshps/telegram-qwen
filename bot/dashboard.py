import os
import json
import logging
import psutil
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from bot.config import Config
from bot.task_engine import TaskStatus

# Create a dedicated logger for the dashboard
logger = logging.getLogger("telegram-qwen.dashboard")

app = FastAPI(title="Telegram-Qwen Agent Dashboard")

# Paths
DASHBOARD_DIR = Config.BOT_ROOT / "dashboard"
DASHBOARD_DIR.mkdir(exist_ok=True)

@app.get("/api/stats")
async def get_stats():
    """Get high-level system and agent stats."""
    task_files = list(Config.TASK_DIR.glob("*.json"))
    conv_files = list(Config.CONVERSATION_DIR.glob("*.json"))
    
    # Calculate statuses
    status_counts = {s.value: 0 for s in TaskStatus}
    total_steps = 0
    
    for tf in task_files:
        try:
            data = json.loads(tf.read_text(encoding="utf-8"))
            status = data.get("status", "unknown")
            if status in status_counts:
                status_counts[status] += 1
            total_steps += len(data.get("steps", []))
        except (json.JSONDecodeError, OSError):
            continue

    # Qwen Stats
    qwen_version = "Unknown"
    qwen_status = "❌ Unavailable"
    try:
        import subprocess
        # Use shell=True because qwen might be a .cmd or .ps1 in the path
        result = subprocess.run("qwen --version", shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            qwen_version = result.stdout.strip()
            qwen_status = "✅ Available"
    except Exception:
        pass

    return {
        "tasks": {
            "total": len(task_files),
            "completed": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
            "running": status_counts.get("running", 0),
            "pending": status_counts.get("pending", 0),
            "checkpoints": status_counts.get("checkpoint", 0),
            "total_steps": total_steps
        },
        "conversations": len(conv_files),
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "uptime_seconds": int(psutil.boot_time()) # Simplified uptime
        },
        "qwen": {
            "version": qwen_version,
            "status": qwen_status,
            "mcp_enabled": (Config.BOT_ROOT / ".qwen" / "mcp_settings.json").exists() # Heuristic check
        }
    }

@app.get("/api/tasks")
async def list_tasks(limit: int = 50):
    """List recent tasks with details."""
    tasks = []
    task_files = sorted(Config.TASK_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    for tf in task_files[:limit]:
        try:
            data = json.loads(tf.read_text(encoding="utf-8"))
            # No full truncation, allow UI to handle long text
            tasks.append(data)
        except (json.JSONDecodeError, OSError):
            continue
            
    return tasks

@app.get("/api/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """Get full details of a specific task."""
    task_file = Config.TASK_DIR / f"{task_id}.json"
    if not task_file.exists():
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        return json.loads(task_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations")
async def list_conversations():
    """List conversation histories."""
    conversations = []
    conv_files = sorted(Config.CONVERSATION_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    for cf in conv_files:
        try:
            data = json.loads(cf.read_text(encoding="utf-8"))
            conversations.append({
                "chat_id": cf.stem,
                "message_count": len(data),
                "last_message": data[-1]["content"][:100] if data else "Empty",
                "updated_at": cf.stat().st_mtime
            })
        except (json.JSONDecodeError, OSError):
            continue
            
    return conversations

@app.get("/api/conversations/{chat_id}")
async def get_conversation_detail(chat_id: str):
    """Get full message history for a chat."""
    conv_file = Config.CONVERSATION_DIR / f"{chat_id}.json"
    if not conv_file.exists():
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        return json.loads(conv_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent system logs."""
    from bot.config import LOG_FILE
    if not LOG_FILE.exists():
        return "No logs yet."
    try:
        content = LOG_FILE.read_text(encoding="utf-8")
        log_lines = content.splitlines()[-lines:]
        return "\n".join(log_lines)
    except Exception as e:
        return f"Error reading logs: {e}"

@app.get("/api/config")
async def get_config():
    """Expose non-sensitive config for the dashboard."""
    return {
        "max_tool_turns": Config.MAX_TOOL_TURNS,
        "qwen_timeout": Config.QWEN_TIMEOUT,
        "max_retries": Config.MAX_RETRIES,
        "max_history_length": Config.MAX_HISTORY_LENGTH,
        "rate_limits": {
            "messages": Config.RATE_LIMIT_MESSAGES,
            "window": Config.RATE_LIMIT_WINDOW
        },
        "bot_root": str(Config.BOT_ROOT),
        "data_dir": str(Config.DATA_DIR)
    }

@app.get("/")
async def serve_dashboard():
    return FileResponse(DASHBOARD_DIR / "index.html")

# Serve other static files
app.mount("/", StaticFiles(directory=str(DASHBOARD_DIR)), name="static")

def start_dashboard(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    logger.info(f"Starting dashboard on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="error")
