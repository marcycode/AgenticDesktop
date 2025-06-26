# 🖥️ Virtual Desktop Capture for AgenticDesktop

AgenticDesktop now supports capturing and streaming from different virtual desktops across **Linux**, **Windows**, and **macOS**!

## 🚀 Features

- **Multi-Platform Support**: Works on Linux (GNOME, KDE, XFCE, etc.), Windows 10/11, and macOS
- **Virtual Desktop Detection**: Automatically detects available virtual desktops/workspaces/spaces
- **Real-time Streaming**: Stream from any virtual desktop at 10 FPS
- **Desktop Switching**: Programmatically switch between virtual desktops
- **Smart Capture**: Temporarily switch to target desktop for capture, then switch back

## 📋 Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install System Dependencies

Run the setup script to install platform-specific dependencies:

```bash
python install_virtual_desktop.py
```

**Or install manually:**

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install wmctrl xdotool python3-tk
```

#### Linux (Fedora/RHEL/CentOS):
```bash
sudo dnf install wmctrl xdotool tkinter
```

#### Linux (Arch):
```bash
sudo pacman -S wmctrl xdotool tk
```

#### Windows:
```bash
pip install pywin32
```

#### macOS:
```bash
pip install pyobjc-core pyobjc-framework-Cocoa
```

## 🖥️ Platform-Specific Support

### Linux Support

| Desktop Environment | Virtual Desktops | Switch Support | Notes |
|-------------------|------------------|----------------|--------|
| **GNOME** | ✅ Workspaces | ✅ Yes | Uses `gsettings` and `wmctrl` |
| **KDE Plasma** | ✅ Virtual Desktops | ✅ Yes | Uses `qdbus` and KWin API |
| **XFCE** | ✅ Workspaces | ✅ Yes | Uses `wmctrl` |
| **MATE** | ✅ Workspaces | ✅ Yes | Uses `wmctrl` |
| **Cinnamon** | ✅ Workspaces | ✅ Yes | Uses `wmctrl` |
| **i3/Sway** | ⚠️ Limited | ⚠️ Limited | May require custom config |

### Windows Support

| Version | Virtual Desktops | Switch Support | Notes |
|---------|-----------------|----------------|--------|
| **Windows 10** | ✅ Task View | ✅ Yes | Uses Win+Tab navigation |
| **Windows 11** | ✅ Task View | ✅ Yes | Enhanced Task View support |
| **Windows 8.1** | ❌ No | ❌ No | No virtual desktop support |

### macOS Support

| Version | Spaces | Switch Support | Notes |
|---------|--------|----------------|--------|
| **macOS 10.7+** | ✅ Mission Control | ✅ Yes | Uses AppleScript |
| **macOS 12+** | ✅ Stage Manager | ✅ Yes | Enhanced support |

## 🔧 How It Works

### 1. Virtual Desktop Detection

The system automatically detects:
- **Linux**: Uses desktop environment specific APIs (GNOME Shell, KWin, wmctrl)
- **Windows**: Uses PowerShell and Windows API calls
- **macOS**: Uses AppleScript and Mission Control APIs

### 2. Screen Capture Strategies

#### Current Desktop (Default)
- Direct capture using `mss` library
- Fastest and most reliable method

#### Non-Active Desktop
- **Method 1**: Temporarily switch to target desktop, capture, switch back
- **Method 2**: Background capture (when supported by OS)
- **Method 3**: Application window enumeration and capture

### 3. Desktop Switching

- **Linux**: `wmctrl -s <desktop_id>` or DE-specific commands
- **Windows**: Keyboard shortcuts (Win+Ctrl+Left/Right) or Task View navigation
- **macOS**: AppleScript to change current Space

## 🎮 Usage

### Web UI

1. **Start AgenticDesktop Web UI**:
   ```bash
   python run_web.py
   ```

2. **Access Desktop View**:
   - Click "📺 Desktop" button
   - Select virtual desktop from dropdown
   - Start streaming

3. **Switch Virtual Desktops**:
   - Use dropdown to select different desktop
   - Stream updates automatically
   - Desktop switching happens in background

### API Endpoints

#### Get Virtual Desktops
```http
GET /api/virtual_desktops
```

Response:
```json
{
  "desktops": [
    {"id": 0, "name": "Workspace 1", "active": true},
    {"id": 1, "name": "Workspace 2", "active": false}
  ],
  "os_type": "linux",
  "desktop_environment": "gnome"
}
```

#### Switch Desktop
```http
POST /api/switch_desktop
Content-Type: application/json

{"desktop_id": 1}
```

### SocketIO Events

#### Start Streaming Specific Desktop
```javascript
socket.emit('start_desktop_stream', {desktop_id: 1});
```

#### Change Streaming Desktop
```javascript
socket.emit('change_stream_desktop', {desktop_id: 2});
```

## 🔧 Configuration

### Performance Tuning

Edit `virtual_desktop.py` to adjust:

```python
# Capture frequency (FPS)
time.sleep(0.1)  # 10 FPS (change to 0.05 for 20 FPS)

# Image quality
img.save(buffer, format='JPEG', quality=85)  # 85% quality

# Image size
if width > 1280:  # Max width 1280px
```

### Desktop Environment Specific Settings

#### GNOME
```bash
# Enable workspace switching animations
gsettings set org.gnome.desktop.wm.preferences workspace-animations true

# Set number of workspaces
gsettings set org.gnome.desktop.wm.preferences num-workspaces 4
```

#### KDE
```bash
# Configure virtual desktops
qdbus org.kde.KWin /KWin setNumberOfDesktops 4
```

## 🐛 Troubleshooting

### Common Issues

#### Linux: "wmctrl command not found"
```bash
sudo apt-get install wmctrl  # Ubuntu/Debian
sudo dnf install wmctrl      # Fedora/RHEL
sudo pacman -S wmctrl        # Arch
```

#### Windows: "PowerShell access denied"
- Run as Administrator
- Enable PowerShell execution: `Set-ExecutionPolicy RemoteSigned`

#### macOS: "AppleScript permission denied"
- Grant accessibility permissions in System Preferences
- Add Terminal/Python to accessibility apps

#### Permission Issues
```bash
# Linux: Add user to required groups
sudo usermod -a -G video,input $USER

# macOS: Grant screen recording permissions
# System Preferences > Security & Privacy > Screen Recording
```

### Debug Mode

Enable debug logging:

```python
# In virtual_desktop.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing

Run the test script:
```bash
python install_virtual_desktop.py
```

This will:
- Install platform dependencies
- Test virtual desktop detection
- Test screen capture
- Report any issues

## 🔒 Security Notes

- **Screen Capture**: Requires screen recording permissions on macOS
- **Desktop Switching**: May require accessibility permissions
- **PowerShell**: Windows execution policy must allow scripts
- **X11**: Linux requires DISPLAY environment variable

## 🎯 Use Cases

### AI Agent Monitoring
- Watch AI agent work across multiple virtual desktops
- Monitor different applications simultaneously
- Debug automation scripts running on different workspaces

### Remote Desktop Management
- Manage multiple virtual desktops remotely
- Switch between work environments
- Monitor background processes

### Development & Testing
- Test applications on different virtual desktops
- Monitor development environments
- Debug cross-desktop workflows

## 🔮 Future Enhancements

- [ ] **Background Capture**: Capture without desktop switching
- [ ] **Multi-Monitor Support**: Capture from specific monitors
- [ ] **Custom Capture Regions**: Select specific screen areas
- [ ] **Recording**: Save desktop streams to video files
- [ ] **Wayland Support**: Full support for Wayland compositors
- [ ] **Performance Optimization**: GPU-accelerated capture

---

**Happy Virtual Desktop Streaming! 🚀** 