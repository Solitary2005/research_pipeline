#!/usr/bin/env python3
"""Generate Jekyll paper pages and index.md from papers_index.json."""

import json
import sys
from pathlib import Path
from urllib.parse import quote

from scripts.utils.config import config


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

    body = f"""## Abstract

{abstract}

## Links

- [arXiv]({paper.get('abs_url', f'https://arxiv.org/abs/{pid}')})
- [PDF]({paper.get('pdf_url', f'https://arxiv.org/pdf/{pid}.pdf')})

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

[View full summary + podcast page](/podcasts/{pid}/)
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
    sorted_papers = sorted(
        index.items(),
        key=lambda x: x[1].get("published_date", ""),
        reverse=True,
    )

    content = """---
layout: default
title: "Dexterous Grasp Daily"
---

# Dexterous Grasp — Daily Paper Digest

Papers updated daily from arXiv. Click a paper to read the abstract, or request an AI-generated summary + Chinese podcast.

"""

    for paper_id, paper in sorted_papers:
        title = paper.get("title", "Unknown")
        date = paper.get("published_date", "")[:10]
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

**{date}** · {first_author} et al. {badge_str}

{abstract_preview}

[Read more →]({{{{ site.baseurl }}}}/papers/{paper_id}/)

---

"""

    with open(config.data_dir.parent / "index.md", "w") as f:
        f.write(content)

    print(f"[generate] Updated index.md with {len(sorted_papers)} papers.")


def main():
    index = load_index()
    if not index:
        print("[generate] No papers to generate.")
        return

    generate_paper_pages(index)
    generate_index_md(index)


if __name__ == "__main__":
    main()
