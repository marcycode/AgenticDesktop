import os
import time
import mss
import io
from google.cloud import vision
from google.cloud.vision_v1 import types
from desktop_actions import execute_steps
from openai import AzureOpenAI
import base64
import json
from system_info import get_system_info
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT

# Check for Google Cloud Vision API key
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
if not GOOGLE_CREDENTIALS or not os.path.exists(GOOGLE_CREDENTIALS):
    raise RuntimeError("Google Cloud Vision API key not found. Please set the GOOGLE_APPLICATION_CREDENTIALS environment variable to your service account JSON file.")

# Initialize Google Cloud Vision client
vision_client = vision.ImageAnnotatorClient()

# Initialize OpenAI client (new API)
openai_client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-10-21",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

# State for transparency and web UI
agent_state = {
    'goal': None,
    'actions_taken': [],
    'step': 0,
    'screen_ocr': '',
    'screen_b64': '',
    'ocr_annotations': [],
    'llm_prompt': '',
    'llm_response': '',
    'status': 'idle',
    'message': '',
    'stop_requested': False
}

def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
        # For web UI: base64 encode
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        # Debug: Print monitor and image information
        print(f"[Debug] Monitor info: {monitor}")
        print(f"[Debug] Screenshot size: {screenshot.size}")
        print(f"[Debug] Image bytes size: {len(img_bytes)}")
        
        return img_bytes, img_b64

def ocr_screen_with_coordinates(img_bytes):
    """Extract text with coordinate annotations from the screen, robust scaling for Retina/HiDPI displays."""
    image = types.Image(content=img_bytes)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations
    
    if not texts:
        return "", []
    
    # Full text content
    full_text = texts[0].description
    
    # Get scaling factor using mss
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        screen_width = monitor['width']
        screen_height = monitor['height']
        screenshot_width = screenshot.width
        screenshot_height = screenshot.height
        scale_x = screen_width / screenshot_width
        scale_y = screen_height / screenshot_height
        # Optional: print debug info
        print(f"[Debug] Screen: {screen_width}x{screen_height}, Screenshot: {screenshot_width}x{screenshot_height}, Scale: x={scale_x:.3f}, y={scale_y:.3f}")
    
    # Group by text content for instance tracking
    text_groups = {}
    for text in texts[1:]:
        text_content = text.description
        vertices = text.bounding_poly.vertices
        x_coords = [vertex.x for vertex in vertices]
        y_coords = [vertex.y for vertex in vertices]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        # Scale to screen coordinates
        screen_x = int(center_x * scale_x)
        screen_y = int(center_y * scale_y)
        bbox = {
            'x1': int(min(x_coords) * scale_x),
            'y1': int(min(y_coords) * scale_y),
            'x2': int(max(x_coords) * scale_x),
            'y2': int(max(y_coords) * scale_y)
        }
        ann = {
            'text': text_content,
            'x': screen_x,
            'y': screen_y,
            'bbox': bbox
        }
        if text_content not in text_groups:
            text_groups[text_content] = []
        text_groups[text_content].append(ann)
    # Add instance info
    annotations = []
    for text_content, instances in text_groups.items():
        if len(instances) == 1:
            ann = instances[0]
            ann['index'] = 0
            ann['total_instances'] = 1
            annotations.append(ann)
        else:
            for i, ann in enumerate(instances):
                ann['index'] = i
                ann['total_instances'] = len(instances)
                annotations.append(ann)
    return full_text, annotations

def build_llm_prompt(goal, actions_taken, ocr_annotations):
    sysinfo = get_system_info()
    sysinfo_str = f"OS: {sysinfo['os']} {sysinfo['os_version']} | Arch: {sysinfo['architecture']} | Desktop: {sysinfo.get('desktop_environment', 'unknown')}"
    
    # Format OCR annotations for the prompt
    ocr_info = "Available clickable text elements on screen:\n"
    for ann in ocr_annotations:
        ocr_info += f"- '{ann['text']}' at position ({ann['x']}, {ann['y']})\n"
    
    prompt = f'''
You are an agent controlling a computer only through simulated mouse and keyboard actions.

Device/system info:
{sysinfo_str}

Your goal is: "{goal}"

Here are the actions you have taken so far:
{json.dumps(actions_taken, indent=2)}

{ocr_info}

IMPORTANT: Look carefully at the current screen image. If you see evidence that your previous actions were incorrect, made a mistake, or didn't achieve the intended result, you MUST correct course immediately. Don't continue with a flawed approach - adapt and fix the situation.

Examples of when to correct course:
- If you opened the wrong application, close it and open the correct one
- If you typed in the wrong field, clear it and type in the right place
- If you clicked the wrong button, undo the action or navigate back
- If you see an error message, address it appropriately
- If the screen shows something unexpected, adjust your strategy

CURSOR POSITION AWARENESS: Pay special attention to the cursor location in the screenshot. When deciding on mouse movements:
- If the cursor is already at or near the target location, you may not need to move it
- If the cursor is far from where you need to click, specify the exact coordinates to move it
- Consider the current cursor position when planning your next mouse action
- Avoid unnecessary mouse movements if the cursor is already positioned correctly
- Additionally, use keyboard shortcuts to navigate the UI when possible.

You can only use these actions:
- {{"action": "type", "text": "..."}}  # For typing plain text (no modifiers)
- {{"action": "press", "keys": [key1, key2, ...]}}  # For keyboard shortcuts or modifier keys (e.g., ['command', 't'] for Cmd+T)
- {{"action": "click_text", "target": "text to click"}}  # Click on text element (use exact text from OCR annotations)

Examples:
- To type 'hello', use: {{"action": "type", "text": "hello"}}
- To press Cmd+T (open new tab on macOS), use: {{"action": "press", "keys": ["command", "t"]}}
- To press Ctrl+W, use: {{"action": "press", "keys": ["ctrl", "w"]}}
- To click on a button with text "Submit", use: {{"action": "click_text", "target": "Submit"}}

Look at the current screen image and determine what action to take next to achieve your goal. If you need to correct a previous mistake, do so immediately. Pay special attention to the cursor position when deciding mouse movements.

If the goal is achieved, respond with:
{{"action": "done"}}

Respond ONLY with a single JSON object and no extra text.
'''
    return prompt

def call_llm(prompt, image_b64):
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a desktop automation agent. Follow instructions precisely."},
            {
                "role": "user", 
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                ]
            }
        ],
        temperature=0.2,
        max_tokens=256
    )
    content = response.choices[0].message.content.strip()
    return content

def parse_llm_response(response):
    try:
        # Find the first JSON object in the response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end != -1:
            return json.loads(response[start:end])
    except Exception as e:
        print(f"[Agent] Failed to parse LLM response: {e}")
    return {"action": "ask", "message": "Could not parse LLM response."}

def agent_autorun(goal, max_steps=20):
    agent_state['goal'] = goal
    agent_state['actions_taken'] = []
    agent_state['step'] = 0
    agent_state['status'] = 'running'
    agent_state['message'] = ''
    agent_state['stop_requested'] = False
    print(f"[Agent] Starting autorun perception-action loop for goal: {goal}")
    for step in range(max_steps):
        # Check if stop was requested
        if agent_state['stop_requested']:
            agent_state['status'] = 'stopped'
            agent_state['message'] = 'Agent loop stopped by user.'
            print("[Agent] Agent loop stopped by user.")
            break
            
        agent_state['step'] = step
        # 1. Capture the screen
        img_bytes, img_b64 = capture_screen()
        agent_state['screen_b64'] = img_b64
        # 2. OCR the screen with coordinates
        screen_text, ocr_annotations = ocr_screen_with_coordinates(img_bytes)
        agent_state['screen_ocr'] = screen_text
        agent_state['ocr_annotations'] = ocr_annotations
        # 3. Build LLM prompt
        prompt = build_llm_prompt(goal, agent_state['actions_taken'], agent_state['ocr_annotations'])
        agent_state['llm_prompt'] = prompt
        # 4. Call LLM
        llm_response = call_llm(prompt, img_b64)
        agent_state['llm_response'] = llm_response
        print(f"[LLM Prompt]:\n{prompt}\n[LLM Response]:\n{llm_response}")
        # 5. Parse LLM response
        action = parse_llm_response(llm_response)
        agent_state['actions_taken'].append(action)
        # 6. Execute action
        if action['action'] == 'done':
            agent_state['status'] = 'done'
            agent_state['message'] = 'Goal achieved.'
            print("[Agent] Goal achieved!")
            break
        elif action['action'] == 'ask':
            agent_state['status'] = 'ask'
            agent_state['message'] = action.get('message', 'Agent is stuck or needs clarification.')
            print(f"[Agent] {agent_state['message']}")
            break
        else:
            execute_steps([action], agent_state['ocr_annotations'])
        time.sleep(1)  # Small delay between steps
    else:
        agent_state['status'] = 'max_steps'
        agent_state['message'] = 'Reached maximum number of steps.'
        print("[Agent] Reached maximum number of steps.")

def get_agent_state():
    """Return the current agent state for the web UI."""
    return agent_state

def stop_agent_loop():
    """Stop the currently running agent loop."""
    agent_state['stop_requested'] = True
    return True

def get_current_mouse_position():
    """Get current mouse position for debugging"""
    import pyautogui
    x, y = pyautogui.position()
    print(f"[Debug] Current mouse position: ({x}, {y})")
    return x, y

def test_coordinate_mapping():
    """Test function to debug coordinate mapping between OCR and mouse"""
    print("=== COORDINATE MAPPING TEST ===")
    
    # Capture screen
    img_bytes, img_b64 = capture_screen()
    
    # Get current mouse position
    mouse_x, mouse_y = get_current_mouse_position()
    
    # Perform OCR
    screen_text, ocr_annotations = ocr_screen_with_coordinates(img_bytes)
    
    print(f"\n[Debug] OCR found {len(ocr_annotations)} text elements:")
    for i, ann in enumerate(ocr_annotations[:5]):  # Show first 5
        print(f"  {i+1}. '{ann['text']}' at ({ann['x']}, {ann['y']})")
    
    print(f"\n[Debug] Current mouse position: ({mouse_x}, {mouse_y})")
    print(f"[Debug] Screen text length: {len(screen_text)}")
    
    return ocr_annotations, mouse_x, mouse_y

if __name__ == "__main__":
    print("=== AGENTIC DESKTOP: PERCEPTION-ACTION LOOP (AUTORUN) ===")
    
    # Test coordinate mapping first
    test_coordinate_mapping()
    
    user_goal = input("Enter your goal: ")
    agent_autorun(user_goal)
    print("\nFinal agent state:")
    print(json.dumps(agent_state, indent=2)) 