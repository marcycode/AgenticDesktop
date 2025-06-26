import pyautogui
import webbrowser
import time
import subprocess
import os
import shutil
import glob
import platform
import sys

selected_file = None  # For select_file/locate_file action

def get_os_type():
    """Detect the operating system type"""
    return platform.system().lower()

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
            pyautogui.typewrite(msg)
        elif action == "press":
            key = step.get("key", "enter")
            pyautogui.press(key)
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
