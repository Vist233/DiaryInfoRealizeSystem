import re
from typing import Iterable, Optional

WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")


def extract_wikilinks(text: str) -> list[str]:
    if not text:
        return []
    return list({m.group(1).strip(): None for m in WIKILINK_RE.finditer(text)}.keys())


def render_markdown_safe(text: str) -> str:
    """Render markdown to safe HTML.

    Tries to use python-markdown + bleach if available, otherwise falls back to a
    tiny renderer supporting headings, emphasis, code, and line breaks.
    """
    if not text:
        return ""

    # Try: markdown + bleach
    try:
        import markdown  # type: ignore
        import bleach  # type: ignore

        html = markdown.markdown(
            text,
            extensions=[
                'extra',
                'sane_lists',
                'smarty',
                'codehilite',
            ],
            output_format='html5',
        )
        allowed_tags = [
            'p', 'br', 'a', 'strong', 'em', 'code', 'pre',
            'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'blockquote'
        ]
        allowed_attrs = {
            'a': ['href', 'title', 'rel', 'data-wikilink'],
            'code': ['class'],
        }
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
    except Exception:
        pass

    # Fallback: minimal, escape then apply a few rules
    def escape(s: str) -> str:
        return (s
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    s = escape(text)
    s = re.sub(r'^###\s+(.*)$', r'<h3>\1</h3>', s, flags=re.M)
    s = re.sub(r'^##\s+(.*)$', r'<h2>\1</h2>', s, flags=re.M)
    s = re.sub(r'^#\s+(.*)$', r'<h1>\1</h1>', s, flags=re.M)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = s.replace('\n', '<br>')
    return s
