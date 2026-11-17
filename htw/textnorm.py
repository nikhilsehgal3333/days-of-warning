"""Text normalisation and the word-for-word quote check."""
from __future__ import annotations

import re

_TYPOGRAPHIC = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "′": "'",
    "“": '"', "”": '"', "„": '"', "″": '"',
    "–": "-", "‑": "-", " ": " ",
})


def squeeze(text: str) -> str:
    """The same rule as `squeeze` in the sector likelihood register."""
    return re.sub(r"\s+", " ", text).strip().lower()


def plain(text: str) -> str:
    return text.translate(_TYPOGRAPHIC)


def quote_in_text(quote: str, text: str) -> bool:
    """True if the quote occurs word for word in the text, ignoring white space, case and
    typographic quote marks."""
    q = squeeze(plain(quote))
    return bool(q) and q in squeeze(plain(text))
