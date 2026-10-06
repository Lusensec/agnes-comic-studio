#!/usr/bin/env python3
"""Final video composition: merge clips + scene-aligned TTS + BGM + subtitles.

Requires: ffmpeg + ffprobe

All ffmpeg steps run with cwd=<project>/videos and RELATIVE file names, so
they work on Windows too (absolute paths with backslashes break ffmpeg's
concat demuxer and filtergraph). TTS lines are placed at their scene start
time ((scene-1) * video_duration) instead of being concatenated from t=0,
which used to truncate later lines with -shortest.

Usage:
    python final-compose.py "项目名" [--bgm path/to/music.mp3] [--no-subtitles] [--no-tts]

Output: videos/<project>-final.mp4
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import PROJECT_ROOT
from track import track_file


def run_ffmpeg(cmd: list, desc: str, cwd: Path) -> bool:
    print(f"   {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"   ❌ ffmpeg 失败 ({desc}):\n{result.stderr[-600:]}")
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    bgm_path = None
    no_subs = "--no-subtitles" in sys.argv
    no_tts = "--no-tts" in sys.argv
    if "--bgm" in sys.argv:
        idx = sys.argv.index("--bgm")
        if idx + 1 < len(sys.argv):
            bgm_path = sys.argv[idx + 1]

    proj_dir = PROJECT_ROOT / project
    video_dir = proj_dir / "videos"
    audio_dir = video_dir / "audio"
    out = video_dir / f"{project}-final.mp4"

    if not shutil.which("ffmpeg"):
        print("[ERROR] 需要 ffmpeg。安装: winget install Gyan.FFmpeg / brew install ffmpeg / apt install ffmpeg")
        sys.exit(1)

    clips = sorted(video_dir.glob("scene-*.mp4"))
    if not clips:
        print("[ERROR] 没有视频片段，先运行 gen-video.py")
        sys.exit(1)

    # Scene duration from the script JSON (used to align TTS lines to scenes)
    duration = 5
    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    if scripts:
        script = json.loads(scripts[0].read_text(encoding="utf-8"))
        try:
            duration = int(script.get("config", {}).get("video_duration", 5) or 5)
        except (TypeError, ValueError):
            pass

    print(f"🎬 最终合成: {project}")
    print(f"   片段: {len(clips)} 个 | TTS: {'否' if no_tts else '是'} | BGM: {'是' if bgm_path else '否'} | 字幕: {'否' if no_subs else '是'}\n")

    # --- 1. Concat clips (relative names, cwd=videos) -----------------------
    concat_file = video_dir / "concat_final.txt"
    concat_file.write_text(
        "\n".join(f"file '{c.name}'" for c in clips) + "\n", encoding="utf-8"
    )
    merged = video_dir / "merged-temp.mp4"
    if not run_ffmpeg(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", "concat_final.txt", "-c", "copy", merged.name],
        f"拼接 {len(clips)} 个片段", video_dir,
    ):
        sys.exit(1)
    current = merged

    # --- 2. TTS, scene-aligned ------------------------------------------------
    # line-<scene>-<idx>.mp3 starts at (scene-1)*duration + (idx-1)*2s
    audio_clips = sorted(audio_dir.glob("line-*.mp3"))
    if no_tts:
        print("   ⏭  跳过 TTS (--no-tts)")
    elif not audio_clips:
        print("   ⚠️  未找到 TTS 配音（先运行 gen-tts.py）")
    else:
        def _key(a: Path):
            p = a.stem.split("-")
            return (int(p[1]), int(p[2]))

        inputs, filter_parts = [], []
        for n, a in enumerate(audio_clips, start=1):
            sc, idx = _key(a)
            delay_ms = (sc - 1) * duration * 1000 + (idx - 1) * 2000
            inputs += ["-i", f"audio/{a.name}"]
            filter_parts.append(f"[{n}]adelay={delay_ms}|{delay_ms}[a{n}]")
        labels = "".join(f"[a{n}]" for n in range(1, len(audio_clips) + 1))
        filter_complex = (
            ";".join(filter_parts)
            + f";{labels}amix=inputs={len(audio_clips)}:normalize=0,apad[aout]"
        )
        with_audio = video_dir / "with-tts.mp4"
        if run_ffmpeg(
            ["ffmpeg", "-y", "-i", current.name] + inputs
            + ["-filter_complex", filter_complex,
               "-map", "0:v:0", "-map", "[aout]",
               "-c:v", "copy", "-c:a", "aac", "-shortest", with_audio.name],
            f"混音 {len(audio_clips)} 段配音（按场景对齐）", video_dir,
        ):
            current = with_audio
        else:
            print("   ⚠️  配音混音失败，最终成片将使用片段自带音频（如有）")

    # --- 3. BGM (if specified) ------------------------------------------------
    if bgm_path and Path(bgm_path).exists():
        with_bgm = video_dir / "with-bg.mp4"
        has_audio = current.name == "with-tts.mp4"
        if has_audio:
            cmd = [
                "ffmpeg", "-y", "-i", current.name, "-i", str(bgm_path),
                "-filter_complex",
                "[1:a]volume=0.3[bg];[0:a][bg]amix=inputs=2:duration=first[aout]",
                "-map", "0:v:0", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", "-shortest", with_bgm.name,
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-i", current.name, "-i", str(bgm_path),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-shortest", with_bgm.name,
            ]
        if run_ffmpeg(cmd, "叠加 BGM (音量 30%)", video_dir):
            current = with_bgm
    elif bgm_path:
        print(f"   ⚠️  BGM 文件不存在: {bgm_path}")

    # --- 4. Burn subtitles (relative srt path → no filtergraph escaping) ----
    srt = video_dir / "subtitles.srt"
    if no_subs:
        print("   ⏭  跳过字幕 (--no-subtitles)")
    elif srt.exists():
        final_tmp = video_dir / "final-subbed.mp4"
        if run_ffmpeg(
            ["ffmpeg", "-y", "-i", current.name,
             "-vf", "subtitles=subtitles.srt",
             "-c:v", "libx264", "-c:a", "copy", final_tmp.name],
            "烧录字幕", video_dir,
        ):
            current = final_tmp
        else:
            print("   ⚠️  字幕烧录失败，输出无字幕版本")
    else:
        print("   ⚠️  未找到字幕（先运行 gen-subtitles.py）")

    # --- 5. Finalize ----------------------------------------------------------
    shutil.move(str(current), str(out))
    track_file(project, "video_final", str(out), f"最终成片: {project}", "synthesized")

    for tmp in [merged, video_dir / "with-tts.mp4", video_dir / "with-bg.mp4",
                video_dir / "final-subbed.mp4", concat_file]:
        try:
            tmp.unlink()
        except (OSError, FileNotFoundError):
            pass

    size_mb = out.stat().st_size / 1024 / 1024
    print(f"\n✅ 最终成片: {out.name} ({size_mb:.1f}MB)")
    print(f"   片段: {len(clips)} | TTS: {'有' if not no_tts else '无'} | BGM: {'有' if bgm_path else '无'} | 字幕: {'有' if not no_subs else '无'}")


if __name__ == "__main__":
    main()
