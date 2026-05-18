#!/usr/bin/env python3
"""Download Repo A JSON, fetch arxiv abstracts for new papers, update papers_index.json."""

import json
import sys
import time
from pathlib import Path

import requests

from utils.arxiv_api import fetch_abstract, ArxivFetchError
from utils.config import config


def load_repo_a_papers():
    print(f"[fetch] Downloading papers from {config.repo_a_json_url}")
    resp = requests.get(config.repo_a_json_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    papers = {}
    for topic, entries in data.items():
        for paper_id, row in entries.items():
            clean_id = paper_id.split("v")[0].strip()
            papers[clean_id] = {
                "topic": topic,
                "raw_row": row,
            }
    print(f"[fetch] Found {len(papers)} papers in Repo A")
    return papers


def load_index():
    if config.index_path.exists():
        with open(config.index_path) as f:
            return json.load(f)
    return {}


def save_index(index):
    config.data_dir.mkdir(parents=True, exist_ok=True)
    with open(config.index_path, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def parse_markdown_row(row):
    parts = row.split("|")
    if len(parts) >= 5:
        date = parts[1].strip().strip("*")
        title = parts[2].strip().strip("*")
        authors = parts[3].strip()
        return {"date": date, "title": title, "authors": authors}
    return {}


def main():
    repo_papers = load_repo_a_papers()
    index = load_index()

    new_count = 0
    for paper_id, repo_info in repo_papers.items():
        if paper_id in index and index[paper_id].get("abstract"):
            continue

        print(f"[fetch] New paper: {paper_id} — {repo_info.get('topic', '')}")

        parsed = parse_markdown_row(repo_info.get("raw_row", ""))

        try:
            arxiv_data = fetch_abstract(paper_id)
            time.sleep(3)  # respect arxiv rate limit
        except ArxivFetchError as e:
            print(f"[fetch] WARNING: {e}", file=sys.stderr)
            arxiv_data = {
                "arxiv_id": paper_id,
                "title": parsed.get("title", "Unknown"),
                "abstract": "[Abstract not available]",
                "published_date": parsed.get("date", ""),
                "authors": [parsed.get("authors", "Unknown")],
                "first_author": parsed.get("authors", "Unknown"),
                "pdf_url": f"https://arxiv.org/pdf/{paper_id}.pdf",
                "abs_url": f"https://arxiv.org/abs/{paper_id}",
            }

        entry = {
            "arxiv_id": paper_id,
            "title": arxiv_data.get("title") or parsed.get("title", "Unknown"),
            "abstract": arxiv_data.get("abstract", ""),
            "published_date": arxiv_data.get("published_date") or parsed.get("date", ""),
            "authors": arxiv_data.get("authors", [parsed.get("authors", "Unknown")]),
            "first_author": arxiv_data.get("first_author") or parsed.get("authors", "Unknown"),
            "primary_category": arxiv_data.get("primary_category", ""),
            "pdf_url": arxiv_data.get("pdf_url", f"https://arxiv.org/pdf/{paper_id}.pdf"),
            "abs_url": arxiv_data.get("abs_url", f"https://arxiv.org/abs/{paper_id}"),
            "topic": repo_info.get("topic", ""),
            "interesting": index.get(paper_id, {}).get("interesting", False),
            "has_summary": index.get(paper_id, {}).get("has_summary", False),
            "has_podcast": index.get(paper_id, {}).get("has_podcast", False),
        }

        index[paper_id] = entry
        new_count += 1

    save_index(index)
    print(f"[fetch] Added {new_count} new papers. Index has {len(index)} total.")

    new_ids = [pid for pid in repo_papers if pid not in load_index() or not load_index().get(pid, {}).get("abstract")]
    new_ids_path = config.data_dir / "new_papers.txt"
    with open(new_ids_path, "w") as f:
        for pid in new_ids:
            if pid in index and index[pid].get("abstract"):
                f.write(f"{pid}\n")


if __name__ == "__main__":
    main()
