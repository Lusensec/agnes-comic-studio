"""Shared .env loader for all sub-skills.

Usage:
    from load_env import API_KEY, PROJECT_ROOT
"""
import os
import sys
from pathlib import Path


def _find_env_file():
    """Walk up from this file to find .env."""
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent, Path.cwd()]:
        env = parent / ".env"
        if env.exists():
            return env
    # Fallback: workspace .env
    ws = Path("/workspace/.env")
    if ws.exists():
        return ws
    return None


def load_env():
    """Load AGNESAI_API_KEY from .env if not already in env."""
    if os.environ.get("AGNESAI_API_KEY"):
        return
    env_file = _find_env_file()
    if not env_file:
        print("[ERROR] .env not found. Set AGNESAI_API_KEY or create .env", file=sys.stderr)
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line.startswith("AGNESAI_API_KEY="):
            os.environ["AGNESAI_API_KEY"] = line.split("=", 1)[1]
            break


API_KEY = None
PROJECT_ROOT = Path.home() / "comic-studio" / "projects"

load_env()
API_KEY = os.environ.get("AGNESAI_API_KEY", "")
