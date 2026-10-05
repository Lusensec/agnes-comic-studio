#!/usr/bin/env python3
"""Poll a video task until complete.

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

BASE = "https://api.agnes-ai.cn/agnesapi"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    video_id = sys.argv[1]

    for i in range(40):
        url = f"{BASE}?video_id={video_id}&model_name=agnes-video-2.5-flash"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
        resp = urllib.request.urlopen(req, timeout=60).read()
        r = json.loads(resp)
        status = r.get("status", "")
        print(f"  [{i+1:>2}] {status} {r.get('progress', 0)}%")
        if status == "completed":
            print(f"\n✅ {r.get('url')}")
            return
        if status == "failed":
            print(f"\n❌ {r.get('error')}")
            sys.exit(1)
        time.sleep(30)

    print("⚠️  超时（20分钟），请手动查询")


if __name__ == "__main__":
    main()
