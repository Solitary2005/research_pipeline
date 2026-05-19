# Research Pipeline — Paper Digest + AI Podcast

Daily paper tracking for dexterous grasping research, with AI-generated summaries and Chinese podcasts.

## How It Works

1. **Daily** — GitHub Actions pulls new papers from [Dexterous-grasp-daily](https://github.com/Solitary2005/Dexterous-grasp-daily), fetches abstracts from arXiv, and generates a GitHub Pages site.
2. **Browse** — Read abstracts on the site at `https://solitary2005.github.io/research_pipeline/`
3. **Request** — Click "Request Summary + Podcast" on any paper to open a GitHub Issue.
4. **Generate** — The workflow downloads the PDF, calls an LLM for an English summary card + Chinese podcast script, and runs TTS for 15-30 min audio.
5. **Listen** — Audio appears on the paper's podcast page.
6. **Cleanup** — Papers you didn't request a summary for are auto-deleted after 7 days.

## Setup

### 1. GitHub Secrets (Settings > Secrets and variables > Actions)

| Secret | Required | Purpose |
|--------|----------|---------|
| `ANTHROPIC_API_KEY` | Yes (default LLM) | Claude API for summaries and podcast scripts |
| `OPENAI_API_KEY` | Optional | OpenAI GPT for summaries / TTS for audio |
| `DEEPSEEK_API_KEY` | Optional | DeepSeek as alternative LLM backend |

### 2. GitHub Pages

Enable Pages in repo Settings > Pages:
- Source: Deploy from a branch
- Branch: `main`, folder: `/ (root)`

### 3. Configure (optional)

Set environment variables in workflow files to change backends:
- `LLM_BACKEND=claude|openai|deepseek` (default: `claude`)
- `TTS_BACKEND=edge|openai` (default: `edge`)

## Project Structure

```
├── .github/workflows/
│   ├── daily-update.yml        # Daily: fetch abstracts, generate pages
│   ├── process-summary.yml     # Issue-triggered: summary + podcast generation
│   └── cleanup.yml             # Daily: remove uninteresting papers > 7 days
├── scripts/
│   ├── fetch_abstracts.py      # Download Repo A JSON, fetch arxiv abstracts
│   ├── generate_pages.py       # Build Jekyll paper pages and index
│   ├── process_paper.py        # PDF→text→LLM summary→TTS podcast pipeline
│   ├── cleanup.py              # 7-day auto-purge
│   └── utils/                  # Shared modules (arxiv, LLM, TTS, PDF, config)
├── _papers/                    # Jekyll collection: individual paper pages
├── _podcasts/                  # Jekyll collection: summary card + audio player
├── _data/summaries/            # LLM output JSON
├── assets/audio/               # Generated MP3 files
└── _layouts/                   # Jekyll templates
```

## Manual Test

```bash
# Test arxiv API
python -c "from scripts.utils.arxiv_api import fetch_abstract; print(fetch_abstract('2605.15157')['title'])"

# Generate mock pages
python scripts/generate_pages.py

# Process a paper (needs API keys)
python scripts/process_paper.py --arxiv_id 2605.15157
```

## User Guide

### 📍 1. 它们存放的具体位置？

生成的播客和总结卡片会在 GitHub Action 流程运行结束后自动保存在项目仓库中，您也可以直接在 GitHub Pages 网页上看到。具体存储路径如下：

- **总结卡片原始数据 (JSON)**: `_data/summaries/` 文件夹下。
- **播客展示页面 (Markdown)**: `_podcasts/` 文件夹下。
- **播客音频文件 (MP3)**: `assets/audio/` 文件夹下。
- **网页前端查看**: 基于 GitHub Pages 自动渲染好的博客网站（项目默认路由应在您的博客站点的 Podcast 或对应 Paper 详情页中）。

### 📖 2. 完整用户使用手册：从配置到收听体验

以下是使用本系统跑通整个“论文获取 -> 生成总结 -> 播客生成”流程的步骤。

#### 第一步：配置 API 与基础环境变量
系统运行需要依赖大语言模型 (LLM) 和文本转语音 (TTS) 接口。

1. 进入该项目的 GitHub 仓库页面。
2. 点击 **Settings (设置)** -> **Secrets and variables** -> **Actions**。
3. 点击 **New repository secret**，添加您需要使用的 API Key：
   - `ANTHROPIC_API_KEY`：如果使用 Claude（推荐用于生成高质量总结脚本）。
   - `OPENAI_API_KEY`：如果使用 GPT（用于总结）或 OpenAI 的高质量 TTS。
   - `DEEPSEEK_API_KEY`：如果使用 DeepSeek 进行大模型推理。
4. *(可选进阶)*：打开 `.github/workflows/process-summary.yml`，您可以配置使用的具体模型：
   - `LLM_BACKEND`: 可选 `claude`、`openai` 或 `deepseek`。
   - `TTS_BACKEND`: 可选免费标准的 `edge` 或高质量的 `openai`。

#### 第二步：配置 GitHub Pages 网站
为了获得最好的阅读和收听体验，请开启网页可视化：

1. 在 GitHub 仓库页，进入 **Settings** -> 左侧菜单找 **Pages**。
2. 在 **Build and deployment** 部分：
   - Source (源) 选择: `Deploy from a branch`。
   - Branch (分支) 选择: `main` 分支 -> 文件夹选 `/ (root)`。
3. 保存后 GitHub 将为您的项目生成一个专属网址（例如 `https://您的用户名.github.io/research_pipeline/`）。

#### 第三步：日常浏览与请求总结播客
这套系统每天会自动通过 GitHub Actions 抓取指定领域的最新论文，生成基础摘要页。

1. **浏览最新论文**：打开上面生成的 GitHub Pages 网站，浏览每日更新的论文摘要列表。
2. **请求播客和总结**：如果您觉得某篇论文很有价值，点击网页上该论文底部的 **"Request Summary + Podcast"** 按钮。
3. **触发后台运行**：该操作会自动在您的 GitHub 仓库中打开一个新的 Issue（按模板填写）。当提交此 Issue 后，GitHub Actions 中的 `process-summary.yml` 工作流就会被触发。

#### 第四步：收听播客与查看总结卡片
机器人在后台接收指令后，会自动下载 PDF、使用 LLM 生成英文总结和中文播客台本、最后转换为音频资源，大概需要等待几分钟。

1. **收到更新通知**：工作流执行完毕后，爬取的总结文件以及生成的 MP3 播客会被自动拉取提交 (Commit) 到 `main` 分支。
2. **查看总结卡片**：直接在您的 GitHub Pages 网站中访问这篇论文页面，此时页面上已经挂载了详细的“英文重点总结”板块。
3. **收听播客**：就在当前网页中，会出现一个内置的网页音频播放器。点击播放，您就可以直接收听基于该篇论文内容生成的 15~30 分钟中文深度讨论音频了！

> 💡 **注**：系统默认保留最近 7 天的论文流。如果不手动“请求播客”，单纯的日常摘要展示存留时间到期后将被自动清理脚本 `cleanup.yml` 清除，而保存过精华总结和音频的论文页面则会永久保留。