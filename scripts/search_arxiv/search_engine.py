"""Search arXiv API for papers matching a topic configuration."""

from dataclasses import dataclass, field
from typing import List

import arxiv

from .config_reader import TopicConfig


@dataclass
class PaperInfo:
    """Structured information about a single arXiv paper.

    Attributes:
        arxiv_id: Clean arXiv ID without version suffix (e.g. "2606.09798").
        title: Paper title.
        abstract: Paper abstract (summary).
        authors: List of author names.
        first_author: First author's name.
        published_date: Publication date as "YYYY-MM-DD".
        primary_category: Primary arXiv category (e.g. "cs.RO").
        pdf_url: Direct PDF download URL.
        abs_url: Abstract page URL.
        topic: Name of the topic that matched this paper.
    """
    arxiv_id: str
    title: str
    abstract: str
    authors: List[str] = field(default_factory=list)
    first_author: str = "Unknown"
    published_date: str = ""
    primary_category: str = ""
    pdf_url: str = ""
    abs_url: str = ""
    topic: str = ""

    @property
    def entry_id(self) -> str:
        """Reconstruct the versioned arXiv entry URL."""
        return f"http://arxiv.org/abs/{self.arxiv_id}"


class ArxivSearchEngine:
    """Executes arXiv API searches using the `arxiv` Python library.

    Wraps arxiv.Search and arxiv.Result to produce clean PaperInfo objects.
    The arxiv library handles pagination and rate-limiting internally.
    """

    def search(self, topic_cfg: TopicConfig) -> List[PaperInfo]:
        """Search arXiv for papers matching the given topic configuration.

        Args:
            topic_cfg: Topic configuration with query and max_results.

        Returns:
            List of PaperInfo objects (unfiltered — apply PaperFilter separately).
        """
        search = arxiv.Search(
            query=topic_cfg.search_query,
            max_results=topic_cfg.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )

        # arxiv>=2.0 requires Client().results() — Search.results() was removed
        client = arxiv.Client()
        papers = []
        for result in client.results(search):
            info = self._to_paper_info(result, topic_cfg.name)
            papers.append(info)

        return papers

    @staticmethod
    def _to_paper_info(result: arxiv.Result, topic_name: str) -> PaperInfo:
        """Convert an arxiv.Result into a PaperInfo dataclass.

        Args:
            result: Raw result from the arxiv library.
            topic_name: Name of the topic being searched.

        Returns:
            Populated PaperInfo.
        """
        paper_id = result.get_short_id()

        # Strip version suffix (e.g. "2108.09112v1" → "2108.09112")
        ver_pos = paper_id.find("v")
        clean_id = paper_id[:ver_pos] if ver_pos != -1 else paper_id

        authors = [str(a) for a in result.authors]
        first_author = authors[0] if authors else "Unknown"
        abstract = result.summary.replace("\n", " ") if result.summary else ""
        published = result.published.date().isoformat() if result.published else ""

        return PaperInfo(
            arxiv_id=clean_id,
            title=result.title,
            abstract=abstract,
            authors=authors,
            first_author=first_author,
            published_date=published,
            primary_category=result.primary_category,
            pdf_url=f"https://arxiv.org/pdf/{clean_id}.pdf",
            abs_url=f"https://arxiv.org/abs/{clean_id}",
            topic=topic_name,
        )
