#!/usr/bin/env python3
"""Generate short video clips from storyboard.

Uses image reference mode when URLs are available (from gen-storyboard.py).
Falls back to text mode if no URLs stored.

Rate limit (agnes-video-2.5-flash):
  - 1 次/分钟（每次提交间隔 >= 65s）
  - 图片参考最多 5 张
  - 音频参考最多 3 段
  - 不支持视频参考
  - size 固定 720P
  - 时长 4-12s

Usage:
    python gen-video.py "项目名" [--scene N] [--duration 5]
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY, PROJECT_ROOT
from track import track_file

BASE_VIDEO = "https://api.agnes-ai.cn/v1/videos"
BASE_POLL = "https://api.agnes-ai.cn/agnesapi"
VIDEO_INTERVAL_SEC = 65


def validate_duration(seconds: str) -> str:
    s = int(seconds)
    if s < 4:
        print(f"⚠️  时长 {s}s < 4s，自动调整为 4s")
        return "4"
    if s > 12:
        print(f"⚠️  时长 {s}s > 12s，自动调整为 12s")
        return "12"
    return str(s)


def load_image_urls(project: str) -> dict:
    """Load stored image URLs from gen-storyboard output."""
    urls_file = PROJECT_ROOT / project / "scripts" / f"{project}-image-urls.json"
    if urls_file.exists():
        return json.loads(urls_file.read_text(encoding="utf-8"))
    return {}


def submit_video(prompt: str, image_refs: list = None,
                 seconds: str = "5", aspect_ratio: str = "16:9") -> str:
    """Submit video task. Uses reference mode if image_refs provided."""
    # Validate: max 5 image refs
    refs = (image_refs or [])[:5]

    body = {
        "model": "agnes-video-2.5-flash",
        "prompt": prompt,
        "seconds": seconds,
        "size": "720P",
        "aspect_ratio": aspect_ratio,
    }

    if refs:
        body["mode"] = "reference"
        body["images"] = refs
    else:
        body["mode"] = "text"

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


def retry_api(func, max_retries=4):
    """Retry a submit on 429 (rate limit) and 503 (video_queue_full) with backoff.

    The Agnes video queue is shared and fills quickly at peak hours; waiting
    a few in-script retries (65s, 130s, 195s) usually beats the queue surge.
    If all retries fail the HTTPError is re-raised and the caller decides
    (main() fast-fails with exit code 3 so an outer runner can re-run later —
    completed scenes are skipped, so re-running is idempotent).
    """
    for attempt in range(max_retries):
        try:
            return func()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < max_retries - 1:
                wait = 65 * (attempt + 1)
                reason = "429 限流" if e.code == 429 else "503 视频队列已满"
                print(f"     ⏱  {reason}，等待 {wait}s 后重试 ({attempt+1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    scene_filter = None
    duration = None
    if "--scene" in sys.argv:
        scene_filter = int(sys.argv[sys.argv.index("--scene") + 1])
    if "--duration" in sys.argv:
        duration = validate_duration(sys.argv[sys.argv.index("--duration") + 1])

    proj_dir = PROJECT_ROOT / project
    video_dir = proj_dir / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    img_dir = proj_dir / "images"

    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    script = json.loads(scripts[0].read_text(encoding="utf-8")) if scripts else {}
    scenes = script.get("scenes", [])
    config = script.get("config", {})
    if duration is None:
        duration = validate_duration(str(config.get("video_duration", "5")))
    aspect_ratio = config.get("aspect_ratio", "16:9")

    # Load stored image URLs (for reference mode)
    image_urls = load_image_urls(project)
    has_urls = len(image_urls) > 0
    mode_label = "reference (图生视频)" if has_urls else "text (文生视频)"

    if scene_filter:
        scenes = [s for s in scenes if s.get("scene_id") == scene_filter]
    if not scenes:
        scene_files = sorted(img_dir.glob("scene-*.png"))
        scenes = [{"scene_id": int(f.stem.split("-")[1]), "title": f.stem,
                   "description": f.stem, "description_zh": f.stem} for f in scene_files]

    total = len(scenes)
    print(f"🎬 生成 {total} 个视频片段")
    print(f"   模式: {mode_label}")
    print(f"   时长: {duration}s/段 | 间隔: {VIDEO_INTERVAL_SEC}s")
    est_min = total * 5
    print(f"   预计总耗时: ~{est_min} 分钟\n")

    for i, scene in enumerate(scenes):
        sid = scene.get("scene_id", 0)
        out_file = video_dir / f"scene-{sid}.mp4"
        if out_file.exists():
            print(f"  ⏭  scene-{sid} 已存在，跳过")
            continue

        # Build image refs for this scene
        refs = []
        if has_urls:
            # Use the specific scene image + character refs
            scene_key = f"scene-{sid}"
            if scene_key in image_urls:
                refs.append(image_urls[scene_key])
            # Add character refs
            char_refs = [v for k, v in image_urls.items() if k.startswith("char-")]
            refs.extend(char_refs[:4])  # Keep total <= 5
            refs = refs[:5]

        # Build prompt
        desc_en = scene.get("description", "")
        desc_zh = scene.get("description_zh", "")
        style = config.get("style", "动画")
        style_word = {"动画": "anime", "写实": "cinematic", "水墨": "ink wash",
                      "赛博朋克": "cyberpunk", "二次元": "2D anime"}.get(style, "anime")
        prompt = f"{style_word} style, smooth animation. {desc_en}. {desc_zh[:60]}"

        print(f"  🎥 [{i+1}/{total}] scene-{sid}: {scene.get('title', '')[:30]}...")
        try:
            video_id = retry_api(
                lambda: submit_video(prompt, refs, duration, aspect_ratio)
            )
            print(f"     submitted: {video_id} ({len(refs)} refs)")
            video_url = poll_video(video_id)
            mp4_data = urllib.request.urlopen(video_url).read()
            out_file.write_bytes(mp4_data)
            track_file(project, "video", str(out_file), f"视频 scene-{sid}", f"duration={duration}s")
            print(f"     ✅ {out_file.name} ({len(mp4_data)//1024}KB)")
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                print(f"     ❌ scene-{sid} 提交失败 (HTTP {e.code})，重试 {4} 次后仍被限流/队列满")
                print("⚠️  Agnes 视频队列已满，本轮停止。稍后重新运行本脚本即可续跑（已完成的片段会自动跳过）。")
                sys.exit(3)
            print(f"     ❌ 提交失败 (HTTP {e.code}): {e.reason}")
        except Exception as e:
            print(f"     ❌ 失败: {e}")

        # Rate limit: wait before next
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
