def create_parent_chunks(
    sections: list[dict],
    max_parent_chars: int = 4000,
    min_parent_chars: int = 500,
) -> list[dict]:
    """
    Group sections into parent chunks.

    A new parent starts at a new section, but only once the
    current parent has at least min_parent_chars of text.
    Small sections (short headings, table cells detected as
    headings) are merged into the current parent instead of
    becoming tiny, meaningless chunks of their own.
    """

    parents = []

    current = None

    for section in sections:

        if current is None:
            current = {
                "page": section["page"],
                "section": section["section"],
                "text": section["text"],
            }
            continue

        too_big = (
            len(current["text"]) + len(section["text"]) > max_parent_chars
        )

        new_section_and_big_enough = (
            section["section"] != current["section"]
            and len(current["text"]) >= min_parent_chars
        )

        if too_big or new_section_and_big_enough:
            parents.append(current)

            current = {
                "page": section["page"],
                "section": section["section"],
                "text": section["text"],
            }

        else:
            # When merging, label the parent with the section that
            # contributes the most text (a short running page header
            # like "STRUCTURE AND CONTENT OF ..." should not win).
            if len(section["text"]) > len(current["text"]):
                current["section"] = section["section"]

            current["text"] += "\n" + section["text"]

    if current is not None:
        # A small last section is merged into the previous parent
        if (
            parents
            and len(current["text"]) < min_parent_chars
            and len(parents[-1]["text"]) + len(current["text"]) <= max_parent_chars
        ):
            parents[-1]["text"] += "\n" + current["text"]
        else:
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