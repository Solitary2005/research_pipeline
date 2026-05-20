#!/usr/bin/env python3
"""Unmark a paper: set interesting=False, remove summary, podcast, and audio files."""

import argparse
import json
import sys

from utils.config import config
from generate_pages import paper_frontmatter, paper_body, generate_index_md


def load_index():
    if not config.index_path.exists():
        print("[unmark] No papers_index.json found.", file=sys.stderr)
        sys.exit(1)
    with open(config.index_path) as f:
        return json.load(f)


def save_index(index):
    config.data_dir.mkdir(parents=True, exist_ok=True)
    with open(config.index_path, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def remove_file(path, label):
    if path.exists():
        path.unlink()
        print(f"[unmark] Removed {label}: {path}")
    else:
        print(f"[unmark] {label} not found (skip): {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arxiv_id", required=True)
    args = parser.parse_args()

    arxiv_id = args.arxiv_id.strip()
    print(f"[unmark] Unmarking paper {arxiv_id}")

    index = load_index()
    if arxiv_id not in index:
        print(f"[unmark] Paper {arxiv_id} not in index.", file=sys.stderr)
        sys.exit(1)

    paper = index[arxiv_id]
    if not paper.get("interesting"):
        print(f"[unmark] Paper {arxiv_id} is already not marked as interesting.")
        return

    paper["interesting"] = False
    paper["has_summary"] = False
    paper["has_podcast"] = False
    save_index(index)
    print(f"[unmark] Updated papers_index.json: flags cleared for {arxiv_id}")

    remove_file(config.summaries_dir / f"{arxiv_id}.json", "summary")
    remove_file(config.podcasts_dir / f"{arxiv_id}.md", "podcast page")
    remove_file(config.audio_dir / f"{arxiv_id}.mp3", "audio")

    md_path = config.papers_dir / f"{arxiv_id}.md"
    if md_path.exists():
        content = f"{paper_frontmatter(paper)}\n\n{paper_body(paper)}"
        with open(md_path, "w") as f:
            f.write(content)
        print(f"[unmark] Updated paper page: {md_path}")
    else:
        print(f"[unmark] Paper page not found: {md_path}")

    generate_index_md(index)

    print(f"[unmark] Done. Paper {arxiv_id} fully removed from favorites.")


if __name__ == "__main__":
    main()
