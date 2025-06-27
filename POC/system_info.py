import platform
import subprocess
import os
import shutil

def get_system_info():
    """Get comprehensive system information for context-aware automation"""
    info = {
        'os': platform.system().lower(),
        'os_version': platform.version(),
        'architecture': platform.architecture()[0],
        'desktop_environment': detect_desktop_environment(),
        'display_server': detect_display_server(),
        'available_apps': detect_available_apps(),
        'shell': os.environ.get('SHELL', 'unknown'),
        'home_dir': os.path.expanduser('~'),
        'common_dirs': get_common_directories()
    }
    return info

def detect_desktop_environment():
    """Detect the desktop environment on Linux"""
    if platform.system().lower() != 'linux':
        return None
    
    desktop_env = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    if desktop_env:
        return desktop_env
    
    # Fallback detection
    for env_var in ['DESKTOP_SESSION', 'GDMSESSION']:
        if env_var in os.environ:
            return os.environ[env_var].lower()
    
    return 'unknown'

def detect_display_server():
    """Detect if we're running on X11 or Wayland"""
    session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
    if session_type:
        return session_type
    
    # Fallback: check if WAYLAND_DISPLAY is set
    if os.environ.get('WAYLAND_DISPLAY'):
        return 'wayland'
    
    # Fallback: check if DISPLAY is set (X11)
    if os.environ.get('DISPLAY'):
        return 'x11'
    
    return 'unknown'

def is_wayland():
    """Check if we're running on Wayland"""
    return detect_display_server() == 'wayland'

def detect_available_apps():
    """Detect which applications are available on the system"""
    apps = {}
    
    # Common app categories and their possible names
    app_categories = {
        'calculator': ['gnome-calculator', 'kcalc', 'xcalc', 'galculator', 'qalculate-gtk'],
        'browser': ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'firefox', 'firefox-esr'],
        'text_editor': ['gedit', 'kate', 'mousepad', 'leafpad', 'nano', 'vim', 'emacs'],
        'terminal': ['gnome-terminal', 'konsole', 'xterm', 'alacritty', 'terminator', 'kitty'],
        'file_manager': ['nautilus', 'dolphin', 'thunar', 'pcmanfm', 'nemo'],
        'image_viewer': ['eog', 'gwenview', 'ristretto', 'feh'],
        'video_player': ['vlc', 'mpv', 'totem', 'dragon'],
        'office': ['libreoffice', 'writer', 'calc', 'impress']
    }
    
    for category, app_list in app_categories.items():
        available = []
        for app in app_list:
            if shutil.which(app):
                available.append(app)
        apps[category] = available
    
    return apps

def get_common_directories():
    """Get common user directories"""
    home = os.path.expanduser('~')
    common_dirs = {
        'home': home,
        'desktop': os.path.join(home, 'Desktop'),
        'downloads': os.path.join(home, 'Downloads'),
        'documents': os.path.join(home, 'Documents'),
        'pictures': os.path.join(home, 'Pictures'),
        'music': os.path.join(home, 'Music'),
        'videos': os.path.join(home, 'Videos'),
    }
    
    # Check which directories actually exist
    existing_dirs = {}
    for name, path in common_dirs.items():
        if os.path.exists(path):
            existing_dirs[name] = path
    
    return existing_dirs

def get_best_app_for_task(task_type):
    """Get the best available application for a specific task"""
    apps = detect_available_apps()
    
    if task_type in apps and apps[task_type]:
        return apps[task_type][0]  # Return the first available app
    
    return None



def print_system_summary():
    """Print a summary of system capabilities"""
    info = get_system_info()
    
    print("🖥️  System Information:")
    print(f"   OS: {info['os'].title()} ({info['architecture']})")
    if info['desktop_environment']:
        print(f"   Desktop: {info['desktop_environment'].title()}")
    
    print("\n📱 Available Applications:")
    for category, apps in info['available_apps'].items():
        if apps:
            print(f"   {category.replace('_', ' ').title()}: {', '.join(apps[:3])}")
    
    print(f"\n📁 Common Directories:")
    for name, path in info['common_dirs'].items():
        print(f"   {name.title()}: {path}")

if __name__ == "__main__":
    print_system_summary() 