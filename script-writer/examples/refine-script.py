#!/usr/bin/env python3
"""Refine a specific character or scene in an existing script.

Usage:
    python refine-script.py "项目名" "角色名" "新描述"
    python refine-script.py "项目名" --scene 3 "新场景描述"
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import PROJECT_ROOT


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    proj_dir = PROJECT_ROOT / project / "scripts"
    script_file = list(proj_dir.glob(f"{project}-script.json"))
    if not script_file:
        print(f"[ERROR] 找不到 {project}-script.json，请先运行 write-script.py")
        sys.exit(1)

    script = json.loads(script_file[0].read_text())

    if sys.argv[2] == "--scene":
        scene_id = int(sys.argv[3])
        new_desc = sys.argv[4]
        for s in script.get("scenes", []):
            if s.get("scene_id") == scene_id:
                s["description_zh"] = new_desc
                print(f"✅ 场景 {scene_id} 描述已更新: {new_desc}")
                break
        else:
            print(f"[ERROR] 场景 {scene_id} 不存在")
            sys.exit(1)
    else:
        char_name = sys.argv[2]
        new_desc = sys.argv[3]
        for c in script.get("characters", []):
            if c.get("name") == char_name:
                c["description"] = new_desc
                print(f"✅ 角色 [{char_name}] 描述已更新: {new_desc}")
                break
        else:
            print(f"[ERROR] 角色 [{char_name}] 不存在，可用角色: " +
                  ", ".join(c.get("name", "?") for c in script.get("characters", [])))
            sys.exit(1)

    script_file[0].write_text(json.dumps(script, ensure_ascii=False, indent=2))
    print(f"\n保存至: {script_file[0]}")
    print("下一步：")
    print(f"  [1] 重新生成分镜图 → python storyboard-gen/examples/gen-storyboard.py \"{project}\"")
    print(f"  [2] 继续修改 → python refine-script.py \"{project}\" ...")


if __name__ == "__main__":
    main()
