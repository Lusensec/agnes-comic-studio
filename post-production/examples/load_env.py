"""Shared .env loader + config for all sub-skills.

Usage:
    from load_env import API_KEY, PROJECT_ROOT
"""
import os
import sys
from pathlib import Path


def _find_env_file() -> Path:
    """Walk up to find .env."""
    here = Path(__file__).resolve()
    for parent in [here.parent, here.parent.parent, Path.cwd()]:
        env = parent / ".env"
        if env.exists():
            return env
    ws = Path("/workspace/.env")
    if ws.exists():
        return ws
    return Path("")


def _load_env():
    """Load AGNESAI_API_KEY and COMIC_STUDIO_ROOT from .env if not in env."""
    env_file = _find_env_file()
    if not env_file or not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip()
            if key not in os.environ:
                os.environ[key] = val


_load_env()

API_KEY = os.environ.get("AGNESAI_API_KEY", "")

# Configurable project root (fix #11)
# Priority: env var > .env > default
PROJECT_ROOT = Path(os.environ.get(
    "COMIC_STUDIO_ROOT",
    str(Path.home() / "comic-studio" / "projects")
))
