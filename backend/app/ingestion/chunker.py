def _new_parent(section: dict) -> dict:
    return {
        "page": section["page"],
        "section": section["section"],
        "text": section["text"],
        # Where each page begins inside the parent text:
        # [(character_offset, page_number), ...]
        "page_starts": [(0, section["page"])],
    }


def _append_section(parent: dict, section: dict) -> None:
    # +1 for the "\n" that joins the two texts
    offset = len(parent["text"]) + 1

    parent["text"] += "\n" + section["text"]

    if section["page"] != parent["page_starts"][-1][1]:
        parent["page_starts"].append((offset, section["page"]))


def _page_at(parent: dict, offset: int) -> int:
    """
    Page number of the character at `offset` in the parent text.
    """

    page = parent["page"]

    for start, page_number in parent["page_starts"]:
        if start > offset:
            break
        page = page_number

    return page


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

    Sections are at most one page long (detect_sections splits
    at page breaks), so max_parent_chars is always respected
    unless a single page is longer than the limit.
    """

    parents = []

    current = None

    for section in sections:

        if current is None:
            current = _new_parent(section)
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
            current = _new_parent(section)

        else:
            # When merging, label the parent with the section that
            # contributes the most text (a short running page header
            # like "STRUCTURE AND CONTENT OF ..." should not win).
            if len(section["text"]) > len(current["text"]):
                current["section"] = section["section"]

            _append_section(current, section)

    if current is not None:
        # A small last section is merged into the previous parent
        if (
            parents
            and len(current["text"]) < min_parent_chars
            and len(parents[-1]["text"]) + len(current["text"]) <= max_parent_chars
        ):
            _append_section(parents[-1], current)
        else:
            parents.append(current)

    return parents


def _last_whitespace(text: str, low: int, high: int) -> int:
    return max(text.rfind(" ", low, high), text.rfind("\n", low, high))


def _next_whitespace(text: str, low: int, high: int) -> int:
    found = [
        index
        for index in (text.find(" ", low, high), text.find("\n", low, high))
        if index != -1
    ]

    return min(found) if found else -1


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

            # Don't cut a word in half: end at the last whitespace
            # in the second half of the window.
            if end < len(text):
                space = _last_whitespace(text, start + child_size // 2, end)

                if space != -1:
                    end = space

            chunk_text = text[start:end].strip()

            if chunk_text:
                children.append(
                    {
                        "parent_index": parent_index,
                        # The page containing the middle of this chunk
                        "page": _page_at(parent, (start + end) // 2),
                        "section": parent["section"],
                        "text": chunk_text,
                        "position": position,
                    }
                )

                position += 1

            if end >= len(text):
                break

            # Overlap with the previous chunk, starting on a word boundary
            start = end - overlap

            space = _next_whitespace(text, start, end)

            if space != -1:
                start = space + 1

    return children
