import json
from pathlib import Path

PROMPT_FILE = Path(__file__).resolve().parent.parent / "config" / "CodeFrame_categories.json"

def load_prompts():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_categories():
    data = load_prompts()
    return list(data.keys())

def get_split_prompt(product_name: str):
    data = load_prompts()
    return data.get(product_name, {}).get("Split_Prompt")

def get_map_prompt(product_name: str):
    data = load_prompts()
    return data.get(product_name, {}).get("Map_Prompt")