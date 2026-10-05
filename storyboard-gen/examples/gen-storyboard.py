#!/usr/bin/env python3
"""Generate storyboard images from script JSON using agnes-image-2.5-flash.

Rate limits (agnes-image-2.5-flash):
  1K: 20/min | 2K: 10/min | 3K: 1/min | 4K: 1/min
Script auto-inserts appropriate sleep between calls.

Usage:
    python gen-storyboard.py "项目名" [--scene N] [--size 1K|2K]
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
    "动画": "anime style, clean lines, vibrant colors, ",
    "写实": "photorealistic, high detail, cinematic lighting, ",
    "水墨": "Chinese ink wash painting, minimalist, elegant, ",
    "赛博朋克": "cyberpunk, neon lights, futuristic, dark tones, ",
    "二次元": "2D anime, cute, pastel colors, soft shading, ",
}

# Sleep intervals based on rate limits
SLEEP_BY_SIZE = {"1K": 3, "2K": 7, "3K": 60, "4K": 60}


def gen_image(prompt: str, size="1K", ratio="16:9", ref_image_url="") -> str:
    body = {
        "model": "agnes-image-2.5-flash",
        "prompt": prompt,
        "size": size,
        "ratio": ratio,
        "extra_body": {"response_format": "url"}
    }
    if ref_image_url:
        body["extra_body"]["image"] = [ref_image_url]

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE_IMG, data=data,
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
    scene_filter = None
    image_size = None  # None = read from script config
    if "--scene" in sys.argv:
        scene_filter = int(sys.argv[sys.argv.index("--scene") + 1])
    if "--size" in sys.argv:
        image_size = sys.argv[sys.argv.index("--size") + 1]
        if image_size not in SLEEP_BY_SIZE:
            print(f"[ERROR] 无效尺寸 {image_size}，可选: {list(SLEEP_BY_SIZE.keys())}")
            sys.exit(1)

    sleep_sec = SLEEP_BY_SIZE[image_size] if image_size else SLEEP_BY_SIZE.get("1K", 3)

    proj_dir = PROJECT_ROOT / project
    img_dir = proj_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    # Find the script
    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    if not scripts:
        print(f"[ERROR] 未找到剧本，请先运行 write-script.py", file=sys.stderr)
        sys.exit(1)
    script = json.loads(scripts[0].read_text())
    style = script.get("style", "动画")
    style_prefix = STYLE_PREFIX.get(style, "")
    # Read config: aspect_ratio, image size
    config = script.get("config", {})
    if image_size is None:
        image_size = config.get("image_size", "1K")
        sleep_sec = SLEEP_BY_SIZE.get(image_size, 3)
    aspect_ratio = config.get("aspect_ratio", "16:9")

    scenes = script.get("scenes", [])
    if scene_filter:
        scenes = [s for s in scenes if s.get("scene_id") == scene_filter]

    if not scenes:
        print(f"未找到 scene {scene_filter}")
        sys.exit(1)

    print(f"⏱  图片尺寸: {image_size} | 间隔: {sleep_sec}s | 速率: {20//max(sleep_sec,1)}张/min")

    # Generate character reference images first
    char_urls = {}
    chars = script.get("characters", [])
    for i, ch in enumerate(chars):
        name = ch["name"]
        desc = ch.get("description", name)
        out_file = img_dir / f"character-{name}.png"
        if out_file.exists() and not scene_filter:
            print(f"  ⏭  角色 [{name}] 已有参考图，跳过")
            continue
        print(f"  🎨 生成角色参考 [{i+1}/{len(chars)}]: {name}")
        prompt = f"{style_prefix}character design sheet, full body, {desc}, white background"
        url = gen_image(prompt, size=image_size, ratio="1:1")
        char_urls[name] = url
        img_data = urllib.request.urlopen(url).read()
        out_file.write_bytes(img_data)
        print(f"     ✅ {out_file.name}")
        track_file(project, "image", str(out_file), f"角色参考: {name}", f"style={style}")
        if i < len(chars) - 1:
            time.sleep(sleep_sec)

    # Generate scene images
    print(f"\n📷 生成 {len(scenes)} 张分镜图...")
    ref_url = list(char_urls.values())[0] if char_urls else ""

    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id", 0)
        desc_en = scene.get("description", scene.get("description_zh", ""))
        prompt = f"{style_prefix}{desc_en}"

        print(f"  [{i+1}/{len(scenes)}] scene-{sid}: {scene.get('title', '')[:30]}...")
        img_url = gen_image(prompt, size=image_size, ratio=aspect_ratio,
                            ref_image_url=ref_url)

        out_file = img_dir / f"scene-{sid}.png"
        img_data = urllib.request.urlopen(img_url).read()
        out_file.write_bytes(img_data)
        print(f"     ✅ {out_file.name}")
        track_file(project, "image", str(out_file), f"分镜 {sid}: {scene.get('title','')}", f"style={style},scene={sid}")

        # Rate limit: sleep between calls (not after last)
        if i < len(scenes) - 1:
            time.sleep(sleep_sec)

    print(f"\n✅ 分镜图完成 ({len(scenes)} 张)，保存在 {img_dir}/")
    print("\n下一步：")
    print(f"  [1] 生成视频 → python video-composer/examples/gen-video.py \"{project}\"")
    print(f"  [2] 重新生成某场景 → python gen-storyboard.py \"{project}\" --scene N")
    print(f"  [3] 调整风格 → 修改剧本 style 字段后重新运行")


if __name__ == "__main__":
    main()
