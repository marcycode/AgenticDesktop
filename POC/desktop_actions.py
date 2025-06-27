import pyautogui
import time

# Only allow simulated keyboard and mouse actions
# All high-level actions are removed

# Action format examples:
# {"action": "type", "text": "hello world"}
# {"action": "press", "keys": ["command", "t"]}  # For Cmd+T (new tab on macOS)
# {"action": "mouse", ...}

# Map LLM key names to pyautogui key names
KEY_MAP = {
    'command': 'command',  # pyautogui uses 'command' for macOS
    'cmd': 'command',
    'ctrl': 'ctrl',
    'control': 'ctrl',
    'alt': 'alt',
    'option': 'option',
    'shift': 'shift',
    # Add more aliases if needed
}

def execute_steps(steps):
    if isinstance(steps, str):
        print("[!] Steps not structured.\n", steps)
        return
    for step in steps:
        action = step.get("action", "").lower()
        if action == "type":
            msg = step.get("text", "")
            delay = step.get("delay", 2)
            time.sleep(delay)  # Give time for focus
            pyautogui.typewrite(msg)
        elif action == "press":
            keys = step.get("keys")
            print("KEYS HERE", keys)
            if isinstance(keys, str):
                keys = [keys]
            if keys and isinstance(keys, list):
                # Map keys to pyautogui names
                mapped_keys = [KEY_MAP.get(k.lower(), k.lower()) for k in keys]
                print(f"[Agent] Pressing keys: {mapped_keys}")
                pyautogui.hotkey(*mapped_keys)
            else:
                print(f"[!] 'press' action missing or invalid 'keys': {step}")
        elif action == "mouse":
            x = step.get("x")
            y = step.get("y")
            button = step.get("button", "left")
            clicks = step.get("clicks", 1)
            interval = step.get("interval", 0.0)
            if x is not None and y is not None:
                pyautogui.click(x=x, y=y, clicks=clicks, interval=interval, button=button)
            else:
                print(f"[!] Mouse action missing coordinates: {step}")
        else:
            print(f"[!] Unknown or unsupported action: {action} | step: {step}")
