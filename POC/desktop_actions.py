import pyautogui
import webbrowser
import time
import subprocess
import os
import shutil
import glob

selected_file = None  # For select_file/locate_file action

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
            # Try to open the app using 'start' (Windows)
            try:
                if app:
                    # If a path is provided, use it directly
                    if os.path.exists(app):
                        subprocess.Popen(app)
                    else:
                        # Use 'start' to open by app name
                        subprocess.Popen(["cmd", "/c", "start", "", app])
                else:
                    print(f"[!] No app specified in step: {step}")
            except Exception as e:
                print(f"[!] Failed to open app '{app}': {e}")
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
                try:
                    os.startfile(filename)
                    print(f"[Open File] Opened file: {filename}")
                except Exception as e:
                    print(f"[!] Failed to open file: {e}")
            else:
                print("[!] open_file missing filename")
        else:
            print(f"[!] Unknown action: {action} | step: {step}")
