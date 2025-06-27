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
    'enter': 'enter',
    'return': 'return',
    'tab': 'tab',
    'space': 'space',
    'backspace': 'backspace',
    'delete': 'delete',
    'escape': 'escape',
    'esc': 'escape',
    'up': 'up',
    'down': 'down',
    'left': 'left',
    'right': 'right',
    'home': 'home',
    'end': 'end',
    'pageup': 'pageup',
    'pagedown': 'pagedown',
    'insert': 'insert',
    'f1': 'f1',
    'f2': 'f2',
    'f3': 'f3',
    'f4': 'f4',
    'f5': 'f5',
    'f6': 'f6',
    'f7': 'f7',
    'f8': 'f8',
    'f9': 'f9',
    'f10': 'f10',
    'f11': 'f11',
    'f12': 'f12',
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
    
    # Normalize text for comparison (remove extra spaces, lowercase)
    target_normalized = ' '.join(target_text.lower().split())
    
    # Try exact match first
    for ann in ocr_annotations:
        ann_text = ann['text'].strip()
        ann_normalized = ' '.join(ann_text.lower().split())
        if ann_normalized == target_normalized:
            print(f"[Debug] Found exact match: '{ann_text}' at ({ann['x']}, {ann['y']})")
            return ann['x'], ann['y']
    
    # Try case-insensitive exact match
    for ann in ocr_annotations:
        ann_text = ann['text'].strip()
        if ann_text.lower() == target_text.lower():
            print(f"[Debug] Found case-insensitive exact match: '{ann_text}' at ({ann['x']}, {ann['y']})")
            return ann['x'], ann['y']
    
    # Try partial match (target text is contained in annotation)
    for ann in ocr_annotations:
        ann_text = ann['text'].strip()
        if target_normalized in ' '.join(ann_text.lower().split()):
            print(f"[Debug] Found partial match (target in annotation): '{ann_text}' contains '{target_text}' at ({ann['x']}, {ann['y']})")
            return ann['x'], ann['y']
    
    # Try reverse partial match (annotation text is contained in target)
    for ann in ocr_annotations:
        ann_text = ann['text'].strip()
        ann_normalized = ' '.join(ann_text.lower().split())
        if ann_normalized in target_normalized:
            print(f"[Debug] Found partial match (annotation in target): '{target_text}' contains '{ann_text}' at ({ann['x']}, {ann['y']})")
            return ann['x'], ann['y']
    
    # Try word-by-word matching for multi-word targets
    target_words = target_normalized.split()
    if len(target_words) > 1:
        for ann in ocr_annotations:
            ann_text = ann['text'].strip()
            ann_words = ' '.join(ann_text.lower().split()).split()
            
            # Check if all target words are in annotation
            if all(word in ' '.join(ann_words) for word in target_words):
                print(f"[Debug] Found word-by-word match: '{ann_text}' contains all words from '{target_text}' at ({ann['x']}, {ann['y']})")
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
            
            # Check if this looks like a keyboard key that should be pressed instead of clicked
            target_lower = target_text.lower().strip()
            if target_lower in KEY_MAP:
                print(f"[Agent] Converting click on '{target_text}' to key press")
                pyautogui.press(KEY_MAP[target_lower])
                continue
            
            # Check for common keyboard key variations
            key_variations = {
                'enter': 'enter',
                'return': 'return',
                'tab': 'tab',
                'space': 'space',
                'backspace': 'backspace',
                'delete': 'delete',
                'escape': 'escape',
                'esc': 'escape',
                'up': 'up',
                'down': 'down',
                'left': 'left',
                'right': 'right',
                'home': 'home',
                'end': 'end',
                'page up': 'pageup',
                'page down': 'pagedown',
                'insert': 'insert'
            }
            
            if target_lower in key_variations:
                print(f"[Agent] Converting click on '{target_text}' to key press")
                pyautogui.press(key_variations[target_lower])
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
                # Try to suggest alternatives
                if ocr_annotations:
                    print(f"[Debug] Similar available elements:")
                    target_words = target_lower.split()
                    for ann in ocr_annotations[:5]:
                        ann_words = ' '.join(ann['text'].lower().split()).split()
                        common_words = set(target_words) & set(ann_words)
                        if common_words:
                            print(f"  - '{ann['text']}' (shares words: {list(common_words)})")
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
