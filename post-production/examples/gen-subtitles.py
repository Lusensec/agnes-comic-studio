#!/usr/bin/env python3
"""Generate SRT subtitles from script dialogue.

Strips parenthetical stage directions.
Timing based on actual video duration (scene count × duration per scene).

Usage:
    python gen-subtitles.py "项目名"
"""
import json
import re
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


def clean_text(text: str) -> str:
    """Remove stage directions in parentheses. Keep only actual dialogue."""
    # Remove （...） and (...) patterns
    text = re.sub(r'（[^）]*）', '', text)
    text = re.sub(r'\([^)]*\)', '', text)
    text = text.strip()
    return text


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
    total_scenes = len(scenes)
    
    # Timing: each scene = duration seconds, subtitles centered in that window
    lines = []
    for scene in scenes:
        # Handle dialogue field: could be list, string, or missing
        raw_dialogue = scene.get("dialogue", [])
        if isinstance(raw_dialogue, str):
            # It's a single string - treat as one line
            dialogs = [raw_dialogue] if raw_dialogue.strip() else []
        elif isinstance(raw_dialogue, list):
            dialogs = raw_dialogue
        else:
            dialogs = []

        for dialog in dialogs:
            # Handle both formats: string or dict
            if isinstance(dialog, str):
                raw = dialog
                char = ""
            elif isinstance(dialog, dict):
                raw = dialog.get("line", "")
                char = dialog.get("character", "")
            else:
                continue
            text = clean_text(raw)
            if not text:
                continue
            # Display: "角色：台词" or just "台词"
            display = f"{char}：{text}" if char else text

            # Center subtitle within scene's time window
            scene_id = scene.get("scene_id", 1)
            scene_start = (scene_id - 1) * duration
            # Each dialogue gets 60% of scene time, centered
            offset = scene_start + duration * 0.2
            dur = min(duration * 0.6, 4.0)
            lines.append(f"{len(lines)+1}\n{fmt_time(offset)} --> {fmt_time(offset + dur)}\n{display}\n")

    total_dur = total_scenes * duration
    out = proj_dir / "videos" / "subtitles.srt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    track_file(project, "subtitle", str(out), "SRT 字幕文件", f"scenes={total_scenes}")
    print(f"✅ 字幕已生成: {out.name} ({len(lines)} 条)")
    print(f"   视频总时长: {total_dur}s | 字幕对齐窗口: 每场景 {duration}s 内居中")


if __name__ == "__main__":
    main()
