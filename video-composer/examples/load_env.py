"""Shared .env loader + config for all sub-skills.

Usage:
    from load_env import API_KEY, PROJECT_ROOT

.env discovery order: walk UP from this file (covers <suite-root>/.env,
<sub-skill>/.env, examples/.env), then CWD/.env. If no .env is found the
module still imports cleanly and API_KEY stays empty (caller decides what
to do) instead of crashing.

Stdio bootstrap: on systems whose console code page is not UTF-8 (e.g.
zh-CN Windows GBK/cp936), reconfigure stdout/stderr to UTF-8 with
errors="replace" so CJK + emoji output never crashes the script.
"""
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------- stdio fix
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass  # not a reconfigurable stream (e.g. pythonw, captured pipes)

# ------------------------------------------------------------- .env loading


def _find_env_file():
    """Return the first .env found walking up from this file, else CWD/.env."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        env = parent / ".env"
        if env.is_file():
            return env
    env = Path.cwd() / ".env"
    if env.is_file():
        return env
    return None


def _load_env():
    """Parse KEY=VALUE pairs from .env into os.environ (no overwrite)."""
    env_file = _find_env_file()
    if env_file is None:
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()

# ------------------------------------------------------------- config values
API_KEY = os.environ.get("AGNESAI_API_KEY", "")

# Configurable project root: env var > .env > default
PROJECT_ROOT = Path(
    os.environ.get(
        "COMIC_STUDIO_ROOT",
        str(Path.home() / "comic-studio" / "projects"),
    )
)
