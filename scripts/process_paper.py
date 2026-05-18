#!/usr/bin/env python3
"""Orchestrator: Download PDF → extract text → LLM summary → TTS podcast → create pages."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

from scripts.utils.config import config
from scripts.utils.pdf_extractor import extract_text
from scripts.utils.llm_client import LLMClient
from scripts.utils.tts_client import TTSClient


def load_index():
    if not config.index_path.exists():
        print("[process] No papers_index.json found.", file=sys.stderr)
        sys.exit(1)
    with open(config.index_path) as f:
        return json.load(f)


def save_index(index):
    config.data_dir.mkdir(parents=True, exist_ok=True)
    with open(config.index_path, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def download_pdf(arxiv_id):
    config.pdf_cache_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = config.pdf_cache_dir / f"{arxiv_id}.pdf"

    if pdf_path.exists():
        print(f"[process] PDF already cached: {pdf_path}")
        return str(pdf_path)

    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    print(f"[process] Downloading PDF from {url}")
    headers = {"User-Agent": "ResearchPipeline/1.0 (mailto:research@example.com)"}

    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=120)
            resp.raise_for_status()
            with open(pdf_path, "wb") as f:
                f.write(resp.content)
            print(f"[process] Downloaded PDF: {pdf_path} ({len(resp.content)} bytes)")
            return str(pdf_path)
        except requests.RequestException as e:
            if attempt < 2:
                wait = 2 ** attempt * 5
                print(f"[process] Download failed, retrying in {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"[process] PDF download failed after 3 attempts: {e}", file=sys.stderr)
                sys.exit(1)


def save_summary(arxiv_id, summary, podcast_script=""):
    config.summaries_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "arxiv_id": arxiv_id,
        "summary": summary,
        "podcast_script": podcast_script,
    }
    path = config.summaries_dir / f"{arxiv_id}.json"
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[process] Saved summary to {path}")


def create_podcast_page(paper_info, summary):
    pid = paper_info["arxiv_id"]
    title = paper_info.get("title", "Unknown").replace('"', '\\"')
    authors = ", ".join(paper_info.get("authors", [])[:3])
    if len(paper_info.get("authors", [])) > 3:
        authors += " et al."

    motivation = summary.get("motivation", "")
    method = summary.get("method", "")
    key_results = summary.get("key_results", "")
    takeaways = summary.get("takeaways", "")

    content = f"""---
layout: podcast
arxiv_id: "{pid}"
title: "{title}"
authors: "{authors}"
published_date: {paper_info.get('published_date', '')}
permalink: /podcasts/{pid}/
---

<audio controls style="width:100%;margin-bottom:2em;">
  <source src="/{config.repo_name.split('/')[-1]}/assets/audio/{pid}.mp3" type="audio/mpeg">
  Your browser does not support audio.
</audio>

## Paper

**[{title}]({paper_info.get('abs_url', f'https://arxiv.org/abs/{pid}')})** — {authors}

## Summary Card

### Motivation
{motivation}

### Method
{method}

### Key Results
{key_results}

### Takeaways
{takeaways}

[Back to paper page](/papers/{pid}/)
"""

    config.podcasts_dir.mkdir(parents=True, exist_ok=True)
    path = config.podcasts_dir / f"{pid}.md"
    with open(path, "w") as f:
        f.write(content)
    print(f"[process] Created podcast page: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arxiv_id", required=True)
    parser.add_argument("--llm_backend", default=None)
    parser.add_argument("--tts_backend", default=None)
    args = parser.parse_args()

    arxiv_id = args.arxiv_id.strip()
    llm_backend = args.llm_backend or config.llm_backend
    tts_backend = args.tts_backend or config.tts_backend

    print(f"[process] Processing {arxiv_id} (LLM: {llm_backend}, TTS: {tts_backend})")

    index = load_index()
    if arxiv_id not in index:
        print(f"[process] Paper {arxiv_id} not in index.", file=sys.stderr)
        sys.exit(1)

    paper_info = index[arxiv_id]

    # Step 1: Download PDF and extract text
    pdf_path = download_pdf(arxiv_id)
    print("[process] Extracting text from PDF...")
    paper_text, was_truncated = extract_text(pdf_path)
    print(f"[process] Extracted {len(paper_text)} chars (truncated: {was_truncated})")

    # Step 2: Generate English summary
    print("[process] Generating English summary via LLM...")
    llm = LLMClient(llm_backend, config)
    summary = llm.generate_summary(paper_info, paper_text)
    print(f"[process] Summary keys: {list(summary.keys())}")

    # Step 3: Generate Chinese podcast script
    print("[process] Generating Chinese podcast script via LLM...")
    podcast_script = llm.generate_podcast_script(paper_info, summary, paper_text)
    print(f"[process] Podcast script: {len(podcast_script)} chars")

    # Step 4: Save summary + podcast script
    save_summary(arxiv_id, summary, podcast_script)

    # Step 5: TTS audio generation
    print("[process] Generating audio via TTS...")
    config.audio_dir.mkdir(parents=True, exist_ok=True)
    audio_path = config.audio_dir / f"{arxiv_id}.mp3"
    tts = TTSClient(tts_backend, config)
    duration = tts.generate_audio(podcast_script, str(audio_path))
    duration_min = duration / 60
    print(f"[process] Audio saved: {audio_path} ({duration_min:.1f} min)")

    # Step 6: Create podcast page
    create_podcast_page(paper_info, summary)

    # Step 7: Update index
    paper_info["has_summary"] = True
    paper_info["has_podcast"] = True
    paper_info["interesting"] = True
    save_index(index)

    print(f"[process] Done processing {arxiv_id}.")


if __name__ == "__main__":
    main()
