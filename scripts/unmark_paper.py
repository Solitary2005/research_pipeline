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

    paper_id = args.arxiv_id.strip()
    print(f"[unmark] Unmarking paper {paper_id}")

    index = load_index()
    if paper_id not in index:
        print(f"[unmark] Paper '{paper_id}' not found in index.", file=sys.stderr)
        # Show available IDs that look similar
        import difflib
        candidates = difflib.get_close_matches(paper_id, list(index.keys()), n=5, cutoff=0.4)
        if candidates:
            print(f"[unmark] Did you mean one of these?", file=sys.stderr)
            for c in candidates:
                print(f"[unmark]   - {c}", file=sys.stderr)
        else:
            print(f"[unmark] Available paper IDs ({len(index)} total):", file=sys.stderr)
            for pid in sorted(index.keys())[:10]:
                print(f"[unmark]   - {pid}", file=sys.stderr)
            if len(index) > 10:
                print(f"[unmark]   ... and {len(index) - 10} more", file=sys.stderr)
        sys.exit(1)

    paper = index[paper_id]
    if not paper.get("interesting"):
        print(f"[unmark] Paper {paper_id} is already not marked as interesting.")
        return

    paper["interesting"] = False
    paper["has_summary"] = False
    paper["has_podcast"] = False
    save_index(index)
    print(f"[unmark] Updated papers_index.json: flags cleared for {paper_id}")

    # Clean up generated artifacts
    remove_file(config.summaries_dir / f"{paper_id}.json", "summary")
    remove_file(config.podcasts_dir / f"{paper_id}.md", "podcast page")
    remove_file(config.audio_dir / f"{paper_id}.mp3", "audio")

    # Clean up cached PDF (arXiv downloads) or manually-uploaded PDF
    remove_file(config.pdf_cache_dir / f"{paper_id}.pdf", "cached PDF")

    # Clean up uploaded PDF in _uploads/ — try the conventional name, then scan
    uploads_dir = config.papers_dir.parent / "_uploads"
    conventional = uploads_dir / f"{paper_id}.pdf"
    if conventional.exists():
        remove_file(conventional, "uploaded PDF")
    elif uploads_dir.exists():
        # Scan for any PDF whose name suggests it belongs to this paper
        for f in uploads_dir.glob("*.pdf"):
            if paper_id[:20] in f.name or f.stem in paper_id:
                remove_file(f, "uploaded PDF (matched)")

    md_path = config.papers_dir / f"{paper_id}.md"
    if md_path.exists():
        content = f"{paper_frontmatter(paper)}\n\n{paper_body(paper)}"
        with open(md_path, "w") as f:
            f.write(content)
        print(f"[unmark] Updated paper page: {md_path}")
    else:
        print(f"[unmark] Paper page not found: {md_path}")

    generate_index_md(index)

    print(f"[unmark] Done. Paper {paper_id} fully removed from favorites.")


if __name__ == "__main__":
    main()
