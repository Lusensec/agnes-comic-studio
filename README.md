# Agnes Comic Studio 🎬

基于 **Agnes AI Flash** 系列的漫剧 / 短视频创作套件。

一个故事概念 → 剧本 → 分镜图 → 短视频，全自动化流水线。每个步骤可暂停、修改、重试。

## 特性

- 📝 **AI 剧本生成** — 输入故事概念，自动输出结构化剧本（角色 + 场景 + 台词）
- 🎨 **分镜图生成** — 逐镜头调用 Agnes 图像模型，角色一致性保证
- 🎬 **短视频合成** — 图片 → 动态视频，可选 ffmpeg 拼接
- 📦 **资产追踪** — SQLite 数据库统一管理所有产出文件
- 🔀 **模块化** — 每个步骤独立子 Skill，可单独调用

## 快速开始

```bash
# 1. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 AGNESAI_API_KEY

# 2. 初始化项目
python asset-manager/examples/init-project.py "我的漫剧"

# 3. 写剧本
python script-writer/examples/write-script.py "我的漫剧" "一个宇航员在太空遇见一条会说话的鱼"

# 4. 生成分镜图
python storyboard-gen/examples/gen-storyboard.py "我的漫剧"

# 5. 生成视频（可选）
python video-composer/examples/gen-video.py "我的漫剧"

# 6. 拼接完整视频（需要 ffmpeg）
python video-composer/examples/merge-videos.py "我的漫剧"
```

## 目录结构

```
agnes-comic-studio/
├── SKILL.md                    # 主文档（RikkaHub Skill 入口）
├── README.md                   # 本文件
├── .env.example                # API Key 模板
├── agnes-flash-suite/          # 基础 API 调用
│   ├── SKILL.md
│   └── examples/
├── script-writer/              # Step 1: 剧本生成
│   ├── SKILL.md
│   └── examples/
├── storyboard-gen/             # Step 2: 分镜图生成
│   ├── SKILL.md
│   └── examples/
├── video-composer/             # Step 3: 视频合成
│   ├── SKILL.md
│   └── examples/
└── asset-manager/              # 资产管理
    ├── SKILL.md
    └── examples/
```

## 依赖

- Python 3.9+（标准库即可，无第三方包）
- ffmpeg（仅视频拼接需要）
- Agnes AI API Key（[免费注册](https://platform.agnes-ai.cn)）

## 作为 RikkaHub Skill 使用

```bash
# 从 URL 安装
skill_install_from_url https://raw.githubusercontent.com/YOUR_NAME/agnes-comic-studio/main/SKILL.md
```

然后对 AI 说：
- "帮我写一个关于 XX 的漫剧剧本"
- "生成这个项目的分镜图"
- "把分镜做成视频"

## 许可

MIT
