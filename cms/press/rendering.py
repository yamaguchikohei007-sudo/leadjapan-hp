import re

from markdown_it import MarkdownIt

_SAFE_LINK = re.compile(r"^(?:https?://|mailto:)", re.IGNORECASE)
_HAS_SCHEME = re.compile(r"^[a-z][a-z0-9+.\-]*:", re.IGNORECASE)


def _is_safe(url: str) -> bool:
    url = url.strip()
    return bool(_SAFE_LINK.match(url)) or not _HAS_SCHEME.match(url)


def _sanitize_inline_tokens(state) -> None:
    """Unwrap unsafe links and replace all body images with escaped alt text."""
    for block in state.tokens:
        if block.type != "inline" or not block.children:
            continue
        kept, skipping = [], []
        for tok in block.children:
            if tok.type == "link_open":
                unsafe = not _is_safe(tok.attrGet("href") or "")
                skipping.append(unsafe)
                if unsafe:
                    continue
            elif tok.type == "link_close":
                if skipping.pop():
                    continue
            elif tok.type == "image":
                tok.type, tok.tag, tok.attrs, tok.children = "text", "", {}, None
            kept.append(tok)
        block.children = kept


_md = MarkdownIt("commonmark", {"html": False})
_md.validateLink = lambda url: True  # unsafe URLs are unwrapped by _sanitize_inline_tokens
_md.core.ruler.push("sanitize_inline_tokens", _sanitize_inline_tokens)


def render_markdown(md: str) -> str:
    return _md.render(md)
