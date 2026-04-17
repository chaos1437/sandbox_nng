#!/usr/bin/env python3
"""Keybinding setup utility. Run from project root: python -m config.setup_controls"""
import curses
from pathlib import Path
import yaml


def find_curses_name(k):
    """Find curses constant name for key code k."""
    for attr in dir(curses):
        if attr.startswith("KEY_") and getattr(curses, attr) == k:
            return attr
    # Not a special key — return the char itself
    if 32 <= k <= 126:
        return chr(k)
    return str(k)


def setup(stdscr):
    curses.curs_set(1)
    stdscr.clear()
    stdscr.nodelay(False)
    stdscr.keypad(True)

    actions = ["up", "down", "left", "right", "quit"]
    bindings = {}

    stdscr.addstr("=== Keybinding Setup ===\n\n")
    stdscr.addstr("Press corresponding key for each action.\n")
    stdscr.addstr("Arrow keys should work if terminal supports them.\n\n")
    stdscr.refresh()

    for action in actions:
        stdscr.addstr(f"Press key for [{action}]: ")
        stdscr.refresh()
        key = stdscr.getch()
        name = find_curses_name(key)
        # Store as clean string: KEY_UP or single char
        if name.startswith("KEY_"):
            bindings[action] = name
        elif len(name) == 3 and name.startswith("'") and name.endswith("'"):
            bindings[action] = name[1]  # 'w' -> w
        else:
            bindings[action] = name
        stdscr.addstr(f"  -> {bindings[action]} (code {key})\n")
        stdscr.refresh()

    # Write config
    config_path = Path(__file__).parent.parent / "config" / "client.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    config["controls"] = bindings

    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    stdscr.clear()
    stdscr.addstr("Controls saved to config/client.yaml:\n\n")
    for action, name in bindings.items():
        stdscr.addstr(f"  {action}: {name}\n")
    stdscr.addstr("\nDone! Press any key to exit.\n")
    stdscr.refresh()
    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(setup)
