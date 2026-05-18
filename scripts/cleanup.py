#!/usr/bin/env python3
"""Delete non-archived papers older than 7 days."""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.utils.config import config


CUTOFF_DAYS = 7


def load_index():
    if not config.index_path.exists():
        print("[cleanup] No papers_index.json found.", file=sys.stderr)
        return {}
    with open(config.index_path) as f:
        return json.load(f)


def save_index(index):
    config.data_dir.mkdir(parents=True, exist_ok=True)
    with open(config.index_path, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def safe_remove(path):
    if path.exists():
        os.remove(path)
        return True
    return False


def main():
    index = load_index()
    if not index:
        print("[cleanup] Nothing to clean up.")
        return

    today = datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=CUTOFF_DAYS)

    to_delete = []
    for paper_id, paper in index.items():
        if paper.get("interesting") or paper.get("has_summary") or paper.get("has_podcast"):
            continue

        pub_date_str = paper.get("published_date", "")
        if not pub_date_str:
            continue

        try:
            pub_date = datetime.strptime(pub_date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            continue

        if pub_date < cutoff:
            to_delete.append((paper_id, pub_date))

    if not to_delete:
        print("[cleanup] No stale papers to remove.")
        return

    for paper_id, pub_date in to_delete:
        age = (today - pub_date).days
        print(f"[cleanup] Removing {paper_id} (published {pub_date}, {age} days ago)")

        safe_remove(config.papers_dir / f"{paper_id}.md")
        safe_remove(config.podcasts_dir / f"{paper_id}.md")
        safe_remove(config.audio_dir / f"{paper_id}.mp3")
        safe_remove(config.summaries_dir / f"{paper_id}.json")

        pdf_path = config.pdf_cache_dir / f"{paper_id}.pdf"
        safe_remove(pdf_path)

        del index[paper_id]

    save_index(index)
    kept = len(index)
    removed = len(to_delete)
    print(f"[cleanup] Removed {removed} stale papers, {kept} remaining.")


if __name__ == "__main__":
    main()
