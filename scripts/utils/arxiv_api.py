import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

ARXIV_API_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


class ArxivFetchError(Exception):
    pass


def fetch_abstract(arxiv_id, max_retries=3):
    clean_id = arxiv_id.split("v")[0].strip()
    url = f"http://export.arxiv.org/api/query?id_list={clean_id}&max_results=1"

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ResearchPipeline/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_data = resp.read().decode("utf-8")
            return _parse_atom(xml_data, arxiv_id)
        except urllib.error.HTTPError as e:
            if e.code == 503 and attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise ArxivFetchError(f"HTTP {e.code} fetching {clean_id}")
        except urllib.error.URLError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise ArxivFetchError(f"URL error fetching {clean_id}: {e}")
        except Exception as e:
            raise ArxivFetchError(f"Error fetching {clean_id}: {e}")
    raise ArxivFetchError(f"Max retries exceeded for {clean_id}")


def _parse_atom(xml_data, arxiv_id):
    root = ET.fromstring(xml_data)
    entry = root.find(f"{ARXIV_API_NS}entry")
    if entry is None:
        raise ArxivFetchError(f"No entry found for {arxiv_id}")

    title_el = entry.find(f"{ARXIV_API_NS}title")
    title = title_el.text.strip() if title_el is not None else "Unknown"

    summary_el = entry.find(f"{ARXIV_API_NS}summary")
    abstract = summary_el.text.strip() if summary_el is not None else ""

    published_el = entry.find(f"{ARXIV_API_NS}published")
    published = published_el.text.strip()[:10] if published_el is not None else ""

    updated_el = entry.find(f"{ARXIV_API_NS}updated")
    updated = updated_el.text.strip()[:10] if updated_el is not None else ""

    authors = []
    for author in entry.findall(f"{ARXIV_API_NS}author"):
        name_el = author.find(f"{ARXIV_API_NS}name")
        if name_el is not None:
            authors.append(name_el.text.strip())

    primary_cat_el = entry.find(f"{ARXIV_NS}primary_category")
    primary_category = primary_cat_el.get("term", "") if primary_cat_el is not None else ""

    links = []
    for link in entry.findall(f"{ARXIV_API_NS}link"):
        href = link.get("href", "")
        rel = link.get("rel", "")
        title_attr = link.get("title", "")
        links.append({"href": href, "rel": rel, "title": title_attr})

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id.split('v')[0]}.pdf"
    abs_url = f"https://arxiv.org/abs/{arxiv_id.split('v')[0]}"

    return {
        "arxiv_id": arxiv_id.split("v")[0],
        "title": title,
        "abstract": abstract,
        "published_date": published,
        "updated_date": updated,
        "authors": authors,
        "first_author": authors[0] if authors else "Unknown",
        "primary_category": primary_category,
        "pdf_url": pdf_url,
        "abs_url": abs_url,
    }


def get_pdf_url(arxiv_id):
    clean_id = arxiv_id.split("v")[0]
    return f"https://arxiv.org/pdf/{clean_id}.pdf"
