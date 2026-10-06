---
name: post-production
description: |
  后期制作子 Skill。TTS 配音、字幕生成（多句分窗）、BGM 叠加、最终视频合成（ffmpeg 场景对齐混音，Windows 路径安全）。
  触发场景：配音、字幕、BGM、最终合成。

# Post Production（后期制作）

> TTS 配音、字幕生成、BGM 叠加、最终视频合成。

## 功能

| 脚本 | 功能 | 输出 |
|------|------|------|
| `examples/gen-tts.py` | 角色对白 TTS 配音 | `videos/audio/line-<scene>-<n>.mp3` |
| `examples/gen-subtitles.py` | 从剧本生成 SRT 字幕 | `videos/subtitles.srt` |
| `examples/add-bgm.py` | 叠加 BGM（降低音量） | `videos/<project>-with-bg.mp4` |
| `examples/final-compose.py` | 视频 + 配音 + BGM + 字幕 合成 | `videos/<project>-final.mp4` |

## TTS 配置

支持两种 TTS 后端（通过 `.env` 切换）：

```
# 方案 A: Agnes AI（需 API Key）
TTS_PROVIDER=agnes

# 方案 B: 本地 edge-tts（免费，需 pip install edge-tts）
TTS_PROVIDER=edge
```

角色音色分配（自动）：
- 主角 → 男声 / 女声（根据性别描述）
- 配角 → 不同音色
- 旁白 → 中性

## 字幕

自动生成 SRT 文件，时间轴基于 `duration_hint` 均匀分配。支持：
- 对话字幕（底部）
- 场景描述字幕（可选）
- 多语言（从剧本 `description_zh` 读取）

## BGM

`examples/add-bgm.py` 需要 BGM 文件路径。支持：
- 从 `references/` 目录读取用户上传的 BGM
- 默认无 BGM（纯配音）

## 最终合成

`final-compose.py` 用 ffmpeg 一步完成：
```
视频片段 → 加配音 → 加 BGM → 烧录字幕 → 输出 MP4
```

依赖：`ffmpeg` + `ffprobe`

## 用户确认点

运行 `final-compose.py` 后，**Agent 必须播放最终视频并等用户确认**。

- 展示：播放最终视频
- 询问：「最终版 OK？要调整字幕位置/BGM 音量/重新配音？」
- 用户说"完成"→ 流程结束
