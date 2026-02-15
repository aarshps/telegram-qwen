# Usage Guide

How to interact with the Telegram-Qwen agent on a daily basis.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with feature overview |
| `/help` | Detailed help with usage examples |
| `/reset` | Clear your conversation history |
| `/status` | Bot uptime, Qwen health, memory and CPU stats |
| `/tasks` | List your active, pending, and failed tasks |
| `/resume [task_id]` | Resume a checkpointed or failed task |
| `/selfupdate` | Force-restart the bot (useful after code changes) |

## Messaging

Simply send any message and the agent will process it using Qwen. The agent can:

- Answer questions using its training data
- Search the web for current information
- Read web pages and extract content
- Read/write files on the host system
- Execute shell commands
- Run Python code
- Modify its own source code

### Examples

```
You: What's the weather in Mumbai today?
Bot: [Searches the web, reads a weather page, and responds]

You: List all Python files in my project
Bot: [Runs `find . -name "*.py"` and shows results]

You: Create a Python script that downloads the top HN stories
Bot: [Writes a script, runs it, shows output]
```

## Tools

The agent has 9 built-in tools:

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `WEB_SEARCH` | Search via DuckDuckGo | "Search for Python 3.14 release date" |
| `WEB_READ` | Fetch and parse a URL | "Read https://example.com" |
| `FILE_READ` | Read any file | "Show me /etc/hosts" |
| `FILE_WRITE` | Write/create files | "Create a script that..." |
| `LIST_FILES` | List directory contents | "What's in my Downloads folder?" |
| `EXEC` | Execute shell commands | "Run `git status`" |
| `PYTHON` | Execute Python code | "Calculate the first 100 primes" |
| `SELF_MODIFY` | Edit bot source code | "Add a new /ping command" |
| `SELF_RESTART` | Restart the bot | "Restart yourself" |

## Task System

Every message creates a tracked **Task**:

1. The task gets a unique ID and starts as `PENDING`
2. During execution, up to **15 tool calls** can be chained
3. State is **checkpointed** after each tool call
4. If something fails, the task moves to `CHECKPOINT` status
5. Use `/tasks` to see all tasks and `/resume <id>` to continue

### Long-Running Tasks

The agent supports hour-long tasks:
- Individual Qwen calls timeout at 10 minutes
- Failed calls retry 3 times with exponential backoff (5s → 15s → 45s)
- Progress updates are sent during long operations
- If the bot crashes, tasks can be resumed from the last checkpoint

## Conversation Memory

- Each user gets persistent conversation history stored in `data/conversations/`
- History is automatically loaded when you message the bot
- Old messages are summarized when history exceeds the configured limit
- Use `/reset` to clear your history and start fresh