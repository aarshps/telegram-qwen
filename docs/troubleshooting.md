# Troubleshooting

Common issues and solutions for the Telegram-Qwen Bridge.

## Common Issues

### Bot Not Responding

**Symptoms**: The bot doesn't respond to any commands or messages.

**Possible Causes and Solutions**:
1. **Invalid bot token**:
   - Verify the `TELEGRAM_BOT_TOKEN` in your `.env` file
   - Regenerate the token from [@BotFather](https://t.me/BotFather) if needed
   - Restart the bot after updating the token

2. **Network connectivity issues**:
   - Check your internet connection
   - Verify that the bot can reach Telegram servers
   - Check firewall settings

3. **Bot not started properly**:
   - Ensure the Python script is running
   - Check for any error messages in the console
   - Verify all dependencies are installed

### Authorization Errors

**Symptoms**: Receiving "🔒 Access denied" message even when you should be authorized.

**Possible Causes and Solutions**:
1. **Incorrect TELEGRAM_ADMIN_ID**:
   - Send `/id` command to your bot to get the correct chat ID
   - Update the `TELEGRAM_ADMIN_ID` in your `.env` file
   - Restart the bot after updating

2. **Environment not loaded**:
   - Ensure the `.env` file is in the correct directory
   - Verify that `python-dotenv` is installed and working
   - Check that the bot is looking for the right environment variable

### Command Execution Failures

**Symptoms**: Commands fail to execute or return errors.

**Possible Causes and Solutions**:
1. **Command not found**:
   - Verify the command exists on your system
   - Check command spelling and syntax
   - Consider platform differences (Windows vs Unix commands)

2. **Permission denied**:
   - Run the bot with appropriate user privileges
   - Check file/folder permissions
   - Verify the user running the bot has necessary access rights

3. **Timeout errors**:
   - Increase the `COMMAND_TIMEOUT` value in the code
   - Simplify the command or break it into smaller parts
   - Check if the command is hanging or waiting for input

### Qwen Integration Issues

**Symptoms**: Qwen doesn't respond or returns errors.

**Possible Causes and Solutions**:
1. **Qwen CLI not installed**:
   - Install Qwen: `pip install qwen-cli`
   - Verify installation: `qwen --help`
   - Check that Qwen is in your PATH

2. **Qwen timeout**:
   - Increase the `QWEN_TIMEOUT` value in the code
   - Check if Qwen is responding to direct commands
   - Verify system resources (memory, CPU)

3. **Prompt formatting issues**:
   - Check for special characters that might interfere
   - Verify the system prompt format hasn't been accidentally modified

## Platform-Specific Issues

### Windows Issues

1. **"Command not recognized" errors**:
   - The bot automatically prefixes commands with `cmd /c` on Windows
   - Try using full paths to executables if needed
   - Check that the command exists in your PATH

2. **Encoding issues**:
   - Command output might have encoding problems
   - The bot tries both UTF-8 and CP850 encoding
   - Check the output in the `audit.log` file

### macOS/Linux Issues

1. **Permission errors**:
   - Ensure the bot has necessary file permissions
   - Check if running with appropriate user privileges
   - Verify file ownership and access rights

2. **PATH issues**:
   - Commands might not be found if not in PATH
   - Use full paths to executables
   - Check that the environment is properly set up

## Debugging Steps

### Enable Detailed Logging

1. Modify the logging level in the code:
   ```python
   logging.basicConfig(
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       level=logging.DEBUG  # Change from INFO to DEBUG
   )
   ```

2. Restart the bot and reproduce the issue
3. Check the console output for detailed error information

### Test Individual Components

1. **Test Telegram connection**:
   ```bash
   curl "https://api.telegram.org/bot<BOT_TOKEN>/getMe"
   ```

2. **Test Qwen**:
   ```bash
   echo "Hello" | qwen
   ```

3. **Test environment variables**:
   Create a simple test script to verify environment loading

### Check Log Files

1. **Audit log**: Check `audit.log` for recorded activities
2. **Console output**: Look for error messages in the terminal
3. **System logs**: Check system logs for any related errors

## Performance Issues

### Slow Response Times

1. **System resources**: Check CPU and memory usage
2. **Network latency**: Verify internet connection quality
3. **Qwen processing**: Large prompts may take longer to process

### High Resource Usage

1. **Memory leaks**: Restart the bot periodically
2. **Long-running processes**: Check for stuck commands
3. **Large history**: Consider clearing chat history with `/reset`

## Verification Steps

### After Making Changes

1. **Restart the bot**: Stop and start the bot to reload configurations
2. **Test basic functionality**: Send `/start` and `/id` commands
3. **Verify environment**: Check that all environment variables are loaded
4. **Test command execution**: Try a simple command like `/exec echo hello`

### Before Reporting Issues

1. **Check prerequisites**: Ensure all requirements are met
2. **Update code**: Pull the latest version from the repository
3. **Clean installation**: Try a fresh installation in a new directory
4. **Isolate the problem**: Determine if it's a configuration or code issue

## Getting Help

### Useful Information to Include

When seeking help, provide:

- Operating system and version
- Python version (`python --version`)
- Error messages from the console
- Steps to reproduce the issue
- Configuration details (without sensitive information)
- Recent changes made to the code or configuration

### Resources

- Check the [GitHub Issues](https://github.com/aarshps/telegram-qwen/issues) page
- Review the documentation in the `docs/` directory
- Verify your setup against the installation guide