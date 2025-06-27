import os
import sys
import time
import subprocess
import shutil
import glob
import platform
import webbrowser

# Handle PyAutoGUI import on Wayland systems
pyautogui = None
try:
    # Check if we're on Wayland and set up X11 compatibility if needed
    from system_info import is_wayland
    if is_wayland():
        # For Wayland systems, we need to handle PyAutoGUI carefully
        # Set DISPLAY if not set (for XWayland compatibility)
        if 'DISPLAY' not in os.environ:
            os.environ['DISPLAY'] = ':0'
        
        # Disable PyAutoGUI's fail-safe (can cause issues on Wayland)
        os.environ['PYAUTOGUI_DISABLE_FAILSAFE'] = '1'
        
        print("[Desktop Actions] Wayland detected - configuring PyAutoGUI for XWayland compatibility")
    
    import pyautogui
    pyautogui.FAILSAFE = False  # Disable fail-safe for Wayland compatibility
    
except ImportError as e:
    print(f"[Desktop Actions] PyAutoGUI not available: {e}")
    print("[Desktop Actions] Some typing/clicking actions will be disabled")
    pyautogui = None
except Exception as e:
    print(f"[Desktop Actions] PyAutoGUI initialization failed: {e}")
    print("[Desktop Actions] Trying alternative approach...")
    
    # Try alternative input methods for Wayland
    try:
        # Try importing without mouseinfo
        import pyautogui
        pyautogui.FAILSAFE = False
    except Exception as e2:
        print(f"[Desktop Actions] Alternative PyAutoGUI import also failed: {e2}")
        print("[Desktop Actions] Using keyboard-only mode")
        pyautogui = None

selected_file = None  # For select_file/locate_file action

def get_os_type():
    """Detect the operating system type"""
    return platform.system().lower()

def wayland_type_text(text):
    """Type text using Wayland-compatible methods"""
    try:
        # Try using wtype (Wayland typing tool)
        subprocess.run(['wtype', text], check=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Try using ydotool (universal input tool)
        subprocess.run(['ydotool', 'type', text], check=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Try using xdotool via XWayland
        subprocess.run(['xdotool', 'type', text], check=True, timeout=10)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False

def wayland_press_key(key):
    """Press key using Wayland-compatible methods"""
    try:
        # Try using wtype for key presses
        key_map = {
            'enter': 'Return',
            'return': 'Return',
            'space': 'space',
            'tab': 'Tab',
            'escape': 'Escape',
            'backspace': 'BackSpace',
            'delete': 'Delete'
        }
        wayland_key = key_map.get(key.lower(), key)
        subprocess.run(['wtype', '-k', wayland_key], check=True, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Try using ydotool for key presses
        subprocess.run(['ydotool', 'key', key], check=True, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Try using xdotool via XWayland
        subprocess.run(['xdotool', 'key', key], check=True, timeout=5)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return False

def open_application(app_name):
    """Cross-platform application opener with intelligent app detection"""
    os_type = get_os_type()
    
    try:
        # Try to use system info for smart app selection
        try:
            from system_info import get_best_app_for_task, detect_available_apps
            
            # Map common app requests to categories
            app_mappings = {
                'calculator': 'calculator',
                'calc': 'calculator',
                'chrome': 'browser',
                'browser': 'browser',
                'firefox': 'browser',
                'editor': 'text_editor',
                'notepad': 'text_editor',
                'terminal': 'terminal',
                'console': 'terminal',
                'file-manager': 'file_manager',
                'files': 'file_manager',
                'nautilus': 'file_manager'
            }
            
            app_lower = app_name.lower()
            
            # Check if we can find a better app match
            for key, category in app_mappings.items():
                if key in app_lower or app_lower in key:
                    best_app = get_best_app_for_task(category)
                    if best_app:
                        print(f"[Smart App Selection] Using {best_app} for {app_name}")
                        app_name = best_app
                        break
        except ImportError:
            pass  # Fall back to manual detection
        
        if os_type == "windows":
            # Windows
            if os.path.exists(app_name):
                subprocess.Popen(app_name)
            else:
                subprocess.Popen(["cmd", "/c", "start", "", app_name])
        elif os_type == "darwin":
            # macOS
            if os.path.exists(app_name):
                subprocess.Popen(["open", app_name])
            else:
                subprocess.Popen(["open", "-a", app_name])
        else:
            # Linux and other Unix-like systems
            if os.path.exists(app_name):
                subprocess.Popen(["xdg-open", app_name])
            else:
                # Manual fallback for common apps
                common_apps = {
                    'calculator': ['gnome-calculator', 'kcalc', 'xcalc', 'galculator', 'qalculate-gtk'],
                    'chrome': ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'],
                    'firefox': ['firefox', 'firefox-esr'],
                    'editor': ['gedit', 'kate', 'mousepad', 'leafpad'],
                    'terminal': ['gnome-terminal', 'konsole', 'xterm', 'alacritty', 'terminator'],
                    'file-manager': ['nautilus', 'dolphin', 'thunar', 'pcmanfm', 'nemo'],
                }
                
                app_lower = app_name.lower()
                apps_to_try = [app_name]  # Try the direct name first
                
                # Add alternatives based on common mappings
                for key, app_list in common_apps.items():
                    if key in app_lower or app_lower in key:
                        apps_to_try.extend(app_list)
                
                # Try each application
                for app in apps_to_try:
                    try:
                        subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"[Open App] Successfully opened: {app}")
                        return
                    except FileNotFoundError:
                        continue
                
                # If nothing worked, try xdg-open as final fallback
                try:
                    subprocess.Popen(["xdg-open", app_name])
                    print(f"[Open App] Opened via xdg-open: {app_name}")
                except Exception:
                    raise Exception(f"Could not find or open application: {app_name}")
                
    except Exception as e:
        print(f"[!] Failed to open app '{app_name}': {e}")

def open_file_cross_platform(file_path):
    """Cross-platform file opener"""
    os_type = get_os_type()
    
    try:
        if os_type == "windows":
            os.startfile(file_path)
        elif os_type == "darwin":
            subprocess.Popen(["open", file_path])
        else:
            # Linux and other Unix-like systems
            subprocess.Popen(["xdg-open", file_path])
        
        print(f"[Open File] Opened file: {file_path}")
    except Exception as e:
        print(f"[!] Failed to open file: {e}")

def expand_user_path(path):
    # Expand ~, and map common folders like Downloads, Desktop, Documents
    if not path:
        return path
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        user_dir = os.path.expanduser('~')
        # Map common folders
        for folder in ["Downloads", "Desktop", "Documents", "Pictures", "Music", "Videos"]:
            if path.startswith(folder + os.sep) or path == folder:
                path = os.path.join(user_dir, path)
                break
    return os.path.abspath(path)

def execute_steps(steps):
    global selected_file
    if isinstance(steps, str):
        print("[!] Steps not structured.\n", steps)
        return
    for step in steps:
        action = step.get("action", "").lower()
        if action == "open_app":
            app = step.get("app", "")
            if app:
                open_application(app)
            else:
                print(f"[!] No app specified in step: {step}")
        elif action == "search":
            query = step.get("query", "")
            webbrowser.open(f"https://www.google.com/search?q={query}")
        elif action == "type":
            msg = step.get("text", "")
            time.sleep(2)
            
            # Try Wayland-compatible typing first, then fall back to PyAutoGUI
            try:
                from system_info import is_wayland
                if is_wayland():
                    if wayland_type_text(msg):
                        print(f"[Type] Wayland typing successful: {msg}")
                    else:
                        print(f"[Type] Wayland typing failed, trying PyAutoGUI fallback")
                        if pyautogui:
                            pyautogui.typewrite(msg)
                        else:
                            print(f"[Type] PyAutoGUI not available, skipping typing")
                else:
                    # X11 system, use PyAutoGUI
                    if pyautogui:
                        pyautogui.typewrite(msg)
                    else:
                        print(f"[Type] PyAutoGUI not available, skipping typing")
            except ImportError:
                # Fallback if system_info not available
                if pyautogui:
                    pyautogui.typewrite(msg)
                else:
                    print(f"[Type] PyAutoGUI not available, skipping typing")
                    
        elif action == "press":
            key = step.get("key", "enter")
            
            # Try Wayland-compatible key press first, then fall back to PyAutoGUI
            try:
                from system_info import is_wayland
                if is_wayland():
                    if wayland_press_key(key):
                        print(f"[Press] Wayland key press successful: {key}")
                    else:
                        print(f"[Press] Wayland key press failed, trying PyAutoGUI fallback")
                        if pyautogui:
                            pyautogui.press(key)
                        else:
                            print(f"[Press] PyAutoGUI not available, skipping key press")
                else:
                    # X11 system, use PyAutoGUI
                    if pyautogui:
                        pyautogui.press(key)
                    else:
                        print(f"[Press] PyAutoGUI not available, skipping key press")
            except ImportError:
                # Fallback if system_info not available
                if pyautogui:
                    pyautogui.press(key)
                else:
                    print(f"[Press] PyAutoGUI not available, skipping key press")
        elif action == "file_search":
            pattern = expand_user_path(step.get("pattern", "*"))
            results = glob.glob(pattern, recursive=True)
            print(f"[File Search] Found files: {results}")
        elif action == "file_copy":
            src = expand_user_path(step.get("src"))
            dst = expand_user_path(step.get("dst"))
            if src and dst:
                try:
                    shutil.copy(src, dst)
                    print(f"[File Copy] Copied {src} to {dst}")
                except Exception as e:
                    print(f"[!] File copy failed: {e}")
            else:
                print("[!] file_copy missing src or dst")
        elif action == "select_file":
            selected_file = expand_user_path(step.get("file_path"))
            print(f"[Select File] Selected file: {selected_file}")
        elif action == "locate_file":
            file_name = step.get("file_name")
            directory = expand_user_path(step.get("directory", "."))
            pattern = os.path.join(directory, "**", file_name) if file_name else os.path.join(directory, "**")
            results = glob.glob(pattern, recursive=True)
            if results:
                selected_file = results[0]
                print(f"[Locate File] Found: {selected_file}")
            else:
                selected_file = None
                print(f"[Locate File] File not found: {file_name} in {directory}")
        elif action == "move_file":
            src = expand_user_path(step.get("src") or selected_file)
            dst = expand_user_path(step.get("destination_path"))
            # Try to construct src and dst if not provided
            if not src and step.get("source_directory") and step.get("file_name"):
                src = os.path.join(expand_user_path(step["source_directory"]), step["file_name"])
            if not dst and step.get("destination_directory") and step.get("file_name"):
                dst = os.path.join(expand_user_path(step["destination_directory"]), step["file_name"])
            if src and dst:
                try:
                    shutil.move(src, dst)
                    print(f"[Move File] Moved {src} to {dst}")
                except Exception as e:
                    print(f"[!] File move failed: {e}")
            else:
                print("[!] move_file missing src or destination_path")
        elif action == "navigate":
            directory = expand_user_path(step.get("directory"))
            if directory:
                try:
                    os.chdir(directory)
                    print(f"[Navigate] Changed working directory to: {directory}")
                except Exception as e:
                    print(f"[!] Failed to change directory: {e}")
            else:
                print("[!] navigate missing directory")
        elif action == "open_file":
            filename = expand_user_path(step.get("filename") or step.get("file_path"))
            if filename:
                open_file_cross_platform(filename)
            else:
                print("[!] open_file missing filename")
        else:
            print(f"[!] Unknown action: {action} | step: {step}")
