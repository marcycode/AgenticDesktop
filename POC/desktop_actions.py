import pyautogui
import time

# Only allow simulated keyboard and mouse actions
# All high-level actions are removed

# Action format examples:
# {"action": "type", "text": "hello world"}
# {"action": "press", "keys": ["command", "t"]}  # For Cmd+T (new tab on macOS)
# {"action": "click_text", "target": "text to click"}

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

def find_text_coordinates(target_text, ocr_annotations):
    """Find coordinates for a text target using OCR annotations"""
    if not ocr_annotations:
        print(f"[Debug] No OCR annotations available for target: '{target_text}'")
        return None, None
    
    target_text = target_text.strip()
    print(f"[Debug] Looking for target text: '{target_text}'")
    print(f"[Debug] Available OCR elements: {len(ocr_annotations)}")
    
    # Try exact match first
    for ann in ocr_annotations:
        if ann['text'].strip() == target_text:
            print(f"[Debug] Found exact match: '{ann['text']}' at ({ann['x']}, {ann['y']})")
            return ann['x'], ann['y']
    
    # Try case-insensitive exact match
    for ann in ocr_annotations:
        if ann['text'].strip().lower() == target_text.lower():
            print(f"[Debug] Found case-insensitive exact match: '{ann['text']}' at ({ann['x']}, {ann['y']})")
            return ann['x'], ann['y']
    
    # Try partial match (target text is contained in annotation)
    for ann in ocr_annotations:
        if target_text.lower() in ann['text'].strip().lower():
            print(f"[Debug] Found partial match (target in annotation): '{ann['text']}' contains '{target_text}' at ({ann['x']}, {ann['y']})")
            return ann['x'], ann['y']
    
    # Try reverse partial match (annotation text is contained in target)
    for ann in ocr_annotations:
        if ann['text'].strip().lower() in target_text.lower():
            print(f"[Debug] Found partial match (annotation in target): '{target_text}' contains '{ann['text']}' at ({ann['x']}, {ann['y']})")
            return ann['x'], ann['y']
    
    # Show what we have for debugging
    print(f"[Debug] No match found for '{target_text}'. Available elements:")
    for i, ann in enumerate(ocr_annotations[:10]):  # Show first 10
        print(f"  {i+1}. '{ann['text']}' at ({ann['x']}, {ann['y']})")
    
    return None, None

def test_click_coordinates(x, y, text="test"):
    """Test function to debug coordinate clicking"""
    print(f"[Debug] Attempting to click '{text}' at coordinates ({x}, {y})")
    
    # Get current mouse position
    current_x, current_y = pyautogui.position()
    print(f"[Debug] Current mouse position: ({current_x}, {current_y})")
    
    # Move mouse to target position
    pyautogui.moveTo(x, y, duration=0.5)
    
    # Get new mouse position
    new_x, new_y = pyautogui.position()
    print(f"[Debug] Mouse moved to: ({new_x}, {new_y})")
    
    # Click
    pyautogui.click()
    print(f"[Debug] Clicked at ({new_x}, {new_y})")

def execute_steps(steps, ocr_annotations=None):
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
        elif action == "click_text":
            target_text = step.get("target", "")
            if not target_text:
                print(f"[!] 'click_text' action missing 'target': {step}")
                continue
            
            if not ocr_annotations:
                print(f"[!] No OCR annotations available for click_text action: {step}")
                continue
            
            x, y = find_text_coordinates(target_text, ocr_annotations)
            if x is not None and y is not None:
                print(f"[Agent] Clicking text '{target_text}' at coordinates ({x}, {y})")
                pyautogui.click(x=x, y=y)
            else:
                print(f"[!] Could not find text '{target_text}' in OCR annotations")
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
