from pathlib import Path

import pymupdf


def extract_pages(file_path: Path) -> list[dict]:
    pages = []

    with pymupdf.open(file_path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()

            if not text:
                continue

            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages