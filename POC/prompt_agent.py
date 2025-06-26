import openai
from config import OPENAI_API_KEY
from safety_constants import SAFETY_PROMPT, SAFETY_REFUSAL_MESSAGE
import json
import re
import ast

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def check_moderation_scores(response):
    """Check if moderation scores are within safe ranges"""
    # Define safe thresholds for each category (values close to 0 are safer)
    SAFE_THRESHOLDS = {
        'hate': 0.1,
        'hate/threatening': 0.1,
        'harassment': 0.1,
        'harassment/threatening': 0.1,
        'self-harm': 0.1,
        'self-harm/intent': 0.1,
        'self-harm/instructions': 0.1,
        'sexual': 0.1,
        'sexual/minors': 0.01,  # Extra strict for minors
        'violence': 0.1,
        'violence/graphic': 0.1
    }
    
    # Check if response has moderation data
    if hasattr(response, 'moderation') and response.moderation:
        moderation = response.moderation
        if hasattr(moderation, 'category_scores'):
            scores = moderation.category_scores
            for category, threshold in SAFE_THRESHOLDS.items():
                key = category.replace('/', '_')
                score = scores.get(key)
                if score is not None and score > threshold:
                    score = getattr(scores, category.replace('/', '_'))
                    if score > threshold:
                        return False
    return True

def get_command_steps(prompt):
    try:
        from system_info import get_system_info, get_best_app_for_task
        system_info = get_system_info()
        os_type = system_info['os']
        
        # Build dynamic context from actual system
        available_apps_text = ""
        for category, apps in system_info['available_apps'].items():
            if apps:
                available_apps_text += f"{category}: {', '.join(apps[:2])}; "
        
        current_os_info = f"{os_type} with {system_info.get('desktop_environment', 'unknown')} desktop"
        if available_apps_text:
            current_os_info += f". Available apps: {available_apps_text.rstrip('; ')}"
    except ImportError:
        # Fallback if system_info module isn't available
        import platform
        os_type = platform.system().lower()
        current_os_info = f"{os_type} system"
    
    system_prompt = (
        f"You are an intelligent OS automation agent running on {os_type} ({current_os_info}). "
        "Convert user tasks into a JSON list of step objects with smart context awareness. "
        "Each step should have an 'action' key and relevant parameters. "
        
        "Available actions: "
        "- open_app: Opens applications (be smart about app names for different OS) "
        "- search: Opens web browser with search query "
        "- type: Types text "
        "- press: Presses keyboard keys "
        "- file_search: Searches for files with glob patterns "
        "- file_copy: Copies files (src, dst) "
        "- file_move: Moves files (src, destination_path) "
        "- select_file: Selects a file for operations "
        "- locate_file: Finds files by name in directory "
        "- navigate: Changes directory "
        "- open_file: Opens files with default application "
        
        "Be intelligent about: "
        "1. App names (calculator vs gnome-calculator vs kcalc) "
        "2. File paths (use ~ for home, expand common folder names) "
        "3. Combining multiple actions for complex tasks "
        "4. Error handling and alternative approaches "
        
        "Example: [{\"action\": \"open_app\", \"app\": \"calculator\"}, {\"action\": \"search\", \"query\": \"weather forecast\"}]"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": SAFETY_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    # Check if the response is flagged by OpenAI's safety systems
    if hasattr(response, 'flagged') and response.flagged:
        return {"error": True, "message": SAFETY_REFUSAL_MESSAGE}
    
    # Check individual moderation category scores
    if not check_moderation_scores(response):
        return {"error": True, "message": SAFETY_REFUSAL_MESSAGE}
    
    # Try to extract JSON from the response
    content = response.choices[0].message.content
    
    # Additional check for choice-level flagging if available
    choice = response.choices[0]
    if hasattr(choice, 'flagged') and choice.flagged:
        return {"error": True, "message": SAFETY_REFUSAL_MESSAGE}
    
    # Check if response starts with an apology/refusal
    if content.strip().lower().startswith("error") or content.strip().lower().startswith("i'm sorry"):
        return {"error": True, "message": SAFETY_REFUSAL_MESSAGE}
    
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            try:
                return ast.literal_eval(match.group(0))
            except Exception:
                pass
    # fallback: try to parse as JSON directly
    try:
        return json.loads(content)
    except Exception:
        return content  # fallback to raw content


def get_opposite_command_steps(command_steps):
    try:
        from system_info import get_system_info, get_best_app_for_task
        system_info = get_system_info()
        os_type = system_info['os']
        
        # Build dynamic context from actual system
        available_apps_text = ""
        for category, apps in system_info['available_apps'].items():
            if apps:
                available_apps_text += f"{category}: {', '.join(apps[:2])}; "
        
        current_os_info = f"{os_type} with {system_info.get('desktop_environment', 'unknown')} desktop"
        if available_apps_text:
            current_os_info += f". Available apps: {available_apps_text.rstrip('; ')}"
    except ImportError:
        # Fallback if system_info module isn't available
        import platform
        os_type = platform.system().lower()
        current_os_info = f"{os_type} system"
    
    system_prompt = (
        f"You are an intelligent OS automation agent running on {os_type} ({current_os_info}). "
        "Convert the following steps JSON list into a steps JSON list of the opposite steps. Use valid JSON and use smart context awareness. "
        "Each step should have an 'action' key and relevant parameters. "
        
        "Available actions: "
        "- open_app: Opens applications (be smart about app names for different OS) "
        "- search: Opens web browser with search query "
        "- type: Types text "
        "- press: Presses keyboard keys "
        "- file_search: Searches for files with glob patterns "
        "- file_copy: Copies files (src, dst) "
        "- file_move: Moves files (src, destination_path) "
        "- select_file: Selects a file for operations "
        "- locate_file: Finds files by name in directory "
        "- navigate: Changes directory "
        "- open_file: Opens files with default application "
        
        "Be intelligent about: "
        "1. App names (calculator vs gnome-calculator vs kcalc) "
        "2. File paths (use ~ for home, expand common folder names) "
        "3. Combining multiple actions for complex tasks "
        "4. Error handling and alternative approaches "
        
        "Example: input [{\"action\": \"open_app\", \"app\": \"calculator\"}, {\"action\": \"search\", \"query\": \"weather forecast\"}]"
        "Example: output [{\"action\": \"close_app\", \"app\": \"calculator\"}, {\"action\": \"close_tab\", \"query\": \"weather forecast\"}]"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(command_steps)}
        ],
        temperature=0.2
    )
    # Try to extract JSON from the response
    content = response.choices[0].message.content

    print(content)

    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            try:
                return ast.literal_eval(match.group(0))
            except Exception:
                pass
    # fallback: try to parse as JSON directly
    try:
        return json.loads(content)
    except Exception:
        return content  # fallback to raw content    