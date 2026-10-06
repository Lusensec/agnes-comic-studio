#!/usr/bin/env python3
"""Generate TTS voice-over for character dialogue.

Uses edge-tts (free) or Agnes AI TTS.

Usage:
    python gen-tts.py "项目名" [场景ID]
    不带场景ID则生成所有场景的配音

输出: videos/audio/line-<scene>-<index>.mp3
"""
import json
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import PROJECT_ROOT
from track import track_file

# Voice assignments (edge-tts voices)
VOICES = {
    "male_default": "zh-CN-YunxiNeural",
    "female_default": "zh-CN-XiaoxiaoNeural",
    "elder_female": "zh-CN-XiaoxiaoNeural",
    "narrator": "zh-CN-YunjianNeural",
}


def get_voice_for_character(char: dict) -> str:
    """Pick a voice based on character description."""
    desc = (char.get("description", "") + char.get("personality", "")).lower()
    if "老" in desc or "奶" in desc or "grandma" in desc or "elder" in desc:
        return VOICES["elder_female"]
    if "女" in desc or "girl" in desc or "woman" in desc or "她" in desc:
        return VOICES["female_default"]
    return VOICES["male_default"]


def synthesize_edge_tts(text: str, voice: str, out_path: Path):
    """Use edge-tts to generate audio."""
    try:
        import asyncio
        import edge_tts

        async def _gen():
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    with open(out_path, "ab") as f:
                        f.write(chunk["data"])

        out_path.write_bytes(b"")  # Clear
        asyncio.run(_gen())
        return True
    except ImportError:
        print("  [INFO] edge-tts 未安装，尝试 pip install...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "edge-tts"], check=True)
        # Retry
        import edge_tts
        return synthesize_edge_tts(text, voice, out_path)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    scene_filter = None
    if len(sys.argv) > 2:
        scene_filter = int(sys.argv[2])

    proj_dir = PROJECT_ROOT / project
    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    if not scripts:
        print("[ERROR] 未找到剧本", file=sys.stderr)
        sys.exit(1)
    script = json.loads(scripts[0].read_text(encoding="utf-8"))

    # Build character voice map
    voice_map = {}
    for ch in script.get("characters", []):
        voice_map[ch["name"]] = get_voice_for_character(ch)

    scenes = script.get("scenes", [])
    if scene_filter:
        scenes = [s for s in scenes if s.get("scene_id") == scene_filter]

    audio_dir = proj_dir / "videos" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    print(f"🎙  生成 TTS 配音...")
    print(f"   音色分配: {voice_map}\n")

    count = 0
    for scene in scenes:
        sid = scene.get("scene_id", 0)
        for i, dialog in enumerate(scene.get("dialogue", [])):
            line = dialog.get("line", "")
            # Skip non-speech (actions in parentheses)
            if line.startswith("(") and line.endswith(")"):
                continue
            char = dialog.get("character", "旁白")
            voice = voice_map.get(char, VOICES["narrator"])

            out_file = audio_dir / f"line-{sid}-{i+1}.mp3"
            if out_file.exists():
                print(f"  ⏭  line-{sid}-{i+1} 已存在")
                continue

            print(f"  🎙  scene-{sid} [{char}]: {line[:30]}...")
            synthesize_edge_tts(line, voice, out_file)
            track_file(project, "audio", str(out_file), f"TTS: {char} - {line[:30]}", f"scene={sid}")
            print(f"     ✅ {out_file.name}")
            count += 1

    print(f"\n✅ TTS 配音完成 ({count} 段)，保存在 {audio_dir}/")
    print(f"\n下一步：")
    print(f"  [1] 生成字幕 → python gen-subtitles.py \"{project}\"")
    print(f"  [2] 最终合成 → python final-compose.py \"{project}\"")


if __name__ == "__main__":
    main()
