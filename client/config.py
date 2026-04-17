# client/config.py
import yaml
import curses
from pathlib import Path

def load_client_config(path: str = "config/client.yaml") -> dict:
    full_path = Path(__file__).parent.parent / path
    with open(full_path) as f:
        return yaml.safe_load(f)

def resolve_controls(controls: dict) -> dict:
    """Resolve YAML string keys (e.g. "KEY_UP") to integer curses codes."""
    resolved = {}
    for action, key_name in controls.items():
        if isinstance(key_name, str) and hasattr(curses, key_name):
            resolved[action] = getattr(curses, key_name)
        else:
            resolved[action] = key_name
    return resolved
