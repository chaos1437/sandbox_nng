# client/config.py
import curses


def resolve_controls(controls: dict) -> dict:
    """Resolve YAML string keys to integer curses codes."""
    resolved = {}
    for action, key_name in controls.items():
        if isinstance(key_name, str) and hasattr(curses, key_name):
            resolved[action] = getattr(curses, key_name)
        elif isinstance(key_name, str):
            # Strip surrounding quotes: "'q'" -> 'q' -> ord, '''q''' -> q -> ord
            stripped = key_name.strip("'\"")
            if len(stripped) == 1:
                resolved[action] = ord(stripped)
            else:
                resolved[action] = key_name
        else:
            resolved[action] = key_name
    return resolved
