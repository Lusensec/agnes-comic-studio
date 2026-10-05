#!/usr/bin/env python3
"""Generate prop/item three-view reference images (front/side/top).

Usage:
    python gen-props.py "项目名" [道具名]
    
Outputs:
    images/prop-<name>-front.png
    images/prop-<name>-side.png
    images/prop-<name>-top.png
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

VIEWS = {
    "front": "front view, facing camera, ",
    "side": "side profile view, 90 degree angle, ",
    "top": "top-down view, bird's eye perspective, ",
}


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

    props = script.get("props", [])
    if not props:
        print("⚠️  剧本中没有 'props' 字段")
        return

    if prop_name:
        props = [p for p in props if p.get("name") == prop_name]
        if not props:
            print(f"[ERROR] 道具 {prop_name} 不存在")
            sys.exit(1)

    sleep_sec = 3 if img_size == "1K" else 7
    total = len(props) * 3
    print(f"🔧 生成 {len(props)} 个道具 × 3 视角 = {total} 张...")

    url_map = {}
    count = 0
    for prop in props:
        # Support both formats: string or dict
        if isinstance(prop, str):
            name = prop
            desc = prop
        else:
            name = prop.get("name", "unknown")
            desc = prop.get("description", name)
        
        for view, view_prefix in VIEWS.items():
            out = img_dir / f"prop-{name}-{view}.png"
            if out.exists():
                continue
            
            prompt = (f"product reference, {view_prefix}{desc}, "
                      f"{style} style, white background, studio lighting, "
                      f"isolated object, high detail")
            print(f"  🔧 [{count+1}/{total}] prop-{name}-{view}")
            url = gen_image(prompt, size=img_size)
            out.write_bytes(urllib.request.urlopen(url).read())
            url_map[f"prop-{name}-{view}"] = url
            track_file(project, "image_prop", str(out), f"道具 {name} {view}", f"style={style}")
            count += 1
            time.sleep(sleep_sec)

    # Save URLs
    if url_map:
        urls_file = proj_dir / "scripts" / f"{project}-image-urls.json"
        existing = {}
        if urls_file.exists():
            existing = json.loads(urls_file.read_text())
        existing.update(url_map)
        urls_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
        print(f"\n📝 URL 已追加到 {urls_file.name}")

    print(f"\n✅ 道具图完成")


if __name__ == "__main__":
    main()
