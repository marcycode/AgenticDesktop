# macOS Support for AgenticDesktop

## Overview

AgenticDesktop now includes full support for macOS, including workspace management, desktop capture, and input automation.

## Features

### 🖥️ Workspace Management
- **Spaces Detection**: Automatically detects macOS Spaces using AppleScript
- **Space Switching**: Switches between Spaces using multiple fallback methods
- **Agent Workspace**: Creates and manages dedicated Spaces for agent automation
- **Fallback Handling**: Gracefully handles cases where Space switching fails

### 📸 Desktop Capture
- **Screenshot Capture**: Uses macOS `screencapture` command for reliable screenshots
- **Base64 Encoding**: Converts screenshots to base64 for web streaming
- **Performance Optimization**: Resizes images for better streaming performance

### ⌨️ Input Automation
- **Text Typing**: Uses AppleScript for reliable text input
- **Key Pressing**: Supports common key combinations and special keys
- **Fallback Support**: Falls back to PyAutoGUI when AppleScript methods fail

## Technical Implementation

### Workspace Management
```python
# macOS Space detection
result = subprocess.run([
    'osascript', '-e', 
    'tell application "System Events" to get the index of current space of current desktop'
], capture_output=True, text=True, timeout=5)
```

### Space Switching Methods
1. **Direct Dock Click**: Clicks the Space button in the Dock
2. **Mission Control + Number**: Opens Mission Control and presses number key
3. **Control + Number**: Uses Control + number key combination

### Desktop Capture
```python
# macOS screenshot capture
result = subprocess.run(['screencapture', '-x', tmp.name], 
                      check=True, capture_output=True, timeout=10)
```

### Input Automation
```python
# macOS text typing
subprocess.run([
    'osascript', '-e',
    f'tell application "System Events" to keystroke "{escaped_text}"'
], check=True, timeout=10)
```

## Usage

### Testing macOS Support
Run the test script to verify all features work:
```bash
python test_macos_support.py
```

### Web Interface
The web interface automatically detects macOS and uses appropriate methods:
- Workspace creation and switching
- Desktop streaming
- Agent workspace management

### Command Line
The command-line interface works the same as on Linux:
```bash
python main.py
```

## Requirements

### System Requirements
- macOS 10.14 or later
- Python 3.7+
- Required permissions for accessibility features

### Python Dependencies
- `mss` (for fallback screenshot capture)
- `Pillow` (for image processing)
- `PyAutoGUI` (for fallback input methods)

### Permissions
The application may require accessibility permissions for:
- Input automation (keyboard/mouse control)
- Screen recording (for desktop capture)
- Automation (for AppleScript execution)

## Troubleshooting

### Common Issues

1. **"Failed to switch to agent workspace"**
   - Check if you have multiple Spaces enabled
   - Ensure accessibility permissions are granted
   - Try creating a new Space manually first

2. **Screenshot capture fails**
   - Grant screen recording permissions
   - Try running with `screencapture` manually first

3. **Input automation doesn't work**
   - Grant accessibility permissions in System Preferences
   - Check if any security software is blocking automation

### Debug Mode
Enable debug output by setting environment variable:
```bash
export AGENTIC_DEBUG=1
python app.py
```

## Limitations

- **Space Switching**: May not work reliably on all macOS versions
- **Input Automation**: Requires accessibility permissions
- **Screen Recording**: Requires explicit permission grants
- **Performance**: AppleScript methods may be slower than native Linux tools

## Future Improvements

- [ ] Better Space switching reliability
- [ ] Native macOS window management
- [ ] Improved error handling and recovery
- [ ] Performance optimizations
- [ ] Better permission handling 