#!/usr/bin/env python3
"""Basic chat with agnes-2.5-flash or agnes-3.0-flash.

Usage:
    python basic-chat.py "用户问题" [model]
    model: agnes-2.5-flash (default) | agnes-3.0-flash
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY


def main():
    question = sys.argv[1] if len(sys.argv) > 1 else "你好，请介绍一下自己"
    model = sys.argv[2] if len(sys.argv) > 2 else "agnes-2.5-flash"

    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7
    }).encode()
    req = urllib.request.Request(
        "https://api.agnes-ai.cn/v1/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=120).read()
    print(json.loads(resp)["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
