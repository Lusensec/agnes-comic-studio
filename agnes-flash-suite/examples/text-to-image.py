#!/usr/bin/env python3
"""Generate an image from text prompt.

Usage:
    python text-to-image.py "提示词" [尺寸] [比例]
    尺寸: 1K (default) | 2K
    比例: 1:1 (default) | 16:9 | 9:16 | 4:3
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY


def main():
    prompt = sys.argv[1] if len(sys.argv) > 1 else "a cute kitten"
    size = sys.argv[2] if len(sys.argv) > 2 else "1K"
    ratio = sys.argv[3] if len(sys.argv) > 3 else "1:1"

    data = json.dumps({
        "model": "agnes-image-2.5-flash",
        "prompt": prompt,
        "size": size,
        "ratio": ratio,
        "extra_body": {"response_format": "url"}
    }).encode()
    req = urllib.request.Request(
        "https://api.agnes-ai.cn/v1/images/generations",
        data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=360).read()
    result = json.loads(resp)
    url = result["data"][0]["url"]
    print(f"✅ 图片已生成: {url}")


if __name__ == "__main__":
    main()
