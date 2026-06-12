# Research Pipeline — Paper Digest + AI Podcast

Track arXiv papers by your own keywords, with AI-generated summaries and Chinese podcasts.

## User Guide

### 0. First-Time Setup — Edit ONE File

After forking the repo, open **`config/settings.yaml`** and set your GitHub Pages URL and preferred backends:

```yaml
# config/settings.yaml — ALL user settings in one place
site:
  title: "My Research Digest"                         # your site title
  url: "https://YOUR_USERNAME.github.io"              # your GitHub Pages URL
  baseurl: "/YOUR_REPO_NAME"                          # your repo name

llm:
  backend: "deepseek"     # claude | openai | deepseek

tts:
  backend: "edge"         # edge | openai
```

The pipeline auto-syncs `_config.yml` from this file — you never need to edit `_config.yml` directly.

Then edit **`config/topics.yaml`** to customize which papers are tracked:

```yaml
topics:
  - name: "dexterous_grasp"
    display_name: "Dexterous Grasp"
    search_query: "grasp"
    max_results: 20
    abstract_contains:
      - "grasp"
    any_keyword:
      - "dexterous"
      - "dex"

  - name: "robot_learning"
    display_name: "Robot Learning"
    search_query: "cat:cs.RO robot learning"
    max_results: 15
    abstract_contains: []
    any_keyword:
      - "reinforcement learning"
      - "imitation learning"
      - "policy"
```

**Topic configuration fields:**
| Field | Description |
|-------|-------------|
| `name` | Internal identifier (snake_case) |
| `display_name` | Human-readable label shown on the website |
| `search_query` | arXiv API query (supports boolean ops, category filters like `cat:cs.RO`) |
| `max_results` | Papers to fetch per run (1–100, default 20) |
| `abstract_contains` | ALL keywords must appear in abstract (case-insensitive). Empty = disabled. |
| `any_keyword` | AT LEAST ONE keyword must appear in abstract (case-insensitive). Empty = disabled. |

### 1. Browse Papers

Visit the [GitHub Pages site](https://solitary2005.github.io/research_pipeline/) to browse daily arXiv papers. The system searches arXiv directly and updates each day at 12:00 UTC.

### 2. Request Summary + Podcast (arXiv papers)

On any paper's detail page, click **"Request Summary + Podcast"**. This opens a GitHub Issue — submit it and the workflow will:
- Download the PDF from arXiv
- Generate an English summary card
- Generate a Chinese podcast script (~15-30 min)
- Produce an MP3 audio file
- Add the paper to your Favorites

The result appears on the paper's podcast page within a few minutes.

### 3. Manually Upload a Paper

Have your own PDF? Use the **Manual Upload** feature:

1. Go to Issues → New Issue → **"Manual Paper Upload"**
2. Fill in the paper title, authors, and topic
3. **Drag and drop your PDF** into the form (or place it in `_uploads/` and reference its filename)
4. Submit the issue

The workflow automatically generates the summary card, podcast, and adds the paper to your Favorites — no separate "Request" step needed.

### 4. Listen to Podcasts

Each processed paper gets a dedicated podcast page with an embedded audio player. You can also browse all archived papers on the [Favorites page](https://solitary2005.github.io/research_pipeline/favorites/).

### 5. Remove from Favorites

On any favorited paper's page, click **"Remove from Favorites"**. This opens an issue — submit it to remove the paper from your collection (summary, podcast, and audio files will be cleaned up).

### 6. Cleanup

Papers that haven't been requested for summary/podcast are automatically removed after 7 days. Favorited papers are kept permanently.

---

<details>
<summary>📋 Setup & Configuration</summary>

### GitHub Secrets

| Secret | Required | Purpose |
|--------|----------|---------|
| `ANTHROPIC_API_KEY` | Optional | Claude API for summaries and podcasts |
| `OPENAI_API_KEY` | Optional | OpenAI GPT / TTS |
| `DEEPSEEK_API_KEY` | Yes (default) | DeepSeek as LLM backend |

### GitHub Pages

Enable Pages in repo Settings → Pages:
- Source: Deploy from a branch
- Branch: `main`, folder: `/ (root)`

### All User Configuration

Everything you need to customize is in two files under `config/`:

| File | What it controls |
|------|-----------------|
| `config/settings.yaml` | Site URL, title, LLM backend, TTS backend |
| `config/topics.yaml` | arXiv search queries, keywords, filters |

See [Section 0](#0-first-time-setup--edit-one-file) above for the full format. You can override either file's path via environment variables:
- `SETTINGS_CONFIG_PATH` — path to `settings.yaml`
- `TOPICS_CONFIG_PATH` — path to `topics.yaml`

Backend settings can also be overridden by environment variables (`LLM_BACKEND`, `TTS_BACKEND`) — useful for CI without editing files.

</details>

---

<details>
<summary>📝 Changelog</summary>

Full release notes are published on the [GitHub Releases](https://github.com/Solitary2005/research_pipeline/releases) page.

**Latest — Manual Paper Upload (2026-06-11)**
- New Issue template for manual PDF uploads (drag & drop)
- Uploaded papers go directly to Favorites + auto-generate summary card & podcast
- Supports non-arXiv papers with user-provided metadata
- Unmark workflow updated to support both arXiv IDs and manual paper IDs

[View all releases →](https://github.com/Solitary2005/research_pipeline/releases)

</details>
