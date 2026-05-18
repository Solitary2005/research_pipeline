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
