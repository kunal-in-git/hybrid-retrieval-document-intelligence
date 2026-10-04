def create_parent_chunks(
    sections: list[dict],
    max_parent_chars: int = 4000,
) -> list[dict]:

    parents = []

    current = None

    for section in sections:
        if (
            current is None
            or current["section"] != section["section"]
            or len(current["text"]) + len(section["text"]) > max_parent_chars
        ):
            if current is not None:
                parents.append(current)

            current = {
                "page": section["page"],
                "section": section["section"],
                "text": section["text"],
            }

        else:
            current["text"] += "\n" + section["text"]

    if current is not None:
        parents.append(current)

    return parents

def create_child_chunks(
    parents: list[dict],
    child_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:

    children = []

    position = 0

    for parent_index, parent in enumerate(parents):

        text = parent["text"]

        start = 0

        while start < len(text):

            end = start + child_size

            chunk_text = text[start:end].strip()

            if chunk_text:
                children.append(
                    {
                        "parent_index": parent_index,
                        "page": parent["page"],
                        "section": parent["section"],
                        "text": chunk_text,
                        "position": position,
                    }
                )

                position += 1

            if end >= len(text):
                break

            start = end - overlap

    return children