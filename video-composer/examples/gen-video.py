#!/usr/bin/env python3
"""Generate short video clips from storyboard.

Rate limit (agnes-video-2.5-flash):
  - 1 次/分钟（每次提交间隔 >= 65s）
  - 图片参考最多 5 张
  - 音频参考最多 3 段
  - 不支持视频参考
  - size 固定 720P
  - 时长 4-12s

Usage:
    python gen-video.py "项目名" [--scene N] [--duration 5]
    duration: 4-12 (default 5)
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY, PROJECT_ROOT
from track import track_file

BASE_VIDEO = "https://api.agnes-ai.cn/v1/videos"
BASE_POLL = "https://api.agnes-ai.cn/agnesapi"

VIDEO_INTERVAL_SEC = 65  # 1/min rate limit, add buffer


def validate_duration(seconds: str) -> str:
    s = int(seconds)
    if s < 4:
        print(f"⚠️  时长 {s}s < 4s，自动调整为 4s")
        return "4"
    if s > 12:
        print(f"⚠️  时长 {s}s > 12s，自动调整为 12s")
        return "12"
    return str(s)


def submit_video(prompt: str, ref_image_url: str = "", mode: str = "text",
                 seconds: str = "5", image_refs: list = None, aspect_ratio: str = "16:9") -> str:
    # Validate
    if len(image_refs or []) > 5:
        print("⚠️  图片参考超过 5 张，截取前 5 张")
        image_refs = (image_refs or [])[:5]

    body = {
        "model": "agnes-video-2.5-flash",
        "prompt": prompt,
        "seconds": seconds,
        "mode": mode,
        "size": "720P",  # Fixed
        "aspect_ratio": aspect_ratio
    }
    if ref_image_url and ref_image_url.startswith("http"):
        body["mode"] = "reference"
        body["images"] = [ref_image_url]
    elif image_refs:
        body["mode"] = "reference"
        body["images"] = image_refs[:5]

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE_VIDEO, data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=120).read()
    return json.loads(resp)["video_id"]


def poll_video(video_id: str, timeout=600, interval=30) -> str:
    elapsed = 0
    while elapsed < timeout:
        url = f"{BASE_POLL}?video_id={video_id}&model_name=agnes-video-2.5-flash"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {API_KEY}"})
        resp = urllib.request.urlopen(req, timeout=60).read()
        result = json.loads(resp)
        status = result.get("status", "")
        progress = result.get("progress", 0)
        print(f"     status={status} progress={progress}%")
        if status == "completed":
            return result.get("url", "")
        if status == "failed":
            raise RuntimeError(f"Video failed: {result.get('error')}")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"Video {video_id} not ready after {timeout}s")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    scene_filter = None
    duration = None  # None = read from script config
    if "--scene" in sys.argv:
        scene_filter = int(sys.argv[sys.argv.index("--scene") + 1])
    if "--duration" in sys.argv:
        duration = validate_duration(sys.argv[sys.argv.index("--duration") + 1])

    proj_dir = PROJECT_ROOT / project
    video_dir = proj_dir / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    img_dir = proj_dir / "images"

    # Load script
    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    script = json.loads(scripts[0].read_text()) if scripts else {}
    scenes = script.get("scenes", [])
    # Read config: duration, aspect_ratio
    config = script.get("config", {})
    if duration is None:
        duration = validate_duration(str(config.get("video_duration", "5")))
    aspect_ratio = config.get("aspect_ratio", "16:9")

    if scene_filter:
        scenes = [s for s in scenes if s.get("scene_id") == scene_filter]

    if not scenes:
        scene_files = sorted(img_dir.glob("scene-*.png"))
        scenes = [{"scene_id": int(f.stem.split("-")[1]), "title": f.stem,
                   "description": f.stem, "description_zh": f.stem} for f in scene_files]

    total = len(scenes)
    print(f"🎬 生成 {total} 个视频片段")
    print(f"   时长: {duration}s/段 | 总计约 {total * (int(duration) + 30)}s (~{total * 5}min)")
    print(f"   速率限制: 1次/分钟，自动间隔 {VIDEO_INTERVAL_SEC}s\n")

    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id", 0)
        out_file = video_dir / f"scene-{sid}.mp4"
        if out_file.exists():
            print(f"  ⏭  scene-{sid} 已存在，跳过")
            continue

        # Build prompt
        desc_en = scene.get("description", "")
        desc_zh = scene.get("description_zh", "")
        prompt = f"Anime style, smooth animation. {desc_en}. {desc_zh[:60]}"

        print(f"  🎥 [{i+1}/{total}] scene-{sid}: {scene.get('title', '')[:30]}...")
        try:
            video_id = submit_video(prompt, mode="text", seconds=duration, aspect_ratio=aspect_ratio)
            print(f"     submitted: {video_id}")
            video_url = poll_video(video_id)
            mp4_data = urllib.request.urlopen(video_url).read()
            out_file.write_bytes(mp4_data)
            print(f"     ✅ {out_file.name} ({len(mp4_data)//1024}KB)")
            track_file(project, "video", str(out_file), f"视频 scene-{sid}: {scene.get('title','')}", f"duration={duration}s")
        except Exception as e:
            print(f"     ❌ 失败: {e}")

        # Rate limit: wait before next submission
        if i < total - 1:
            remaining = total - i - 1
            print(f"     ⏱  等待 {VIDEO_INTERVAL_SEC}s (剩余 {remaining} 个)...")
            time.sleep(VIDEO_INTERVAL_SEC)

    print(f"\n✅ 视频生成完成，保存在 {video_dir}/")
    print("\n下一步：")
    print(f"  [1] 拼接完整视频 → python merge-videos.py \"{project}\"")
    print(f"  [2] 重新生成某场景 → python gen-video.py \"{project}\" --scene N")
    print(f"  [3] 完成 🎬")


if __name__ == "__main__":
    main()
