# Video Composer（视频合成）

> 把分镜图片作为参考，调用 `agnes-video-2.5-flash` 逐场景生成短视频，可选拼接。

## 输入

- 项目名
- 分镜图片路径（自动从 `images/` 读取）

## 输出

- `videos/scene-<id>.mp4` — 每个场景一个视频片段
- `videos/<project>-full.mp4` — 拼接后的完整视频（需要 ffmpeg）

## 视频生成策略

1. 每个场景图片作为 `mode: "reference"` 的输入
2. prompt 用场景 description + 动作提示
3. 时长默认 5s，可配置
4. 提交后轮询 `/agnesapi` 直到 `status=completed`
5. （可选）用 ffmpeg 拼接所有片段

## 调用方式

```python
# 生成所有场景视频
python examples/gen-video.py "项目名"

# 只生成某个场景
python examples/gen-video.py "项目名" --scene 3

# 查询视频状态
python examples/poll-video.py <video_id>

# 拼接所有视频（需要 ffmpeg）
python examples/merge-videos.py "项目名"
```

## 用户确认点

运行结束后，**Agent 必须展示/播放视频并等用户确认**，这是流程最后一步。

- 展示：播放视频或展示文件路径
- 询问：「视频 OK？要调时长/重新生成某段？」
- 用户说"完成"→ 流程结束
- 用户说"第 N 段重来"→ `--scene N` 重新生成
- 用户说"拼接"→ 运行 `merge-videos.py`

```
✅ 视频已生成: 5 个片段
   videos/scene-1.mp4 (5s)
   videos/scene-2.mp4 (5s)
   ...

   总时长: ~25s

下一步：
  [1] 拼接完整视频 → python examples/merge-videos.py "项目名"
  [2] 重新生成某场景 → python gen-video.py "项目名" --scene N
  [3] 调整时长 → 修改剧本 duration_hint 后重新运行
  [4] 完成 🎬
```

## 注意事项

- 视频生成每个片段 2-5 分钟，5 个场景总计 10-25 分钟
- **速率限制：1次/分钟**，脚本自动间隔 65s
- 轮询间隔 30s，不要频繁请求
- 拼接需要系统安装 `ffmpeg`（`apt install ffmpeg`）

## 参数约束（agnes-video-2.5-flash）

| 参数 | 限制 |
|------|------|
| size | 固定 720P |
| 时长 | 4-12s（`--duration` 超出自动裁剪） |
| 图片参考 | 最多 5 张 |
| 音频参考 | 最多 3 段 |
| 视频参考 | 不支持 |

## 示例脚本

| 脚本 | 参数 |
|------|------|
| `examples/gen-video.py` | `[项目名] [--scene N]` |
| `examples/poll-video.py` | `<video_id> [api_key]` |
| `examples/merge-videos.py` | `[项目名]` |
| `examples/load_env.py` | 无 |
