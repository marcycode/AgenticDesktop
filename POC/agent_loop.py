import os
import time
import mss
import io
from desktop_actions import execute_steps
from openai import AzureOpenAI
import base64
import json
from system_info import get_system_info
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT

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
    'screen_b64': '',
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
        return img_bytes, img_b64

def build_llm_prompt(goal, actions_taken):
    sysinfo = get_system_info()
    sysinfo_str = f"OS: {sysinfo['os']} {sysinfo['os_version']} | Arch: {sysinfo['architecture']} | Desktop: {sysinfo.get('desktop_environment', 'unknown')}"
    prompt = f'''
You are an agent controlling a computer only through simulated mouse and keyboard actions.

Device/system info:
{sysinfo_str}

Your goal is: "{goal}"

Here are the actions you have taken so far:
{json.dumps(actions_taken, indent=2)}

IMPORTANT: Look carefully at the current screen image. If you see evidence that your previous actions were incorrect, made a mistake, or didn't achieve the intended result, you MUST correct course immediately. Don't continue with a flawed approach - adapt and fix the situation.

Examples of when to correct course:
- If you opened the wrong application, close it and open the correct one
- If you typed in the wrong field, clear it and type in the right place
- If you clicked the wrong button, undo the action or navigate back
- If you see an error message, address it appropriately
- If the screen shows something unexpected, adjust your strategy

You can only use these actions:
- {{"action": "type", "text": "..."}}  # For typing plain text (no modifiers)
- {{"action": "press", "keys": [key1, key2, ...]}}  # For keyboard shortcuts or modifier keys (e.g., ['command', 't'] for Cmd+T)
- {{"action": "mouse", "x": ..., "y": ..., "button": "left"|"right"|"middle", "clicks": 1}}

Examples:
- To type 'hello', use: {{"action": "type", "text": "hello"}}
- To press Cmd+T (open new tab on macOS), use: {{"action": "press", "keys": ["command", "t"]}}
- To press Ctrl+W, use: {{"action": "press", "keys": ["ctrl", "w"]}}

Look at the current screen image and determine what action to take next to achieve your goal. If you need to correct a previous mistake, do so immediately.

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
        # 2. Build LLM prompt
        prompt = build_llm_prompt(goal, agent_state['actions_taken'])
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
            execute_steps([action])
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

if __name__ == "__main__":
    print("=== AGENTIC DESKTOP: PERCEPTION-ACTION LOOP (AUTORUN) ===")
    user_goal = input("Enter your goal: ")
    agent_autorun(user_goal)
    print("\nFinal agent state:")
    print(json.dumps(agent_state, indent=2)) 