# Agnes Flash Suite（基础能力层）

> 直接封装 Agnes AI API 调用，供其他子 Skill 或用户独立使用。

## 模型列表

| 模型 ID | 能力 | 端点 |
|---------|------|------|
| `agnes-3.0-flash` | Agent 编程、推理、工具编排 | `/v1/chat/completions` |
| `agnes-2.5-flash` | 对话、推理、图像理解、工具调用 | `/v1/chat/completions` |
| `agnes-image-2.5-flash` | 文生图、图生图、多图合成 | `/v1/images/generations` |
| `agnes-video-2.5-flash` | 文生视频、图片参考、首尾帧 | `/v1/videos` |

## API 调用

API Key 从 `.env` 文件加载（环境变量 `AGNESAI_API_KEY`）。

```python
import json, urllib.request, os

API_KEY = os.environ.get("AGNESAI_API_KEY")

# 文生图
data = json.dumps({
    "model": "agnes-image-2.5-flash",
    "prompt": "描述",
    "size": "1K",
    "ratio": "16:9",
    "extra_body": {"response_format": "url"}
}).encode()

req = urllib.request.Request(
    "https://api.agnes-ai.cn/v1/images/generations",
    data=data,
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=360).read()
image_url = json.loads(resp)["data"][0]["url"]
```

## 速率限制

| 模型 | 限制 |
|------|------|
| `agnes-image-2.5-flash` | 1K: 20次/分, 2K: 10次/分, 3K: 1次/分, 4K: 1次/分 |
| `agnes-video-2.5-flash` | **1次/分**；图片参考最多 5 张；音频参考最多 3 段；不支持视频参考；size 固定 720P；时长 4-12s |

脚本内置 sleep 逻辑：图片间隔 3s（1K）/ 7s（2K）/ 60s（3K/4K），视频间隔 65s。

## 示例脚本

| 脚本 | 参数 |
|------|------|
| `examples/basic-chat.py` | `[用户问题]` |
| `examples/text-to-image.py` | `[提示词] [尺寸] [比例]` |
| `examples/text-to-video.py` | `[提示词]` |
| `examples/poll-video.py` | `<video_id> [api_key]` |

## 注意事项

- 视频生成需 2-5 分钟，轮询时进度恒 10%，完成时跳 100%
- 图片生成超时 360s，视频任务查询用 `/agnesapi?video_id=...` 端点
- 当前所有模型免费
