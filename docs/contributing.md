# Contributing

Thank you for your interest in contributing to the Telegram-Qwen Bridge! This document outlines how to participate in the project.

## Code of Conduct

Please follow our community guidelines:
- Be respectful and inclusive
- Provide constructive feedback
- Welcome newcomers
- Focus on improving the project

## How to Contribute

### Reporting Bugs

When reporting bugs, please include:
- A clear title and description
- Steps to reproduce the issue
- Expected vs. actual behavior
- Environment information (OS, Python version, etc.)
- Any relevant error messages or logs

### Suggesting Features

Feature suggestions are welcome! Please:
- Explain the problem the feature solves
- Describe the proposed solution
- Consider the impact on existing functionality
- Discuss potential implementation approaches

### Improving Documentation

Documentation improvements are highly valued:
- Fix typos or unclear explanations
- Add examples or tutorials
- Improve existing documentation
- Translate documentation to other languages

### Contributing Code

#### Prerequisites

- Python 3.8+
- Git
- A GitHub account
- Understanding of the project architecture

#### Setting Up Your Environment

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/telegram-qwen.git
   cd telegram-qwen
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install qwen-cli
   ```
5. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

#### Making Changes

1. Follow the existing code style
2. Write clear, descriptive commit messages
3. Add tests if applicable
4. Update documentation as needed
5. Ensure your changes don't break existing functionality

#### Code Style

- Follow PEP 8 guidelines
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Use type hints where appropriate

#### Testing Your Changes

1. Test manually by running the bot
2. Verify that existing functionality still works
3. Test your new functionality thoroughly
4. Check edge cases and error conditions

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Update documentation as needed
3. Squash commits if you have many small changes
4. Write a clear pull request description
5. Link to any related issues
6. Wait for review and address feedback

### Pull Request Guidelines

- Keep pull requests focused on a single issue/feature
- Follow the template if one exists
- Include tests for new functionality
- Update documentation for new features
- Ensure CI checks pass

## Development Workflow

### Branch Strategy

- `main`: Stable, production-ready code
- `feature/*`: New features in development
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates

### Commit Messages

Follow the conventional commit format:
```
type(scope): description

body (optional)

footer (optional)
```

Examples:
- `feat(bot): add new command handler`
- `fix(auth): resolve admin ID validation`
- `docs(readme): update installation instructions`
- `refactor(core): improve error handling`

### Issue Labels

Issues are categorized using labels:
- `bug`: Something isn't working
- `enhancement`: New feature or improvement
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed

## Project Structure

```
telegram-qwen/
├── telegram_qwen_bridge.py    # Main application
├── tools/
│   └── web_reader.py         # Web content extraction tool
├── docs/                     # Documentation files
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .gitignore              # Git ignore rules
├── README.md               # Main documentation
└── LICENSE                 # License information
```

## Architecture Overview

The application consists of:

1. **Telegram Interface**: Handles communication with Telegram API
2. **Authorization Layer**: Verifies user permissions
3. **Qwen Integration**: Processes requests with Qwen AI
4. **Command Execution**: Runs shell commands securely
5. **History Management**: Maintains conversation context
6. **Logging System**: Tracks all activities

## Security Considerations

When contributing code, consider:
- Input validation and sanitization
- Authorization and access controls
- Secure handling of sensitive data
- Protection against injection attacks
- Privacy implications of new features

## Getting Help

If you need help:
- Check the existing documentation
- Look at closed issues for similar problems
- Ask questions in pull request discussions
- Examine existing code for patterns to follow

## Recognition

Contributors will be recognized in:
- Release notes
- The project's README
- GitHub contributors list

Thank you for contributing to the Telegram-Qwen Bridge!