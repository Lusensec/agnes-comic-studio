#!/usr/bin/env python3
"""Generate a video from text prompt.

Usage:
    python text-to-video.py "提示词" [时长秒数]
    时长: 5 (default) | 10
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY


def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "小猫在客厅里追逐激光笔"
    seconds = sys.argv[2] if len(sys.argv) > 2 else "5"

    data = json.dumps({
        "model": "agnes-video-2.5-flash",
        "prompt": prompt,
        "seconds": seconds,
        "mode": "text",
        "size": "720P",
        "aspect_ratio": "16:9"
    }).encode()
    req = urllib.request.Request(
        "https://api.agnes-ai.cn/v1/videos",
        data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=120).read()
    result = json.loads(resp)
    video_id = result["video_id"]
    print(f"🎬 视频任务已提交: {video_id}")
    print(f"   状态: {result.get('status')}")
    print(f"\n查询进度: python poll-video.py {video_id}")


if __name__ == "__main__":
    main()
