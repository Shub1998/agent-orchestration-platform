import json
import re
from langchain_core.tools import tool


@tool
def json_parser(text: str, key_path: str = "") -> str:
    """Parse JSON text and optionally extract a nested value by dot-notation key path (e.g. 'data.items.0.name'). Returns the parsed value or full JSON if no key_path given."""
    try:
        data = json.loads(text)
        if not key_path:
            return json.dumps(data, indent=2)
        parts = key_path.split(".")
        current = data
        for part in parts:
            if isinstance(current, list):
                current = current[int(part)]
            else:
                current = current[part]
        return json.dumps(current, indent=2) if isinstance(current, (dict, list)) else str(current)
    except Exception as e:
        return f"JSON parse failed: {str(e)}"


@tool
def text_summarizer(text: str, max_sentences: int = 5) -> str:
    """Summarize a long text by extracting the most important sentences. Args: text (required), max_sentences (default 5)."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= max_sentences:
        return text
    step = max(1, len(sentences) // max_sentences)
    selected = sentences[:1] + sentences[1::step][: max_sentences - 1]
    return " ".join(selected)
