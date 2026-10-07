import re


# "9.4.2 Identity of Investigational Product(s)", "12. SAFETY EVALUATION"
# A number alone ("1.", "8 (+1)") is NOT a heading: a word must follow it.
NUMBERED_HEADING = re.compile(r"^\d+(\.\d+)*\.?\s+[A-Za-z]")

# Table-of-contents line: "Identity of Investigational Product(s).......7"
TOC_LINE = re.compile(r"\.{5,}\s*\d*$")


def is_heading(line: str) -> bool:
    line = line.strip()

    if not line:
        return False

    if len(line) > 120:
        return False

    if NUMBERED_HEADING.match(line):
        return True

    # ALL-CAPS heading with real words.
    # Table cells like "N", "NR*", "N=50" or "(R2)" have too few letters.
    letters = sum(char.isalpha() for char in line)

    if line.isupper() and letters >= 4 and len(line.split()) <= 12:
        return True

    return False


def detect_sections(pages: list[dict]) -> list[dict]:
    sections = []

    current_section = None
    current_page = None  # page the current piece of text is on
    current_text = []

    def flush():
        text = "\n".join(current_text).strip()

        if not text:
            return

        sections.append(
            {
                "page": current_page,
                "section": current_section,
                "text": text,
            }
        )

    for page in pages:

        # A page break closes the current piece of text, so every
        # piece belongs to exactly one page and citations can point
        # to the right page. The section name carries over.
        flush()
        current_text.clear()
        current_page = page["page"]

        for line in page["text"].splitlines():
            line = line.strip()

            if not line:
                continue

            # Table-of-contents lines are navigation, not content
            if TOC_LINE.search(line):
                continue

            if is_heading(line):
                flush()

                current_section = line

                # Keep the heading in the text so it is searchable
                # (e.g. BM25 can match "title page" to "TITLE PAGE").
                current_text.clear()
                current_text.append(line)

                continue

            current_text.append(line)

    flush()

    return sections
