#!/usr/bin/env python3
"""Poll a video generation task until complete.

Usage:
    python poll-video.py <video_id>
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY

BASE_POLL = "https://api.agnes-ai.cn/agnesapi"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    video_id = sys.argv[1]
    print(f"📡 轮询视频任务: {video_id}\n")

    for i in range(20):
        url = f"{BASE_POLL}?video_id={video_id}&model_name=agnes-video-2.5-flash"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
        resp = urllib.request.urlopen(req, timeout=60).read()
        result = json.loads(resp)
        status = result.get("status", "unknown")
        progress = result.get("progress", 0)
        print(f"  [{i+1}] status={status} progress={progress}%")

        if status == "completed":
            print(f"\n✅ 完成! URL: {result.get('url')}")
            break
        if status == "failed":
            print(f"\n❌ 失败: {result.get('error')}")
            sys.exit(1)
        time.sleep(30)


if __name__ == "__main__":
    main()
