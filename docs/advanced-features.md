# Advanced Features

Explore the advanced capabilities and customization options of the Telegram-Qwen Bridge.

## Custom System Prompts

### Modifying Qwen's Behavior

The bot's behavior is guided by a system prompt in the `handle_message` function. You can customize this to:

1. **Change available tools**:
   ```python
   base_system_instruction = (
       "TASK: You are a specialized system administration assistant.\n"
       "INPUT: Chat History + New Request\n"
       "OUTPUT: Standard [EXEC] formatted command OR Final Answer.\n\n"
       "AVAILABLE TOOLS:\n"
       "1. System Monitoring: [EXEC]top[/EXEC] or [EXEC]htop[/EXEC]\n"
       "2. Disk Usage: [EXEC]df -h[/EXEC] or [EXEC]du -sh *[/EXEC]\n"
       "3. Process Management: [EXEC]ps aux[/EXEC] or [EXEC]kill PID[/EXEC]\n"
       "4. Web Research: [EXEC]python tools/web_reader.py <URL>[/EXEC]\n"
       "RULES:\n"
       "1. Output [EXEC]...[/EXEC] for actions.\n"
       "2. Completed? Output Final Answer as text.\n"
       "3. Prioritize system stability.\n\n"
   )
   ```

2. **Adjust response format expectations**:
   - Modify how Qwen should format its responses
   - Change the delimiter for executable commands
   - Specify different output formats

### Context Window Management

The bot manages conversation history to maintain context:

- **MAX_HISTORY_MESSAGES**: Controls how many messages are kept in context
- **Session History**: Temporary history for the current interaction loop
- **Global History**: Persistent history saved to `chat_history.json`

## Extending Bot Functionality

### Adding New Commands

You can add custom commands by creating handler functions and registering them:

```python
async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Custom command handler."""
    # Your command logic here
    await update.message.reply_text("Custom command executed!")

# Register in main():
# app.add_handler(CommandHandler("custom", custom_command))
```

### Custom Tools for Qwen

Extend the tools available to Qwen by adding new scripts to the `tools/` directory:

1. Create a new Python script in the `tools/` directory
2. Ensure it accepts parameters from command line
3. Update the system prompt to include the new tool
4. Test the integration

### Event Hooks

Add custom logic at different points in the bot's operation:

- Before command execution
- After receiving Qwen responses
- During error handling
- When saving/loading history

## Performance Tuning

### Timeout Configuration

Adjust timeout values based on your needs:

- `COMMAND_TIMEOUT`: Time to wait for command execution (default: 60s)
- `QWEN_TIMEOUT`: Time to wait for Qwen responses (default: 120s)
- `MAX_TURN_COUNT`: Maximum iterations in the ReAct loop (default: 10)

### Message Sizing

Optimize message handling for your use case:

- `MAX_MESSAGE_LENGTH`: Maximum length of messages sent to Telegram (4096)
- `MAX_OUTPUT_LENGTH`: Maximum length of command output stored (8000)
- History pruning settings

## Integration Options

### External Services

Integrate with external services by extending the tools:

1. **Database queries**: Create tools to query databases
2. **API calls**: Develop tools to interact with web APIs
3. **File transfers**: Add capabilities for file uploads/downloads
4. **Notification systems**: Integrate with email or other notification services

### Multiple Admin Support

Currently, the bot supports a single admin via `TELEGRAM_ADMIN_ID`. You can extend this to support multiple admins:

```python
AUTHORIZED_USERS = os.environ.get('TELEGRAM_ADMIN_IDS', '').split(',')
user_id = str(update.effective_chat.id)
if user_id not in AUTHORIZED_USERS:
    # Handle unauthorized access
```

## Security Enhancements

### Command Filtering

Implement additional security by filtering dangerous commands:

```python
DANGEROUS_COMMANDS = ['rm', 'format', 'del', 'shutdown', 'reboot']

def is_dangerous_command(command):
    for dangerous_cmd in DANGEROUS_COMMANDS:
        if command.startswith(dangerous_cmd):
            return True
    return False
```

### Rate Limiting

Add rate limiting to prevent abuse:

```python
from collections import defaultdict
import time

user_requests = defaultdict(list)

def check_rate_limit(user_id):
    now = time.time()
    user_requests[user_id] = [req_time for req_time in user_requests[user_id] 
                              if now - req_time < 60]  # Last minute
    
    if len(user_requests[user_id]) > 10:  # Max 10 requests per minute
        return False
    user_requests[user_id].append(now)
    return True
```

## Customization Examples

### Specialized Assistant

Create a specialized assistant for specific tasks:

```python
# For a DevOps-focused assistant
base_system_instruction = (
    "TASK: You are a DevOps assistant managing deployment environments.\n"
    "INPUT: Chat History + New Request\n"
    "OUTPUT: Standard [EXEC] formatted command OR Final Answer.\n\n"
    "AVAILABLE TOOLS:\n"
    "1. Docker Management: [EXEC]docker ps[/EXEC], [EXEC]docker logs CONTAINER[/EXEC]\n"
    "2. Git Operations: [EXEC]git status[/EXEC], [EXEC]git pull[/EXEC]\n"
    "3. Service Status: [EXEC]systemctl status SERVICE[/EXEC]\n"
    "4. Resource Monitoring: [EXEC]top[/EXEC], [EXEC]df -h[/EXEC]\n"
    "RULES:\n"
    "1. Output [EXEC]...[/EXEC] for actions.\n"
    "2. Prioritize system stability and security.\n"
    "3. Confirm destructive actions before executing.\n\n"
)
```

### Multi-Language Support

Add support for multiple languages by detecting and responding appropriately:

```python
def detect_language(text):
    # Implement language detection
    pass

def get_localized_response(message_key, lang_code):
    # Return localized response based on language
    pass
```

## Monitoring and Analytics

### Enhanced Logging

Add custom logging for analytics:

```python
import json
from datetime import datetime

def log_interaction(user_id, command, response, success=True):
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_id': user_id,
        'command': command,
        'response_length': len(response),
        'success': success
    }
    
    with open('interaction_log.json', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
```

### Performance Metrics

Track performance metrics:

- Command execution times
- Qwen response times
- Error rates
- User engagement metrics

## Backup and Recovery

### Automated Backups

Set up automated backups of important data:

```python
import shutil
from datetime import datetime

def backup_chat_history():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"chat_history_backup_{timestamp}.json"
    shutil.copy(CHAT_HISTORY_FILE, backup_filename)
```

### Configuration Management

Store configuration in version-controlled files:

- Separate configuration files for different environments
- Template-based configuration generation
- Automated configuration validation

## Development Tips

### Testing Changes

1. Test in a safe environment first
2. Use a test Telegram bot for development
3. Implement gradual rollouts for new features
4. Monitor logs during testing

### Version Management

- Tag releases in git
- Maintain changelogs
- Document breaking changes
- Provide upgrade instructions