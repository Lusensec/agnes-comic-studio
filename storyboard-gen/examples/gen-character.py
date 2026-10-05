#!/usr/bin/env python3
"""Generate character reference images.

Usage:
    python gen-character.py "项目名" "角色名" [模式]
    模式: sheet (default, 单张) | three-view (三视图) | expression (多表情)

三视图: front + side + back 在一张图里
多表情: 6种情绪特写在一张图里
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY, PROJECT_ROOT
from track import track_file

BASE_IMG = "https://api.agnes-ai.cn/v1/images/generations"


def gen_image(prompt: str, size="1K", ratio="1:1") -> str:
    body = json.dumps({
        "model": "agnes-image-2.5-flash",
        "prompt": prompt,
        "size": size,
        "ratio": ratio,
        "extra_body": {"response_format": "url"}
    }).encode()
    req = urllib.request.Request(
        BASE_IMG, data=body,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=360).read()
    return json.loads(resp)["data"][0]["url"]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    char_name = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "sheet"

    proj_dir = PROJECT_ROOT / project
    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    if not scripts:
        print("[ERROR] 未找到剧本", file=sys.stderr)
        sys.exit(1)
    script = json.loads(scripts[0].read_text())
    config = script.get("config", {})
    img_size = config.get("image_size", "1K")
    style = config.get("style", "动画")

    char = next((c for c in script.get("characters", []) if c["name"] == char_name), None)
    if not char:
        available = [c["name"] for c in script.get("characters", [])]
        print(f"[ERROR] 角色 {char_name} 不存在。可用: {available}")
        sys.exit(1)

    desc = char.get("description", char_name)

    prompts = {
        "sheet": f"character design sheet, full body, front view, {desc}, {style} style, white background, high detail",
        "three-view": f"character three-view reference sheet, {desc}, front view, side view, back view arranged horizontally, {style} style, white background, clean lines, high detail",
        "expression": f"character expression sheet, 6 panels showing different emotions (happy, sad, angry, surprised, neutral, scared), {desc}, {style} style, white background",
    }

    prompt = prompts.get(mode, prompts["sheet"])
    suffix = mode if mode != "sheet" else ""
    out = proj_dir / "images" / f"character-{char_name}{suffix}.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"🎨 生成角色 [{char_name}] {mode} 图...")
    url = gen_image(prompt, size=img_size)
    out.write_bytes(urllib.request.urlopen(url).read())
    track_file(project, f"image_{mode}", str(out), f"{char_name} {mode}", f"style={style}")
    print(f"✅ 已保存: {out.name}")


if __name__ == "__main__":
    main()
