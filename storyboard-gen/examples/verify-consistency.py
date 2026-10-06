#!/usr/bin/env python3
"""Verify character consistency between three-view and storyboard images.

Uses agnes-2.5-flash vision to compare. If mismatch > threshold, suggests regeneration.

Usage:
    python verify-consistency.py "项目名" [场景ID]
    
Output:
    Prints consistency report. If low score, suggests which scenes to regenerate.
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY, PROJECT_ROOT

BASE = "https://api.agnes-ai.cn/v1/chat/completions"

SYSTEM_PROMPT = """你是角色一致性审核员。对比角色参考图和场景图，评估角色外观一致性。
输出 JSON：
{
  "score": 0-100,
  "issues": ["具体不一致的地方"],
  "pass": true/false,
  "suggestion": "建议"
}
score > 70 为通过。"""


def check_consistency(ref_url: str, scene_url: str, char_name: str) -> dict:
    """Compare character three-view with a scene image."""
    data = json.dumps({
        "model": "agnes-2.5-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": f"对比以下两张图中角色 [{char_name}] 的外观一致性。图1是角色三视图参考，图2是场景图。检查：脸型、发型、服装、体型是否一致。"},
                {"type": "image_url", "image_url": {"url": ref_url}},
                {"type": "image_url", "image_url": {"url": scene_url}}
            ]
        }],
        "temperature": 0.1,
        "max_tokens": 512
    }).encode()
    req = urllib.request.Request(
        BASE, data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=60).read()
    raw = json.loads(resp)["choices"][0]["message"]["content"]
    
    # Parse JSON from response
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start < 0:
        return {"score": -1, "issues": [f"无法解析: {raw[:100]}"], "pass": False, "suggestion": "重试"}
    return json.loads(raw[start:end])


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    scene_filter = int(sys.argv[2]) if len(sys.argv) > 2 else None

    proj_dir = PROJECT_ROOT / project
    urls_file = proj_dir / "scripts" / f"{project}-image-urls.json"
    if not urls_file.exists():
        print("[ERROR] 未找到 image-urls.json")
        sys.exit(1)
    urls = json.loads(urls_file.read_text(encoding="utf-8"))

    scripts = list((proj_dir / "scripts").glob(f"{project}-script.json"))
    script = json.loads(scripts[0].read_text(encoding="utf-8")) if scripts else {}
    scenes = script.get("scenes", [])

    # Get three-view refs
    char_views = {k: v for k, v in urls.items() if "three-view" in k}
    if not char_views:
        print("⚠️  没有找到三视图 URL。跳过校验。")
        return

    if scene_filter:
        scenes = [s for s in scenes if s.get("scene_id") == scene_filter]

    print(f"🔍 角色一致性校验: {len(scenes)} 个场景 × {len(char_views)} 个角色\n")

    all_pass = True
    for scene in scenes:
        sid = scene.get("scene_id", 0)
        scene_key = f"scene-{sid}"
        if scene_key not in urls:
            continue

        scene_url = urls[scene_key]
        print(f"  scene-{sid}: {scene.get('title','')[:30]}...")
        
        for char_key, char_url in char_views.items():
            char_name = char_key.replace("three-view-", "").strip()
            result = check_consistency(char_url, scene_url, char_name)
            score = result.get("score", -1)
            passed = result.get("pass", False)
            mark = "✅" if passed else "❌"
            
            if not passed:
                all_pass = False
            print(f"     {mark} [{char_name}] score={score}")
            
            for issue in result.get("issues", [])[:2]:
                print(f"        - {issue}")

    if all_pass:
        print(f"\n✅ 全部通过！角色一致性良好。")
    else:
        print(f"\n⚠️  有不一致场景。建议：")
        print(f"   1. 重新生成三视图（确认角色外观正确）")
        print(f"   2. 用 --scene N 重新生成对应分镜")
        print(f"   3. 在 prompt 中写更具体的角色描述")


if __name__ == "__main__":
    main()
