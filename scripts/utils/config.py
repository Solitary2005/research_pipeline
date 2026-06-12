import os
from pathlib import Path

import yaml


class ConfigError(Exception):
    pass


DEFAULT_SETTINGS_YAML = """\
# =============================================================================
# Research Pipeline — User Configuration
# =============================================================================
# Edit this file once after forking the repo. All settings are in ONE place.
#
# API keys must ALWAYS be set via environment variables or GitHub Secrets:
#   DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
#
# Settings can also be overridden by environment variables:
#   LLM_BACKEND, TTS_BACKEND
# =============================================================================

# ---- GitHub Pages site settings ----
# Change these to YOUR GitHub username and repo name after forking.
site:
  title: "Research Paper Digest"
  url: "https://YOUR_USERNAME.github.io"
  baseurl: "/YOUR_REPO_NAME"

# ---- LLM backend ----
llm:
  backend: "deepseek"     # claude | openai | deepseek

# ---- TTS backend ----
tts:
  backend: "edge"         # edge | openai
"""

# Boilerplate Jekyll config that is merged with user's site settings.
JEKYLL_BOILERPLATE = """\
markdown: kramdown

collections:
  papers:
    output: true
    permalink: /papers/:name/
  podcasts:
    output: true
    permalink: /podcasts/:name/

defaults:
  - scope:
      path: ""
      type: "papers"
    values:
      layout: "paper"
  - scope:
      path: ""
      type: "podcasts"
    values:
      layout: "podcast"
"""


class Config:
    def __init__(self):
        # ---- Compute repo root (needed early for paths) ----
        base = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).resolve().parents[2]))

        # ---- Config file paths ----
        self.settings_config_path = Path(
            os.environ.get(
                "SETTINGS_CONFIG_PATH",
                base / "config" / "settings.yaml",
            )
        )
        self.topics_config_path = Path(
            os.environ.get(
                "TOPICS_CONFIG_PATH",
                base / "config" / "topics.yaml",
            )
        )
        self.jekyll_config_path = base / "_config.yml"

        # ---- Load settings from YAML (auto-create default if missing) ----
        settings = self._load_settings()

        # Site settings (used to sync _config.yml for GitHub Pages)
        site = settings.get("site", {})
        self.site_title = site.get("title", "Research Paper Digest")
        self.site_url = site.get("url", "https://YOUR_USERNAME.github.io")
        self.site_baseurl = site.get("baseurl", "/YOUR_REPO_NAME")

        # Backend selection: env var > YAML > hardcoded fallback
        self.llm_backend = os.environ.get(
            "LLM_BACKEND",
            settings.get("llm", {}).get("backend", "deepseek"),
        )
        self.tts_backend = os.environ.get(
            "TTS_BACKEND",
            settings.get("tts", {}).get("backend", "edge"),
        )

        # ---- API keys (always from env vars for security) ----
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "")

        # ---- Repo / paths ----
        # DEPRECATED: no longer used by fetch_abstracts.py (now searches arXiv directly).
        self.repo_a_json_url = os.environ.get(
            "REPO_A_JSON_URL",
            "https://cdn.jsdelivr.net/gh/Solitary2005/Dexterous-grasp-daily@main/Dexterous-grasp-arxiv-daily.json"
        )
        self.repo_name = os.environ.get("GITHUB_REPOSITORY", "Solitary2005/research_pipeline")

        self.papers_dir = base / "_papers"
        self.podcasts_dir = base / "_podcasts"
        self.summaries_dir = base / "_data" / "summaries"
        self.audio_dir = base / "assets" / "audio"
        self.data_dir = base / "data"
        self.index_path = self.data_dir / "papers_index.json"
        self.pdf_cache_dir = base / "data" / "pdfs"

        self.podcast_target_words_min = 2250
        self.podcast_target_words_max = 4500

    def _load_settings(self) -> dict:
        """Load settings from YAML. Auto-create default if file missing."""
        if not self.settings_config_path.exists():
            self.settings_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_config_path, "w") as f:
                f.write(DEFAULT_SETTINGS_YAML)
            return yaml.safe_load(DEFAULT_SETTINGS_YAML) or {}

        with open(self.settings_config_path, "r") as f:
            raw = yaml.safe_load(f)
        return raw or {}

    def sync_jekyll_config(self):
        """Write _config.yml from current site settings.

        Call this after editing config/settings.yaml to keep the Jekyll
        config in sync.  Also called automatically by generate_pages.py.
        """
        frontmatter = (
            f"# NOTE: This file is auto-synced from config/settings.yaml.\n"
            f"# Edit config/settings.yaml → the pipeline will update this file automatically.\n"
            f"\n"
            f"title: \"{self.site_title}\"\n"
            f"description: >-\n"
            f"  Daily arXiv paper tracking with AI summaries and podcasts\n"
            f"url: \"{self.site_url}\"\n"
            f"baseurl: \"{self.site_baseurl}\"\n"
        )
        with open(self.jekyll_config_path, "w") as f:
            f.write(frontmatter + JEKYLL_BOILERPLATE)

    def require_key(self, key_name):
        val = getattr(self, key_name, "")
        if not val:
            raise ConfigError(
                f"{key_name} is not set. Add it to GitHub Secrets and pass it as an env var."
            )
        return val


config = Config()
