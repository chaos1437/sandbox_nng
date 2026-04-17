#!/usr/bin/env python3
"""Auto-updating launcher for roguelike game."""
import asyncio
import subprocess
import sys
import argparse
from pathlib import Path


def check_for_updates():
    """Check if git updates available. Returns True if updates exist."""
    repo = Path(__file__).parent
    git_dir = repo / ".git"
    if not git_dir.exists():
        return False

    # Fetch and check status without merging
    subprocess.run(["git", "fetch"], cwd=repo, capture_output=True)
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD..origin/master"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    try:
        count = int(result.stdout.strip())
        return count > 0
    except ValueError:
        return False


def update():
    """Pull latest changes, preserving local config files on conflict."""
    repo = Path(__file__).parent
    config_files = ["config/server.yaml", "config/client.yaml"]

    # Save local configs
    configs = {}
    for f in config_files:
        p = repo / f
        if p.exists():
            configs[f] = p.read_bytes()

    result = subprocess.run(
        ["git", "pull"],
        cwd=repo,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Pull failed (likely conflict) - restore local configs
        for f, data in configs.items():
            (repo / f).write_bytes(data)
        print("Git pull failed, local configs preserved")

    if result.stdout.strip():
        print(result.stdout.rstrip())


def ask_update() -> bool:
    """Ask user if they want to update. Returns True if yes."""
    print("Updates available. Update? [Y/n]", end=" ")
    try:
        answer = input().strip().lower()
        return answer in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def main():
    parser = argparse.ArgumentParser(description="Roguelike game launcher")
    subparsers = parser.add_subparsers(dest="mode", help="Launch mode")

    client_parser = subparsers.add_parser("client", help="Launch client")
    client_parser.add_argument("--host", default="127.0.0.1")
    client_parser.add_argument("--port", type=int, default=8765)

    server_parser = subparsers.add_parser("server", help="Launch server")
    server_parser.add_argument("--port", type=int, default=8765)

    args, unknown = parser.parse_known_args()

    if args.mode is None:
        args.mode = "client"

    # Check for updates before launching either mode
    if check_for_updates():
        if ask_update():
            update()
        else:
            print("Skipping update, launching with current version...")

    if args.mode == "server":
        sys.argv = ["server"]
        if args.port != 8765:
            sys.argv.extend(["--port", str(args.port)])
        from server.main import main as server_main
        asyncio.run(server_main())
    else:
        # Client
        from shared.config import load_client_config
        cfg = load_client_config()
        cfg.host = args.host
        cfg.port = args.port

        from client.main import main as client_main
        import curses
        def run(stdscr):
            asyncio.run(client_main(stdscr, cfg))
        curses.wrapper(run)


if __name__ == "__main__":
    main()
