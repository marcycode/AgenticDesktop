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
    'llm_prompt': '',
    'llm_response': '',
    'status': 'idle',
    'message': ''
}

def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
        # For web UI: base64 encode
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        return img_bytes, img_b64

def ocr_screen(img_bytes):
    image = types.Image(content=img_bytes)
    response = vision_client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description  # Full detected text
    return ""

def build_llm_prompt(goal, actions_taken, screen_ocr):
    sysinfo = get_system_info()
    sysinfo_str = f"OS: {sysinfo['os']} {sysinfo['os_version']} | Arch: {sysinfo['architecture']} | Desktop: {sysinfo.get('desktop_environment', 'unknown')}"
    prompt = f'''
You are an agent controlling a computer only through simulated mouse and keyboard actions.

Device/system info:
{sysinfo_str}

Your goal is: "{goal}"

Here is the text currently visible on the screen (from OCR):
{screen_ocr}

Here are the actions you have taken so far:
{json.dumps(actions_taken, indent=2)}

You can only use these actions:
- {{"action": "type", "text": "..."}}  # For typing plain text (no modifiers)
- {{"action": "press", "keys": [key1, key2, ...]}}  # For keyboard shortcuts or modifier keys (e.g., ['command', 't'] for Cmd+T)
- {{"action": "mouse", "x": ..., "y": ..., "button": "left"|"right"|"middle", "clicks": 1}}

Examples:
- To type 'hello', use: {{"action": "type", "text": "hello"}}
- To press Cmd+T (open new tab on macOS), use: {{"action": "press", "keys": ["command", "t"]}}
- To press Ctrl+W, use: {{"action": "press", "keys": ["ctrl", "w"]}}

If the goal is achieved, respond with:
{{"action": "done"}}
If you are stuck or need clarification, respond with:
{{"action": "ask", "message": "..."}}

Respond ONLY with a single JSON object and no extra text.
'''
    return prompt

def call_llm(prompt):
    response = openai_client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a desktop automation agent. Follow instructions precisely."},
            {"role": "user", "content": prompt}
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
    print(f"[Agent] Starting autorun perception-action loop for goal: {goal}")
    for step in range(max_steps):
        agent_state['step'] = step
        # 1. Capture the screen
        img_bytes, img_b64 = capture_screen()
        agent_state['screen_b64'] = img_b64
        # 2. OCR the screen
        screen_text = ocr_screen(img_bytes)
        agent_state['screen_ocr'] = screen_text
        # 3. Build LLM prompt
        prompt = build_llm_prompt(goal, agent_state['actions_taken'], screen_text)
        agent_state['llm_prompt'] = prompt
        # 4. Call LLM
        llm_response = call_llm(prompt)
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
            execute_steps([action])
        time.sleep(1)  # Small delay between steps
    else:
        agent_state['status'] = 'max_steps'
        agent_state['message'] = 'Reached maximum number of steps.'
        print("[Agent] Reached maximum number of steps.")

def get_agent_state():
    """Return the current agent state for the web UI."""
    return agent_state

if __name__ == "__main__":
    print("=== AGENTIC DESKTOP: PERCEPTION-ACTION LOOP (AUTORUN) ===")
    user_goal = input("Enter your goal: ")
    agent_autorun(user_goal)
    print("\nFinal agent state:")
    print(json.dumps(agent_state, indent=2)) 