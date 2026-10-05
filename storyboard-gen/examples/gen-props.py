#!/usr/bin/env python3
"""Generate prop/item reference images from script.

Props are defined in the script JSON under "props" field:
  "props": [
    {"name": "道具名", "description": "外观描述(用于生图)"}
  ]

If no "props" field exists, will attempt to extract key objects from scene descriptions.

Usage:
    python gen-props.py "项目名" [道具名]
    不带道具名则生成所有道具
"""
import json
import re
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
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    prop_name = sys.argv[2] if len(sys.argv) > 2 else None

    proj_dir = PROJECT_ROOT / project
    img_dir = proj_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    if not scripts:
        print("[ERROR] 未找到剧本", file=sys.stderr)
        sys.exit(1)
    script = json.loads(scripts[0].read_text())
    config = script.get("config", {})
    style = config.get("style", "动画")
    img_size = config.get("image_size", "1K")

    # Get props from script
    props = script.get("props", [])
    if not props:
        print("⚠️  剧本中没有 'props' 字段。")
        print("   请在剧本 JSON 中添加: \"props\": [{\"name\": \"XX\", \"description\": \"...\"}]")
        print("   跳过生成。")
        return

    if prop_name:
        props = [p for p in props if p.get("name") == prop_name]
        if not props:
            print(f"[ERROR] 道具 {prop_name} 不存在。可用: {[p['name'] for p in script.get('props',[])]}")
            sys.exit(1)

    print(f"🔧 生成 {len(props)} 个道具参考图...")
    sleep_sec = 7 if img_size == "2K" else 3

    for i, prop in enumerate(props):
        name = prop.get("name", f"prop-{i}")
        desc = prop.get("description", name)
        prompt = f"product reference sheet, {desc}, {style} style, white background, studio lighting, high detail, isolated object"

        out = img_dir / f"prop-{name}.png"
        print(f"  [{i+1}/{len(props)}] prop-{name}: {desc[:30]}...")
        url = gen_image(prompt, size=img_size)
        out.write_bytes(urllib.request.urlopen(url).read())
        track_file(project, "image_prop", str(out), f"道具: {name}", f"style={style}")
        print(f"     ✅ {out.name}")

        if i < len(props) - 1:
            time.sleep(sleep_sec)

    print(f"\n✅ 道具图完成，保存在 {img_dir}/")


if __name__ == "__main__":
    main()
