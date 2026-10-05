#!/usr/bin/env python3
"""Generate multi-angle background images (wide/mid/close) for each scene.

Usage:
    python gen-background.py "项目名" [场景ID]
    
Outputs:
    images/bg-<id>-wide.png    (environment overview)
    images/bg-<id>-mid.png     (main area)
    images/bg-<id>-close.png   (key detail)
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
    "写实": "cinematic environment, photorealistic, no people, ",
    "水墨": "Chinese ink wash landscape, minimalist, no figures, ",
    "赛博朋克": "cyberpunk cityscape, neon lights, no people, ",
    "二次元": "2D anime background, pastel colors, no characters, ",
}

ANGLES = {
    "wide": "extreme wide shot, establishing shot, full environment visible, ",
    "mid": "medium shot, main focal area, ",
    "close": "close-up detail shot, texture and light focus, ",
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
    scene_id = int(sys.argv[2]) if len(sys.argv) > 2 else None

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

    sleep_sec = 3 if img_size == "1K" else 7
    total = len(scenes) * 3
    print(f"🏞  生成 {len(scenes)} 个场景 × 3 角度 = {total} 张背景图...")

    url_map = {}
    count = 0
    for scene in scenes:
        sid = scene.get("scene_id", 0)
        desc_en = scene.get("description", "")
        
        for angle, angle_prefix in ANGLES.items():
            out = img_dir / f"bg-{sid}-{angle}.png"
            if out.exists():
                print(f"  ⏭  bg-{sid}-{angle} 已存在")
                continue
            
            prompt = f"{style_prefix}{angle_prefix}{desc_en}. Empty environment, no characters, no people."
            print(f"  🏞  [{count+1}/{total}] bg-{sid}-{angle}: {scene.get('title','')[:20]}")
            url = gen_image(prompt, size=img_size, ratio=aspect_ratio)
            out.write_bytes(urllib.request.urlopen(url).read())
            url_map[f"bg-{sid}-{angle}"] = url
            track_file(project, "image_background", str(out), f"背景 {sid} {angle}", f"style={style}")
            print(f"     ✅ {out.name}")
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

    print(f"\n✅ 背景图完成")


if __name__ == "__main__":
    main()
