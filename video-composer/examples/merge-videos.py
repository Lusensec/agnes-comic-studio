#!/usr/bin/env python3
"""Merge all scene videos into one using ffmpeg.

Usage:
    python merge-videos.py "项目名"
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import PROJECT_ROOT


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    video_dir = PROJECT_ROOT / project / "videos"
    clips = sorted(video_dir.glob("scene-*.mp4"))

    if not clips:
        print(f"[ERROR] {video_dir} 下没有 scene-*.mp4 文件")
        sys.exit(1)

    # Build ffmpeg concat file (relative names + cwd=videos dir, so this
    # works from any invocation directory on Windows and Linux)
    concat_list = video_dir / "concat.txt"
    concat_list.write_text(
        "\n".join(f"file '{c.name}'" for c in clips) + "\n", encoding="utf-8"
    )

    out = video_dir / f"{project}-full.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "concat.txt",
        "-c", "copy",
        out.name
    ]

    print(f"🎬 拼接 {len(clips)} 个片段 → {out.name}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=video_dir)
    if result.returncode != 0:
        print(f"[ERROR] ffmpeg 失败:\n{result.stderr[-500:]}")
        print("  请确认 ffmpeg 已安装: winget install Gyan.FFmpeg / brew install ffmpeg / apt install ffmpeg")
        sys.exit(1)

    # Report duration from the script config if available (else clips × 5s guess)
    per_scene = 5
    scripts = list((PROJECT_ROOT / project / "scripts").glob(f"{project}-script.json"))
    if scripts:
        try:
            s = json.loads(scripts[0].read_text(encoding="utf-8"))
            per_scene = int(s.get("config", {}).get("video_duration", 5) or 5)
        except (json.JSONDecodeError, TypeError, ValueError, OSError):
            pass
    print(f"✅ 完整视频: {out}")
    print(f"   时长: {len(clips)} × {per_scene}s ≈ {len(clips)*per_scene}s")
    try:
        (video_dir / "concat.txt").unlink()
    except OSError:
        pass


if __name__ == "__main__":
    main()
