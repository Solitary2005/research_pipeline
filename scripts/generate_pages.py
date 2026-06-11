#!/usr/bin/env python3
"""Generate Jekyll paper pages and index.md from papers_index.json."""

import json
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

from utils.config import config


def load_index():
    if not config.index_path.exists():
        print("[generate] No papers_index.json found.", file=sys.stderr)
        return {}
    with open(config.index_path) as f:
        return json.load(f)


def paper_frontmatter(paper):
    authors_str = ", ".join(paper.get("authors", [])[:5])
    if len(paper.get("authors", [])) > 5:
        authors_str += " et al."

    fm = f"""---
arxiv_id: "{paper['arxiv_id']}"
title: "{_escape(paper.get('title', 'Unknown'))}"
authors: "{_escape(authors_str)}"
published_date: {paper.get('published_date', '')}
primary_category: "{paper.get('primary_category', '')}"
topic: "{paper.get('topic', '')}"
has_summary: {str(paper.get('has_summary', False)).lower()}
has_podcast: {str(paper.get('has_podcast', False)).lower()}
interesting: {str(paper.get('interesting', False)).lower()}
permalink: /papers/{paper['arxiv_id']}/
---"""

    return fm


def paper_body(paper):
    abstract = paper.get("abstract", "").replace("\n", "\n\n")
    pid = paper["arxiv_id"]
    title_enc = quote(paper.get("title", ""), safe="")

    # Build links section
    links = []
    abs_url = paper.get('abs_url', '')
    pdf_url = paper.get('pdf_url', '')
    if abs_url:
        links.append(f"- [arXiv]({abs_url})")
    if pdf_url:
        links.append(f"- [PDF]({pdf_url})")
    if not links:
        links.append("- *Manually uploaded paper*")

    body = f"""## Abstract

{abstract}

## Links

{chr(10).join(links)}

## Actions

<a class="btn-request" href="https://github.com/{config.repo_name}/issues/new?template=summary-request.yml&title=[Summary]+{pid}&arxiv_id={pid}&paper_title={title_enc}" target="_blank">Request Summary + Podcast</a>
"""

    if paper.get("has_podcast"):
        body += f"""
---

<audio controls style="width:100%">
  <source src="/{config.repo_name.split('/')[-1]}/assets/audio/{pid}.mp3" type="audio/mpeg">
  Your browser does not support audio.
</audio>

[View full summary + podcast page](/{config.repo_name.split('/')[-1]}/podcasts/{pid}/)
"""

    return body


def _escape(s):
    return s.replace('"', '\\"')


def generate_paper_pages(index):
    config.papers_dir.mkdir(parents=True, exist_ok=True)
    created = 0

    for paper_id, paper in index.items():
        md_path = config.papers_dir / f"{paper_id}.md"
        if md_path.exists():
            continue

        content = f"{paper_frontmatter(paper)}\n\n{paper_body(paper)}"
        with open(md_path, "w") as f:
            f.write(content)
        created += 1
        print(f"[generate] Created _papers/{paper_id}.md")

    print(f"[generate] Created {created} new paper pages.")
    return created


def generate_index_md(index):
    today = date.today().isoformat()

    new_papers_path = config.data_dir / "new_papers.txt"
    new_ids = set()
    if new_papers_path.exists():
        with open(new_papers_path) as f:
            new_ids = set(line.strip() for line in f if line.strip())

    if new_ids:
        todays_papers = {pid: index[pid] for pid in new_ids if pid in index}
        display_mode = "today"
    else:
        todays_papers = index
        display_mode = "all"

    sorted_papers = sorted(
        todays_papers.items(),
        key=lambda x: x[1].get("published_date", ""),
        reverse=True,
    )

    if display_mode == "today":
        intro = f"**{today}** — {len(sorted_papers)} new paper{'s' if len(sorted_papers) != 1 else ''} from arXiv. [📌 View favorites]({{{{ site.baseurl }}}}/favorites/) for archived papers.\n\n"
    else:
        intro = f"All {len(sorted_papers)} papers in the collection. [📌 View favorites]({{{{ site.baseurl }}}}/favorites/) for archived papers.\n\n"

    content = f"""---
layout: default
title: "Dexterous Grasp Daily"
---

# Dexterous Grasp — Daily Paper Digest

{intro}
"""

    for paper_id, paper in sorted_papers:
        title = paper.get("title", "Unknown")
        pub_date = paper.get("published_date", "")[:10]
        first_author = paper.get("first_author", "Unknown")
        abstract_preview = paper.get("abstract", "")[:300]
        if len(paper.get("abstract", "")) > 300:
            abstract_preview += "..."

        badges = []
        if paper.get("has_podcast"):
            badges.append("🎧 Podcast")
        if paper.get("interesting"):
            badges.append("📌 Archived")
        badge_str = " ".join(f"<span class=\"badge\">{b}</span>" for b in badges)

        content += f"""## [{title}]({{{{ site.baseurl }}}}/papers/{paper_id}/)

**{pub_date}** · {first_author} et al. {badge_str}

{abstract_preview}

[Read more →]({{{{ site.baseurl }}}}/papers/{paper_id}/)

---

"""

    with open(config.data_dir.parent / "index.md", "w") as f:
        f.write(content)

    print(f"[generate] Updated index.md with {len(sorted_papers)} papers (mode: {display_mode}, today: {today}).")


def main():
    index = load_index()
    if not index:
        print("[generate] No papers to generate.")
        return

    generate_paper_pages(index)
    generate_index_md(index)


if __name__ == "__main__":
    main()
