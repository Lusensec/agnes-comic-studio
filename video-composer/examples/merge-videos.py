#!/usr/bin/env python3
"""Merge all scene videos into one using ffmpeg.

Usage:
    python merge-videos.py "项目名"
"""
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

    # Build ffmpeg concat file
    concat_list = video_dir / "concat.txt"
    concat_list.write_text("\n".join(f"file '{c.name}'" for c in clips))

    out = video_dir / f"{project}-full.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(out)
    ]

    print(f"🎬 拼接 {len(clips)} 个片段 → {out.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] ffmpeg 失败:\n{result.stderr[:500]}")
        print("  请确认 ffmpeg 已安装: apt install ffmpeg")
        sys.exit(1)

    print(f"✅ 完整视频: {out}")
    print(f"   时长: {len(clips)} × 5s ≈ {len(clips)*5}s")


if __name__ == "__main__":
    main()
