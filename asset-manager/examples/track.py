"""Shared asset tracking helper. Import from any script.

Usage:
    from track import ensure_project_db, track_file

    ensure_project_db(project)  # Creates assets.db if missing
    track_file(project, "image", path, "描述", "tag1,tag2")
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

sys_path_hack = True  # marker


def _db_path(project: str) -> Path:
    from load_env import PROJECT_ROOT
    return PROJECT_ROOT / project / "assets.db"


def ensure_project_db(project: str):
    """Create project dirs + assets.db if they don't exist."""
    from load_env import PROJECT_ROOT
    proj_dir = PROJECT_ROOT / project
    for subdir in ["scripts", "images", "videos", "references"]:
        (proj_dir / subdir).mkdir(parents=True, exist_ok=True)

    db = _db_path(project)
    if not db.exists():
        conn = sqlite3.connect(db)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                tags TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project, asset_type);
        """)
        conn.commit()
        conn.close()


def track_file(project: str, asset_type: str, filepath: str,
               description: str = "", tags: str = ""):
    """Record a file in the project's assets database."""
    ensure_project_db(project)
    db = _db_path(project)
    conn = sqlite3.connect(db)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO assets (project, asset_type, filename, filepath, description, created_at, tags) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (project, asset_type, Path(filepath).name, str(filepath), description, now, tags)
    )
    conn.commit()
    conn.close()
