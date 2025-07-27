# Application Agent

A secure, local desktop automation agent that interprets natural language commands via GPT and executes them safely on your local machine.

## 🚀 Features

- **Natural Language Processing**: Uses OpenRouter or OpenAI API to interpret commands
- **Safe Execution**: Multiple layers of safety checks and user confirmations
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Mouse & Keyboard Control**: Click, type, move mouse, press keys
- **Application Management**: Launch, close, and control applications
- **File Operations**: Read and write files with safety restrictions
- **System Tray Integration**: Background operation with hotkey activation
- **Comprehensive Logging**: All actions logged with timestamps
- **Modular Architecture**: Easy to extend and customize

## 🔧 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your API configuration:

```env
# For OpenRouter (recommended)
OPENROUTER_API_KEY=your_openrouter_api_key_here
GPT_MODEL=openai/gpt-4-turbo-preview

# OR for direct OpenAI API
OPENAI_API_KEY=your_openai_api_key_here
GPT_MODEL=gpt-4-turbo-preview
```

### 3. Run the Application

```bash
python main.py
```

Or for CLI mode:
```bash
python main.py --cli
```

## 🎯 Example Commands

- **"Open Chrome and go to YouTube"**
- **"Write a note that says 'Meeting at 3 PM' in Notepad"**
- **"Move the mouse to the top left and click"**
- **"Type 'Hello world' and hit enter"**
- **"Read me the contents of desktop.txt"**
- **"Click at coordinates 500, 300"**
- **"Press the enter key"**
- **"Wait for 2 seconds"**
- **"Scroll down 3 times"**

## 🛡️ Safety Features

### Multi-Layer Protection

1. **Application Whitelist**: Only approved applications can be launched
2. **File Extension Filtering**: Only safe file types can be written
3. **Directory Restrictions**: Prevents access to system directories
4. **Content Scanning**: Dangerous patterns blocked in text and files
5. **User Confirmations**: Critical actions require approval
6. **Action Logging**: Complete audit trail of all operations

### Safety Configuration

Edit `config.py` to customize safety settings:

```python
# Add applications to whitelist
WHITELISTED_APPLICATIONS = [
    'notepad.exe', 'code.exe', 'chrome.exe', 
    'firefox.exe', 'calculator.exe'
]

# Block dangerous keywords
DANGEROUS_KEYWORDS = [
    'format', 'delete', 'rm -rf', 'shutdown', 
    'kill', 'taskkill'
]
```

### Emergency Stop

- **Mouse Failsafe**: Move mouse to top-left corner to stop pyautogui
- **Hotkey**: Ctrl+C in terminal to stop CLI mode
- **GUI**: Close button or system tray quit option

## 🎮 Usage

### GUI Mode (Default)

1. **Main Window**: Enter commands and see results
2. **System Tray**: Right-click for quick access
3. **Global Hotkey**: `Ctrl+Shift+A` (configurable) for quick input
4. **Command History**: View and reuse previous commands
5. **Suggestions**: Get example commands based on context

### CLI Mode

```bash
python main.py --cli
```

Interactive command-line interface for headless operation.

### Hotkey Activation

With the GUI running, use the global hotkey (`Ctrl+Shift+A` by default) to quickly activate the agent from anywhere on your system.

## 📁 Project Structure

```
application_agent/
├── main.py                  # Entry point with GUI
├── gpt_interface.py         # GPT API communication
├── interpreter.py           # Command processing pipeline
├── actions.py               # Safe action execution
├── safety.py                # Security checks and confirmations
├── logger.py                # Comprehensive logging
├── config.py                # Configuration and settings
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create from .env.example)
└── README.md               # This file
```

## ⚙️ Configuration

### Environment Variables (.env)

```env
# API Configuration
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
GPT_MODEL=openai/gpt-4-turbo-preview

# Agent Settings
LOG_LEVEL=INFO
SAFETY_MODE=true
CONFIRMATION_REQUIRED=true
MAX_RETRY_ATTEMPTS=3

# Hotkey (modify as needed)
ACTIVATION_HOTKEY=ctrl+shift+a
```

### Safety Settings (config.py)

- **WHITELISTED_APPLICATIONS**: Applications that can be launched
- **DANGEROUS_KEYWORDS**: Blocked text patterns
- **SAFE_FILE_EXTENSIONS**: Allowed file types for writing
- **RESTRICTED_DIRECTORIES**: Protected system directories
- **ACTION_TIMEOUT**: Maximum time for action execution

## 📋 Action Types

| Action | Description | Example |
|--------|-------------|---------|
| `click` | Mouse click at coordinates | Click at (100, 200) |
| `type` | Type text | Type "Hello World" |
| `key_press` | Press keyboard keys | Press Enter |
| `open_app` | Launch application | Open Chrome |
| `close_app` | Close application | Close Notepad |
| `file_read` | Read file content | Read desktop.txt |
| `file_write` | Write to file | Write note to file |
| `mouse_move` | Move mouse cursor | Move to (300, 400) |
| `scroll` | Scroll up/down | Scroll down 3 times |
| `wait` | Pause execution | Wait 2 seconds |

## 🔍 Logging

All actions are logged to `logs/agent_log.txt` with:

- Timestamps
- User commands
- GPT responses
- Safety check results
- Action execution details
- Error information

### Log Levels

- **INFO**: Normal operations
- **WARNING**: Safety checks and important events
- **ERROR**: Failures and exceptions

## 🐛 Troubleshooting

### Common Issues

1. **"No API key configured"**
   - Ensure `.env` file exists with valid API key
   - Check API key has sufficient credits/permissions

2. **"pyautogui not available"**
   - Install missing dependencies: `pip install pyautogui`
   - On Linux: may need display server for GUI automation

3. **"Application not in whitelist"**
   - Add application to `WHITELISTED_APPLICATIONS` in `config.py`
   - Use exact executable name (e.g., 'chrome.exe' on Windows)

4. **Permission errors**
   - Run with appropriate permissions for system automation
   - Check file/directory permissions for read/write operations

### Debug Mode

Enable detailed logging:

```env
LOG_LEVEL=DEBUG
```

### Platform-Specific Notes

**Windows:**
- Applications may require full path or be in PATH
- Some actions may need administrator privileges

**Linux:**
- Install display automation dependencies
- May require X11 forwarding for remote sessions

**macOS:**
- Grant accessibility permissions in System Preferences
- Some applications may require specific permission prompts

## 🔒 Security Considerations

### What's Protected

- System files and directories
- Dangerous shell commands
- Unauthorized application launches
- Large file operations
- Malicious text patterns

### What's Not Protected

- The agent operates with your user permissions
- Physical access to the machine
- Malicious GPT responses (multiple validation layers help)
- Network-based attacks on the API

### Best Practices

1. **Use dedicated API keys** with limited scope
2. **Review confirmation dialogs** carefully
3. **Monitor logs** for unusual activity
4. **Keep whitelists restrictive** initially
5. **Test in safe environment** first

## 🚧 Extending the Agent

### Adding New Actions

1. Define action in `actions.py`:
```python
def _execute_new_action(self, action_data: Dict[str, Any]) -> Tuple[bool, str]:
    # Implementation here
    return True, "Success message"
```

2. Add validation in `safety.py`:
```python
def _validate_new_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
    # Safety checks here
    return True, "Validation passed"
```

3. Update GPT prompt in `gpt_interface.py` to include new action type

### Custom Safety Rules

Modify `config.py` to add custom safety rules:

```python
CUSTOM_DANGEROUS_PATTERNS = [
    r'custom_pattern_\d+',
    r'specific_command.*args'
]
```

## 📄 License

This project is provided as-is for educational and personal use. Please review and test thoroughly before using in production environments.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests for new functionality
4. Ensure all safety checks pass
5. Submit a pull request

## ⚠️ Disclaimer

This tool automates your computer based on AI interpretation of natural language. While multiple safety measures are in place, users are responsible for:

- Reviewing all actions before execution
- Understanding the commands they give
- Ensuring safe usage in their environment
- Backing up important data

Use at your own risk and always test in a safe environment first.