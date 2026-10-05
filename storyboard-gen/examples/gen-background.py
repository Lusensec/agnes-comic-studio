#!/usr/bin/env python3
"""Generate standalone background/scene images (no characters).

Usage:
    python gen-background.py "项目名" [场景ID]
    不带场景ID则生成所有场景的背景

从剧本 JSON 中读取场景描述，生成无角色的纯背景图。
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
STYLE_PREFIX = {
    "动画": "anime background art, clean lines, vibrant colors, no characters, ",
    "写实": "cinematic background, photorealistic, no people, ",
    "水墨": "Chinese ink wash landscape, minimalist, no figures, ",
    "赛博朋克": "cyberpunk cityscape, neon lights, no people, ",
    "二次元": "2D anime background, pastel colors, no characters, ",
}


def gen_image(prompt: str, size="1K", ratio="16:9") -> str:
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
    scene_id = None
    if len(sys.argv) > 2:
        scene_id = int(sys.argv[2])

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
    aspect_ratio = config.get("aspect_ratio", "16:9")
    style_prefix = STYLE_PREFIX.get(style, "")

    scenes = script.get("scenes", [])
    if scene_id:
        scenes = [s for s in scenes if s.get("scene_id") == scene_id]

    print(f"🏞  生成 {len(scenes)} 张纯背景图（无角色）...")
    sleep_sec = 7 if img_size == "2K" else 3

    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id", 0)
        desc_en = scene.get("description", "")
        # Remove character references from the prompt
        prompt = f"{style_prefix}{desc_en}. Empty environment, no people, no characters."

        out = img_dir / f"bg-{sid}.png"
        print(f"  [{i+1}/{len(scenes)}] bg-{sid}: {scene.get('title', '')[:30]}...")
        url = gen_image(prompt, size=img_size, ratio=aspect_ratio)
        out.write_bytes(urllib.request.urlopen(url).read())
        track_file(project, "image_background", str(out), f"背景 {sid}: {scene.get('title','')}", f"style={style}")
        print(f"     ✅ {out.name}")

        if i < len(scenes) - 1:
            time.sleep(sleep_sec)

    print(f"\n✅ 背景图完成，保存在 {img_dir}/")


if __name__ == "__main__":
    main()
