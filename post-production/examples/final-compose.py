#!/usr/bin/env python3
"""Final video composition: merge clips + TTS + BGM + subtitles.

Requires: ffmpeg + ffprobe

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


def run_ffmpeg(cmd: list, desc: str):
    print(f"   {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ ffmpeg 失败: {result.stderr[:300]}")
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    bgm_path = None
    no_subs = False
    no_tts = False
    if "--bgm" in sys.argv:
        bgm_path = sys.argv[sys.argv.index("--bgm") + 1]
    if "--no-subtitles" in sys.argv:
        no_subs = True
    if "--no-tts" in sys.argv:
        no_tts = True

    proj_dir = PROJECT_ROOT / project
    video_dir = proj_dir / "videos"
    audio_dir = video_dir / "audio"
    out = video_dir / f"{project}-final.mp4"

    # Check ffmpeg
    if not shutil.which("ffmpeg"):
        print("[ERROR] 需要 ffmpeg。安装: apt install ffmpeg")
        sys.exit(1)

    # Step 1: Concatenate video clips
    clips = sorted(video_dir.glob("scene-*.mp4"))
    if not clips:
        print("[ERROR] 没有视频片段，先运行 gen-video.py")
        sys.exit(1)

    print(f"🎬 最终合成: {project}")
    print(f"   片段: {len(clips)} 个 | TTS: {'否' if no_tts else '是'} | BGM: {'是' if bgm_path else '否'} | 字幕: {'否' if no_subs else '是'}\n")

    # 1. Concat
    concat_file = video_dir / "concat_final.txt"
    concat_file.write_text("\n".join(f"file '{c}'" for c in [str(c) for c in clips]))
    merged = video_dir / "merged-temp.mp4"
    if not run_ffmpeg(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_file), "-c", "copy", str(merged)],
        f"拼接 {len(clips)} 个片段"
    ):
        sys.exit(1)

    # 2. Add TTS audio (if available)
    current = merged
    if not no_tts and list(audio_dir.glob("*.mp3")):
        # Mix all TTS clips with video
        audio_clips = sorted(audio_dir.glob("line-*.mp3"))
        if audio_clips:
            tts_mix = video_dir / "tts-mix.mp3"
            # Concat all TTS
            tts_concat = video_dir / "tts_concat.txt"
            tts_concat.write_text("\n".join(f"file '{a.name}'" for a in audio_clips))
            run_ffmpeg(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(tts_concat), "-c", "copy", str(tts_mix)],
                "合并 TTS 配音"
            )
            # Mux video + TTS
            with_audio = video_dir / "with-tts.mp4"
            run_ffmpeg(
                ["ffmpeg", "-y", "-i", str(merged), "-i", str(tts_mix),
                 "-c:v", "copy", "-c:a", "aac", "-shortest", str(with_audio)],
                "叠加 TTS 配音"
            )
            current = with_audio

    # 3. Add BGM (if specified)
    if bgm_path and Path(bgm_path).exists():
        with_bgm = video_dir / "with-bg.mp4"
        run_ffmpeg(
            ["ffmpeg", "-y", "-i", str(current), "-i", str(bgm_path),
             "-filter_complex", "[1:a]volume=0.3[bg];[0:a][bg]amix=inputs=2:duration=first[aout]",
             "-map", "0:v", "-map", "[aout]",
             "-c:v", "copy", "-c:a", "aac", "-shortest", str(with_bgm)],
            "叠加 BGM (音量 30%)"
        )
        current = with_bgm

    # 4. Burn subtitles
    srt = video_dir / "subtitles.srt"
    if not no_subs and srt.exists():
        final_tmp = video_dir / "final-subbed.mp4"
        # Escape path for ffmpeg filter
        srt_escaped = str(srt).replace(":", "\\:").replace("'", "'\\''")
        run_ffmpeg(
            ["ffmpeg", "-y", "-i", str(current),
             "-vf", f"subtitles='{srt_escaped}'",
             "-c:a", "copy", str(final_tmp)],
            "烧录字幕"
        )
        current = final_tmp

    # 5. Final output
    shutil.move(str(current), str(out))
    track_file(project, "video_final", str(out), f"最终成片: {project}", "synthesized")

    # Cleanup
    for tmp in [merged, video_dir / "with-tts.mp4", video_dir / "with-bg.mp4",
                video_dir / "final-subbed.mp4", concat_file]:
        if tmp.exists():
            tmp.unlink()

    size_mb = out.stat().st_size / 1024 / 1024
    print(f"\n✅ 最终成片: {out.name} ({size_mb:.1f}MB)")
    print(f"   片段: {len(clips)} | TTS: {'有' if not no_tts else '无'} | BGM: {'有' if bgm_path else '无'} | 字幕: {'有' if not no_subs else '无'}")


if __name__ == "__main__":
    main()
