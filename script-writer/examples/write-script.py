#!/usr/bin/env python3
"""Generate a structured comic script using agnes-3.0-flash.

Usage:
    python write-script.py "项目名" "故事概念" [风格] [方向] [时长] [尺寸]
    风格: 动画|写实|水墨|赛博朋克|二次元 (default: 动画)
    方向: landscape(16:9)|portrait(9:16) (default: landscape)
    时长: 4-12 (default: 5)
    尺寸: 1K|2K (default: 1K)

Examples:
    python write-script.py "项目" "概念"
    python write-script.py "项目" "概念" 动画 portrait 8 2K
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from load_env import API_KEY, PROJECT_ROOT
from track import track_file

BASE = "https://api.agnes-ai.cn/v1/chat/completions"

SYSTEM_PROMPT = """你是专业漫剧编剧。根据用户的故事概念，输出严格 JSON（不要 markdown 代码块），结构：
{
  "logline": "一句话概括",
  "characters": [
    {"name": "角色名", "description": "外貌详细描述(用于生图)", "personality": "性格", "role": "主角/配角"}
  ],
  "props": [
    {"name": "道具名", "description": "外观详细描述(用于生图，材质/颜色/尺寸)"}
  ],
  "scenes": [
    {
      "scene_id": 1,
      "title": "场景标题",
      "description": "画面描述(英文，用于生图提示词，包含角色外观+动作+场景+光线)",
      "description_zh": "画面描述(中文，供阅读)",
      "dialogue": [
        {"character": "角色名", "line": "台词", "emotion": "情绪"}
      ]
    }
  ]
}
场景数 3-8 个。台词硬性约束：每个场景 1-2 句、每句不超过 15 个汉字——台词会被 TTS 配音，必须装进用户指定的"每场景时长"，超长句子会被截断或互相叠音，宁短勿长。props 列出故事中出现的 2-5 个关键道具/物品。"""


def call_agnes(prompt: str, model: str = "agnes-3.0-flash") -> str:
    data = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 8192
    }).encode()
    req = urllib.request.Request(
        BASE, data=data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=120).read()
    return json.loads(resp)["choices"][0]["message"]["content"]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    project = sys.argv[1]
    concept = sys.argv[2]
    style = sys.argv[3] if len(sys.argv) > 3 else "动画"
    orientation = sys.argv[4] if len(sys.argv) > 4 else "landscape"
    duration = sys.argv[5] if len(sys.argv) > 5 else "5"
    img_size = sys.argv[6] if len(sys.argv) > 6 else "1K"

    # Validate
    valid_orient = ["landscape", "portrait"]
    if orientation not in valid_orient:
        print(f"[ERROR] 方向无效: {orientation}，可选: {valid_orient}")
        sys.exit(1)
    valid_sizes = ["1K", "2K", "3K", "4K"]
    if img_size not in valid_sizes:
        print(f"[ERROR] 尺寸无效: {img_size}，可选: {valid_sizes}")
        sys.exit(1)
    duration = str(max(4, min(12, int(duration))))

    aspect_ratio = "16:9" if orientation == "landscape" else "9:16"
    ratio_label = "横屏" if orientation == "landscape" else "竖屏"

    proj_dir = PROJECT_ROOT / project
    script_dir = proj_dir / "scripts"
    script_dir.mkdir(parents=True, exist_ok=True)

    print(f"📝 正在生成剧本...")
    print(f"   项目: {project}")
    print(f"   概念: {concept}")
    print(f"   风格: {style} | {ratio_label}({aspect_ratio}) | {duration}s | {img_size}\n")

    prompt = f"项目名: {project}\n故事概念: {concept}\n风格: {style}\n画面方向: {ratio_label}\n每场景时长: {duration}秒"
    raw = call_agnes(prompt)

    # Extract JSON
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start < 0 or end <= start:
        print("[ERROR] 模型未返回有效 JSON:\n" + raw[:500])
        sys.exit(1)

    script = json.loads(raw[start:end])
    script["project"] = project
    script["style"] = style
    script["config"] = {
        "orientation": orientation,
        "aspect_ratio": aspect_ratio,
        "video_duration": duration,
        "image_size": img_size,
        "style": style
    }
    script["created_at"] = datetime.now(timezone.utc).isoformat()

    out = script_dir / f"{project}-script.json"
    out.write_text(json.dumps(script, ensure_ascii=False, indent=2), encoding="utf-8")
    track_file(project, "script", str(out), f"剧本: {concept[:50]}", f"风格={style},场景数={len(script.get('scenes',[]))}")

    n_chars = len(script.get("characters", []))
    n_scenes = len(script.get("scenes", []))
    print(f"✅ 剧本已保存: {out}")
    print(f"   角色: {n_chars} 个 | 场景: {n_scenes} 个")
    print(f"   配置: {ratio_label} | {style} | {duration}s/段 | {img_size}\n")

    print("下一步：")
    print(f"  [1] 继续生成分镜图 → python storyboard-gen/examples/gen-storyboard.py \"{project}\"")
    print(f"  [2] 修改剧本 → 编辑 {out.name} 后重新运行")
    print(f"  [3] 调整某角色 → python refine-script.py \"{project}\" \"角色名\" \"新描述\"")


if __name__ == "__main__":
    main()
