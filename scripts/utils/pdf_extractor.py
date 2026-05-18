import re

MAX_CHARS = 100000


def extract_text(pdf_path):
    text = _extract_with_pymupdf(pdf_path)
    if not text or len(text.strip()) < 500:
        text = _extract_with_pdfplumber(pdf_path)

    text = _clean_text(text)
    was_truncated = len(text) > MAX_CHARS
    if was_truncated:
        text = text[:MAX_CHARS]
        last_period = text.rfind(".")
        if last_period > MAX_CHARS * 0.8:
            text = text[:last_period + 1]

    return text, was_truncated


def _extract_with_pymupdf(pdf_path):
    try:
        import fitz
        doc = fitz.open(pdf_path)
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n\n".join(pages)
    except Exception:
        return ""


def _extract_with_pdfplumber(pdf_path):
    try:
        import pdfplumber
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
        return "\n\n".join(pages)
    except Exception:
        return ""


def _clean_text(text):
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{3,}", "  ", text)
    ref_idx = text.rfind("\nReferences\n")
    if ref_idx == -1:
        ref_idx = text.rfind("\nREFERENCES\n")
    if ref_idx == -1:
        ref_idx = text.rfind("\nBibliography\n")
    if ref_idx > len(text) * 0.5:
        text = text[:ref_idx]
    return text.strip()
