#!/usr/bin/env python3
"""Generate SRT subtitles from script dialogue.

Usage:
    python gen-subtitles.py "项目名"

输出: videos/subtitles.srt
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import PROJECT_ROOT
from track import track_file


def fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    proj_dir = PROJECT_ROOT / project
    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    if not scripts:
        print("[ERROR] 未找到剧本", file=sys.stderr)
        sys.exit(1)
    script = json.loads(scripts[0].read_text())
    config = script.get("config", {})
    duration = int(config.get("video_duration", "5"))

    scenes = script.get("scenes", [])
    lines = []
    t = 0.0

    for scene in scenes:
        sid = scene.get("scene_id", 0)
        for dialog in scene.get("dialogue", []):
            text = dialog.get("line", "")
            if text.startswith("(") and text.endswith(")"):
                continue  # Skip action descriptions
            char = dialog.get("character", "")
            # Format: "角色名：台词"
            display = f"{char}：{text}" if char else text
            start = t
            end = t + min(duration * 0.8, 4.0)
            lines.append(f"{len(lines)+1}\n{fmt_time(start)} --> {fmt_time(end)}\n{display}\n")
            t = end + 0.5  # 0.5s gap

    out = proj_dir / "videos" / "subtitles.srt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    track_file(project, "subtitle", str(out), "SRT 字幕文件", f"scenes={len(scenes)}")
    print(f"✅ 字幕已生成: {out.name} ({len(lines)} 条)")
    print(f"   总时长: {fmt_time(t)}")


if __name__ == "__main__":
    main()
