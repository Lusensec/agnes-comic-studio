# Agnes Comic Studio 🎬

基于 **Agnes AI Flash** 系列的漫剧 / 短视频创作 Skill 套件。

一个故事概念 → 剧本 → 角色三视图/背景/道具/分镜图 → 短视频，全自动化流水线。每个步骤可暂停确认、修改、重试。

## 特性

- 📝 **AI 剧本生成** — 输入故事概念，自动输出结构化剧本（角色 + 场景 + 台词 + 道具）
- 🎨 **完整视觉资产** — 角色三视图、多表情、纯背景、道具参考、分镜图
- 🎬 **短视频合成** — 图片/文生视频，自动速率控制
- 📦 **资产追踪** — SQLite 数据库统一管理所有产出，支持搜索/复用
- 🔀 **模块化** — 每个步骤独立子 Skill，可单独调用
- ⚡ **速率限制防范** — 自动 sleep，不会触发 429

## 前置条件

| 依赖 | 说明 |
|------|------|
| Python 3.9+ | 仅用标准库，无第三方包 |
| Agnes AI API Key | 免费注册 [platform.agnes-ai.cn](https://platform.agnes-ai.cn) |
| ffmpeg（可选） | 仅视频拼接需要：`apt install ffmpeg` |

## 快速开始

### 1. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env，填入你的 AGNESAI_API_KEY
```

### 2. 初始化项目

```bash
python asset-manager/examples/init-project.py "我的漫剧"
```

创建文件夹结构 + SQLite 数据库：

```
~/comic-studio/projects/我的漫剧/
├── scripts/
├── images/
├── videos/
├── references/
└── assets.db
```

### 3. 生成剧本（Step 1）

```bash
python script-writer/examples/write-script.py "我的漫剧" "故事概念" [风格] [方向] [时长] [尺寸]
```

参数说明：
| 参数 | 选项 | 默认 |
|------|------|------|
| 风格 | 动画/写实/水墨/赛博朋克/二次元 | 动画 |
| 方向 | landscape(16:9)/portrait(9:16) | landscape |
| 时长 | 4-12（秒） | 5 |
| 尺寸 | 1K/2K | 1K |

示例：
```bash
python script-writer/examples/write-script.py "我的漫剧" "宇航员在太空遇见一条鱼" 动画 portrait 8 2K
```

输出：`scripts/我的漫剧-script.json`（角色 + 场景 + 道具 + config）

### 4. 生成视觉资产（Step 2）

```bash
# 角色三视图
python storyboard-gen/examples/gen-character.py "我的漫剧" "角色名" three-view

# 角色多表情
python storyboard-gen/examples/gen-character.py "我的漫剧" "角色名" expression

# 纯背景图（无角色）
python storyboard-gen/examples/gen-background.py "我的漫剧" [场景ID]

# 道具参考图
python storyboard-gen/examples/gen-props.py "我的漫剧" [道具名]

# 全套分镜（角色参考 + 逐场景图）
python storyboard-gen/examples/gen-storyboard.py "我的漫剧"
```

输出：`images/` 目录下的 PNG 文件

### 5. 生成视频（Step 3，可选）

```bash
# 生成所有场景视频
python video-composer/examples/gen-video.py "我的漫剧"

# 只生成某个场景
python video-composer/examples/gen-video.py "我的漫剧" --scene 3

# 指定时长
python video-composer/examples/gen-video.py "我的漫剧" --duration 8

# 拼接完整视频（需要 ffmpeg）
python video-composer/examples/merge-videos.py "我的漫剧"
```

输出：`videos/scene-N.mp4` + `videos/我的漫剧-full.mp4`

### 6. 查看/管理资产

```bash
# 列出所有资产
python asset-manager/examples/list-assets.py "我的漫剧"

# 按类型过滤
python asset-manager/examples/list-assets.py "我的漫剧" image

# 搜索
python asset-manager/examples/find-asset.py "我的漫剧" "花"

# 手动记录新资产
python asset-manager/examples/track-asset.py "我的漫剧" reference "path/to/file.png" "描述" "tag1,tag2"
```

## 完整工作流示例

```
用户："帮我做一个关于外卖小哥在暴雨夜送最后一单的漫剧"
    ↓
Agent 询问配置：
  "横屏/竖屏？时长？风格？尺寸？"
用户："竖屏，5秒，动画，1K"
    ↓
Step 1: write-script.py "暴雨外卖" "概念" 动画 portrait 5 1K
  → 生成剧本 JSON（2角色 + 6场景 + 3道具）
  → Agent 展示剧本，问用户："OK？要改哪部分？"
用户："继续"
    ↓
Step 2a: gen-character.py "暴雨外卖" "阿杰" three-view
Step 2b: gen-background.py "暴雨外卖"
Step 2c: gen-props.py "暴雨外卖"
Step 2d: gen-storyboard.py "暴雨外卖"
  → 生成全套图片
  → Agent 展示图片，问用户："满意吗？要重来哪张？"
用户："继续"
    ↓
Step 3: gen-video.py "暴雨外卖"
  → 逐段生成视频（65s 间隔）
  → Agent 播放视频，问用户："OK？要调时长？"
用户："拼接"
    ↓
merge-videos.py "暴雨外卖"
  → 输出完整视频
```

## 项目文件结构

```
agnes-comic-studio/
│
├── SKILL.md                          # 主入口（RikkaHub Skill 格式）
├── README.md                         # 本文件
├── .env.example                      # API Key 模板
├── .gitignore
│
├── agnes-flash-suite/                # 子 Skill: 基础 API 调用
│   ├── SKILL.md
│   └── examples/
│       ├── load_env.py               # .env 加载（所有子 Skill 共用）
│       ├── basic-chat.py             # 对话
│       ├── text-to-image.py          # 文生图
│       ├── text-to-video.py          # 文生视频
│       └── poll-video.py             # 视频任务轮询
│
├── script-writer/                    # 子 Skill: Step 1 剧本生成
│   ├── SKILL.md
│   └── examples/
│       ├── load_env.py
│       ├── track.py                  # 资产记录（共用模块）
│       ├── write-script.py           # 生成完整剧本 JSON
│       └── refine-script.py          # 修改单个角色描述
│
├── storyboard-gen/                   # 子 Skill: Step 2 视觉资产
│   ├── SKILL.md
│   └── examples/
│       ├── load_env.py
│       ├── track.py
│       ├── gen-storyboard.py         # 全套分镜（角色+场景）
│       ├── gen-character.py          # 角色图（sheet/three-view/expression）
│       ├── gen-background.py         # 纯背景（无角色）
│       └── gen-props.py             # 道具/物品参考
│
├── video-composer/                   # 子 Skill: Step 3 视频合成
│   ├── SKILL.md
│   └── examples/
│       ├── load_env.py
│       ├── track.py
│       ├── gen-video.py              # 逐场景生成视频
│       ├── poll-video.py             # 查询单个视频任务
│       └── merge-videos.py           # ffmpeg 拼接
│
└── asset-manager/                    # 子 Skill: 资产管理
    ├── SKILL.md
    └── examples/
        ├── load_env.py
        ├── track.py                  # ensure_project_db + track_file
        ├── init-project.py           # 初始化项目文件夹 + DB
        ├── track-asset.py            # 记录新资产
        ├── list-assets.py            # 列出资产
        └── find-asset.py            # 搜索资产
```

## 资产数据库（assets.db）

每个项目一个 SQLite 文件，表结构：

```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    asset_type TEXT NOT NULL,  -- script | image | image_three-view | image_expression
                                -- | image_background | image_prop | video | reference
    filename TEXT NOT NULL,
    filepath TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    tags TEXT
);
```

每次生成文件时自动记录，支持 `find-asset.py` 按关键词/标签搜索。

## 速率限制

| 模型 | 限制 | 脚本自动间隔 |
|------|------|-------------|
| `agnes-image-2.5-flash` 1K | 20次/分 | 3s |
| `agnes-image-2.5-flash` 2K | 10次/分 | 7s |
| `agnes-image-2.5-flash` 3K/4K | 1次/分 | 60s |
| `agnes-video-2.5-flash` | **1次/分** | 65s |

视频模型约束：size 固定 720P，时长 4-12s，图片参考最多 5 张，不支持视频参考。

## 作为 RikkaHub Skill 安装

```
skill_install_from_url https://raw.githubusercontent.com/Lusensec/agnes-comic-studio/master/SKILL.md
```

安装后对 AI 说：
- "帮我写一个关于 XX 的漫剧剧本"
- "生成这个项目的角色三视图和背景"
- "把分镜做成视频"

## 许可

MIT
