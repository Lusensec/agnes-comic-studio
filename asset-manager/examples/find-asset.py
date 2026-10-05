#!/usr/bin/env python3
"""Find assets by keyword (searches filename, description, tags).

Usage:
    python find-asset.py "项目名" "关键词" [类型]
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import PROJECT_ROOT


def find_asset(project, keyword, asset_type=""):
    db = PROJECT_ROOT / project / "assets.db"
    if not db.exists():
        print(f"[ERROR] 项目 {project} 不存在", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db)
    where = "project=? AND (filename LIKE ? OR description LIKE ? OR tags LIKE ?)"
    params = [project, f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
    if asset_type:
        where += " AND asset_type=?"
        params.append(asset_type)
    rows = conn.execute(
        f"SELECT id, asset_type, filename, filepath, description FROM assets WHERE {where} ORDER BY id",
        params
    ).fetchall()
    conn.close()

    if not rows:
        print(f"未找到匹配 \"{keyword}\" 的资产")
        return

    print(f"🔍 找到 {len(rows)} 项匹配 \"{keyword}\":\n")
    for r in rows:
        print(f"  #{r[0]} [{r[1]}] {r[2]}")
        print(f"       路径: {r[3]}")
        if r[4]:
            print(f"       描述: {r[4]}")
        print()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    find_asset(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
