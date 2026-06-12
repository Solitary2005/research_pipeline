import os
from pathlib import Path

import yaml


class ConfigError(Exception):
    pass


DEFAULT_SETTINGS_YAML = """\
# =============================================================================
# Research Pipeline — Backend Settings
# =============================================================================
# Customize which LLM and TTS backends the pipeline uses.
#
# API keys must ALWAYS be set via environment variables or GitHub Secrets:
#   DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
#
# All settings can be overridden by environment variables:
#   LLM_BACKEND, TTS_BACKEND
# =============================================================================

llm:
  backend: "deepseek"     # claude | openai | deepseek

tts:
  backend: "edge"         # edge | openai
"""


class Config:
    def __init__(self):
        # ---- Paths ----
        self.settings_config_path = Path(
            os.environ.get(
                "SETTINGS_CONFIG_PATH",
                Path(__file__).resolve().parents[2] / "config" / "settings.yaml",
            )
        )

        self.topics_config_path = Path(
            os.environ.get(
                "TOPICS_CONFIG_PATH",
                Path(__file__).resolve().parents[2] / "config" / "topics.yaml",
            )
        )

        # ---- Load backend settings from YAML (auto-create default if missing) ----
        settings = self._load_settings()

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
        # Kept for backward compatibility with any scripts that may still reference it.
        self.repo_a_json_url = os.environ.get(
            "REPO_A_JSON_URL",
            "https://cdn.jsdelivr.net/gh/Solitary2005/Dexterous-grasp-daily@main/Dexterous-grasp-arxiv-daily.json"
        )

        self.repo_name = os.environ.get("GITHUB_REPOSITORY", "Solitary2005/research_pipeline")

        base = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).resolve().parents[2]))
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
        """Load backend settings from YAML. Auto-create default if file missing."""
        if not self.settings_config_path.exists():
            self.settings_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_config_path, "w") as f:
                f.write(DEFAULT_SETTINGS_YAML)
            return yaml.safe_load(DEFAULT_SETTINGS_YAML) or {}

        with open(self.settings_config_path, "r") as f:
            raw = yaml.safe_load(f)
        return raw or {}

    def require_key(self, key_name):
        val = getattr(self, key_name, "")
        if not val:
            raise ConfigError(
                f"{key_name} is not set. Add it to GitHub Secrets and pass it as an env var."
            )
        return val


config = Config()
