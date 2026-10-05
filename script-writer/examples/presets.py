"""Template presets for common use cases.

Import and use in write-script.py or standalone:
    python presets.py [preset_name]
"""

PRESETS = {
    "douyin": {
        "description": "抖音竖屏短剧（快节奏、强反转）",
        "orientation": "portrait",
        "aspect_ratio": "9:16",
        "video_duration": "5",
        "image_size": "1K",
        "style": "动画",
        "scene_count": "6-8",
        "extra_prompt": "节奏快，每段有明确情绪转折，适合竖屏短视频平台"
    },
    "bilibili": {
        "description": "B站横屏动画（叙事完整、节奏适中）",
        "orientation": "landscape",
        "aspect_ratio": "16:9",
        "video_duration": "8",
        "image_size": "2K",
        "style": "二次元",
        "scene_count": "8-12",
        "extra_prompt": "叙事完整，节奏适中，画面精美，适合B站动画区"
    },
    "xhs": {
        "description": "小红书图文漫剧（静态图为主，少视频）",
        "orientation": "portrait",
        "aspect_ratio": "3:4",
        "video_duration": "4",
        "image_size": "2K",
        "style": "二次元",
        "scene_count": "6-8",
        "extra_prompt": "偏静态画面，构图精美，适合小红书图文发布"
    },
    "weibo": {
        "description": "微博/朋友圈短动画（3-5秒、轻松向）",
        "orientation": "landscape",
        "aspect_ratio": "1:1",
        "video_duration": "4",
        "image_size": "1K",
        "style": "动画",
        "scene_count": "3-5",
        "extra_prompt": "轻松有趣，短小精悍，适合社交媒体分享"
    },
}


def list_presets():
    print("可用预设：")
    for name, p in PRESETS.items():
        print(f"  {name:<12s} {p['description']}")
    print("\n使用: python presets.py douyin")


def get_preset(name: str) -> dict:
    if name not in PRESETS:
        print(f"[ERROR] 未知预设 '{name}'。可选: {list(PRESETS.keys())}")
        return {}
    return PRESETS[name]


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) > 1:
        p = get_preset(sys.argv[1])
        if p:
            print(json.dumps(p, ensure_ascii=False, indent=2))
    else:
        list_presets()
