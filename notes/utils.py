import re

WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")


def extract_wikilinks(text: str) -> list[str]:
    if not text:
        return []
    return list({m.group(1).strip(): None for m in WIKILINK_RE.finditer(text)}.keys())

