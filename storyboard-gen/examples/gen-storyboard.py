#!/usr/bin/env python3
"""Generate storyboard images using multi-reference I2I.

Reference strategy:
  - Character three-view (strongest identity anchor)
  - Current scene background (angle matching: wide/mid/close)
  - Related props for this scene (if defined in script)
  Max 5 refs total (Agnes limit).

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
SLEEP_BY_SIZE = {"1K": 3, "2K": 7, "3K": 60, "4K": 60}


def gen_image(prompt: str, size="1K", ratio="16:9", ref_urls: list = None) -> str:
    body = {
        "model": "agnes-image-2.5-flash",
        "prompt": prompt,
        "size": size,
        "ratio": ratio,
        "extra_body": {"response_format": "url"}
    }
    if ref_urls:
        body["extra_body"]["image"] = ref_urls[:5]  # Max 5
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE_IMG, data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=360).read()
    return json.loads(resp)["data"][0]["url"]


def load_urls(project: str) -> dict:
    """Load all stored image URLs."""
    f = PROJECT_ROOT / project / "scripts" / f"{project}-image-urls.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    return {}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    scene_filter = None
    image_size = None
    if "--scene" in sys.argv:
        scene_filter = int(sys.argv[sys.argv.index("--scene") + 1])
    if "--size" in sys.argv:
        image_size = sys.argv[sys.argv.index("--size") + 1]

    sleep_sec = SLEEP_BY_SIZE.get(image_size or "1K", 3)

    proj_dir = PROJECT_ROOT / project
    img_dir = proj_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    if not scripts:
        print("[ERROR] 未找到剧本", file=sys.stderr)
        sys.exit(1)
    script = json.loads(scripts[0].read_text(encoding="utf-8"))
    config = script.get("config", {})
    style = config.get("style", "动画")
    style_prefix = STYLE_PREFIX.get(style, "")
    if image_size is None:
        image_size = config.get("image_size", "1K")
        sleep_sec = SLEEP_BY_SIZE.get(image_size, 3)
    aspect_ratio = config.get("aspect_ratio", "16:9")

    # Load all available URLs (character three-views, backgrounds, props)
    urls = load_urls(project)

    # Build character three-view refs (one per character)
    char_refs = [v for k, v in urls.items() if "three-view" in k]

    scenes = script.get("scenes", [])
    if scene_filter:
        scenes = [s for s in scenes if s.get("scene_id") == scene_filter]

    print(f"📷 生成 {len(scenes)} 张分镜图...")
    print(f"   参考策略: 角色三视图({len(char_refs)}张) + 场景背景 + 相关道具")
    print(f"   每场景最多 5 张参考\n")

    url_map = {}
    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id", 0)
        desc_en = scene.get("description", "")
        desc_zh = scene.get("description_zh", desc_en)

        # Build reference set for this scene
        refs = []
        # 1. Character three-view (highest priority)
        refs.extend(char_refs[:2])  # Max 2 character refs

        # 2. Scene background (pick "mid" angle as best match for storyboard)
        bg_key = f"bg-{sid}-mid"
        if bg_key in urls:
            refs.append(urls[bg_key])

        # 3. Related props (from scene.props if defined)
        scene_props = scene.get("props", [])
        for pname in scene_props[:2]:  # Max 2 prop refs
            prop_key = f"prop-{pname}-front"
            if prop_key in urls:
                refs.append(urls[prop_key])

        refs = refs[:5]  # Hard limit

        # Build prompt with explicit reference guidance
        ref_desc = ""
        if refs:
            ref_desc = f" [Reference images: {', '.join([r.split('/')[-1][:20] for r in refs])}]"
        prompt = f"{style_prefix}{desc_en}. Maintain character consistency with reference images.{ref_desc}"

        print(f"  [{i+1}/{len(scenes)}] scene-{sid}: {scene.get('title','')[:25]}... ({len(refs)} refs)")
        img_url = gen_image(prompt, size=image_size, ratio=aspect_ratio, ref_urls=refs)
        url_map[f"scene-{sid}"] = img_url

        out_file = img_dir / f"scene-{sid}.png"
        out_file.write_bytes(urllib.request.urlopen(img_url).read())
        track_file(project, "image", str(out_file), f"分镜 {sid}: {scene.get('title','')}",
                   f"style={style},refs={len(refs)}")
        print(f"     ✅ {out_file.name}")

        if i < len(scenes) - 1:
            time.sleep(sleep_sec)

    # Save scene URLs
    if url_map:
        save_file = proj_dir / "scripts" / f"{project}-image-urls.json"
        existing = json.loads(save_file.read_text(encoding="utf-8")) if save_file.exists() else {}
        existing.update(url_map)
        save_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📝 分镜 URL 已保存")

    print(f"\n✅ 分镜图完成 ({len(scenes)} 张)，每场景 {len(refs)} 张参考 I2I")
    print("\n下一步：")
    print(f"  [1] 生成视频 → python video-composer/examples/gen-video.py \"{project}\"")
    print(f"  [2] 重新生成 → python gen-storyboard.py \"{project}\" --scene N")


if __name__ == "__main__":
    main()
