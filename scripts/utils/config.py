import os
from pathlib import Path


class ConfigError(Exception):
    pass


class Config:
    def __init__(self):
        self.llm_backend = os.environ.get("LLM_BACKEND", "claude")
        self.tts_backend = os.environ.get("TTS_BACKEND", "edge")

        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY", "")

        self.repo_a_json_url = os.environ.get(
            "REPO_A_JSON_URL",
            "https://raw.githubusercontent.com/Solitary2005/Dexterous-grasp-daily/main/Dexterous-grasp-arxiv-daily.json"
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

    def require_key(self, key_name):
        val = getattr(self, key_name, "")
        if not val:
            raise ConfigError(
                f"{key_name} is not set. Add it to GitHub Secrets and pass it as an env var."
            )
        return val


config = Config()
