import json
import requests
import re
from ..config import secrets

def call_llm(messages: list, model: str) -> str:
    assert "OPENROUTER_API_KEY" in secrets.keys(), "Missing OPENROUTER_API_KEY"

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {secrets['OPENROUTER_API_KEY']}",
            },
            data=json.dumps({
                "model": model,
                "messages": messages
            })
            )
        response.raise_for_status()
        result = response.json()
        
        # Extract the content from the response
        content = result['choices'][0]['message']['content']
        
        # Handle cases where content contains JSON or code blocks
        if isinstance(content, str):
            # Clean up JSON code blocks
            json_block_match = re.search(r'```json\s*\n?({.*?})\s*\n?```', content, re.DOTALL)
            if json_block_match:
                try:
                    parsed = json.loads(json_block_match.group(1))
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            # Handle stringified JSON (like '{"title": "Technology and Regulatory Compliance"}')
            content = content.strip()
            if content.startswith('{') and content.endswith('}'):
                try:
                    parsed = json.loads(content)
                    return parsed
                except json.JSONDecodeError:
                    pass
            
            # Clean up regular code blocks
            code_block_match = re.search(r'```\w*\s*\n?(.*?)\s*\n?```', content, re.DOTALL)
            if code_block_match:
                return code_block_match.group(1).strip()
            
            # Return cleaned string content
            return content.strip()
        
        # Handle non-string content
        return str(content)

    except Exception as e:
        raise e
