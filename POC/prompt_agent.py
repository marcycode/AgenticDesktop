import openai
from config import OPENAI_API_KEY
import json
import re
import ast

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_command_steps(prompt):
    system_prompt = (
        "You are an OS automation agent. "
        "Convert user tasks into a JSON list of step objects. "
        "Each step should have an 'action' key and relevant parameters. "
        "Example: [{\"action\": \"open_app\", \"app\": \"chrome\"}, {\"action\": \"search\", \"query\": \"food in seattle\"}]"
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    # Try to extract JSON from the response
    content = response.choices[0].message.content
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
