import re
import json

def safe_parse_llama_json(raw_text: str):
    """
    Витягує JSON-масив з тексту, навіть якщо LLaMA додала пояснення або зайві рядки.
    Якщо JSON не знайдено або зіпсовано — повертає текст з помилкою.
    """
    try:
        json_match = re.search(r'\[\s*\{.*?\}\s*\]', raw_text, re.DOTALL)
        if json_match:
            cleaned_json = json_match.group(0)
            return json.loads(cleaned_json)
        else:
            return f"⛔ JSON not found. Full response:\n{raw_text}"
    except json.JSONDecodeError as e:
        return f"⛔ JSON Decode Error: {e}\nFull response:\n{raw_text}"
