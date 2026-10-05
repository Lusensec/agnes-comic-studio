#!/usr/bin/env python3
"""List all assets in a project, optionally filtered by type.

Usage:
    python list-assets.py "项目名" [类型]
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import PROJECT_ROOT


def list_assets(project, asset_type=""):
    db = PROJECT_ROOT / project / "assets.db"
    if not db.exists():
        print(f"[ERROR] 项目 {project} 不存在", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db)
    if asset_type:
        rows = conn.execute(
            "SELECT id, asset_type, filename, description, created_at FROM assets "
            "WHERE project=? AND asset_type=? ORDER BY created_at",
            (project, asset_type)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, asset_type, filename, description, created_at FROM assets "
            "WHERE project=? ORDER BY created_at",
            (project,)
        ).fetchall()
    conn.close()

    if not rows:
        print(f"项目 {project} 暂无资产记录")
        return

    print(f"📦 项目 [{project}] 资产列表 ({len(rows)} 项)\n")
    for r in rows:
        desc = f" — {r[3]}" if r[3] else ""
        print(f"  #{r[0]:>3} [{r[1]:8s}] {r[2]}  ({r[4][:10]}){desc}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    list_assets(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
