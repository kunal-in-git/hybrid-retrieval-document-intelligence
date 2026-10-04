import re


def is_heading(line: str) -> bool:
    line = line.strip()

    if not line:
        return False

    if len(line) > 150:
        return False

    if re.match(r"^\d+(\.\d+)*[\s.)-]+", line):
        return True

    if line.isupper() and len(line.split()) <= 12:
        return True

    return False


def detect_sections(pages: list[dict]) -> list[dict]:
    sections = []

    current_section = None
    current_text = []

    def flush():
        if not current_text:
            return

        sections.append(
            {
                "page": current_page,
                "section": current_section,
                "text": "\n".join(current_text).strip(),
            }
        )

    current_page = None

    for page in pages:
        current_page = page["page"]

        for line in page["text"].splitlines():
            line = line.strip()

            if not line:
                continue

            if is_heading(line):
                flush()

                current_section = line
                current_text.clear()

                continue

            current_text.append(line)

    flush()

    return sections