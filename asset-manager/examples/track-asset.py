#!/usr/bin/env python3
"""Record a new asset in the project database.

Usage:
    python track-asset.py "项目名" <类型> <文件路径> [描述] [标签1,标签2]
    类型: script | image | video | reference
"""
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import PROJECT_ROOT


def track_asset(project, asset_type, filepath, description="", tags=""):
    db = PROJECT_ROOT / project / "assets.db"
    if not db.exists():
        print(f"[ERROR] 项目 {project} 不存在，请先运行 init-project.py", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO assets (project, asset_type, filename, filepath, description, created_at, tags) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (project, asset_type, Path(filepath).name, str(filepath), description, now, tags)
    )
    conn.commit()
    row = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    print(f"✅ 资产已记录 (id={row}): [{asset_type}] {Path(filepath).name}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    track_asset(sys.argv[1], sys.argv[2], sys.argv[3],
                sys.argv[4] if len(sys.argv) > 4 else "",
                sys.argv[5] if len(sys.argv) > 5 else "")
