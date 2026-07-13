import json
from pathlib import Path

PROMPT_FILE = Path(__file__).resolve().parent.parent / "config" / "CodeFrame_prompts.json"
CONFIG_FILE = Path(__file__).resolve().parent.parent / "config" / "CodeFrame_config.json"

def load_prompts():
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_split_prompt():
    data = load_prompts()
    return data.get("Split_Prompt")

def get_map_prompt():
    data = load_prompts()
    return data.get("Map_Prompt")



def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def get_fieldRegion():
    data = load_config()
    return data.get("fieldRegion", {})

def get_dialect_by_region(region_name):
    regions = get_fieldRegion()
    return regions.get(region_name, "English")

def get_outputLanguageOptions():
    data = load_config()
    return data.get("outputLanguageOptions", [])

