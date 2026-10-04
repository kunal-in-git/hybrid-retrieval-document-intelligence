def create_chunks(
    pages: list[dict],
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    chunks = []

    position = 0

    for page in pages:
        text = page["text"]
        page_number = page["page"]

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "text": chunk_text,
                        "page": page_number,
                        "section": None,
                        "position": position,
                    }
                )

                position += 1

            if end >= len(text):
                break

            start = end - overlap

    return chunks