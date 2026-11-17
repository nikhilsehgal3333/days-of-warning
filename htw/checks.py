"""Check every evidence row.

A row passes only if
- its source is tier 1 (primary or official) or tier 2 (established secondary), never tier 3
  (Wikipedia, blogs, aggregators), and
- its quote, 30 words or fewer, occurs word for word in the downloaded text.

    py -3.12 -m htw.checks
"""
from __future__ import annotations

import csv
from pathlib import Path

from .textnorm import quote_in_text

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "local" / "text"
MAX_WORDS = 30
ALLOWED_TIERS = {"1", "2"}


def evaluate(quote: str, text: str, tier: str) -> tuple[bool, str]:
    """Return (passes, reason). The reason is empty when the row passes."""
    if tier not in ALLOWED_TIERS:
        return False, "tier"
    if len(quote.split()) > MAX_WORDS:
        return False, "too long"
    if not quote_in_text(quote, text):
        return False, "quote not found"
    return True, ""


def run() -> list[dict]:
    root = ROOT
    tiers = {r["source_id"]: r.get("tier", "")
             for r in csv.DictReader(open(root / "case" / "sources.csv", encoding="utf-8"))}
    rows = list(csv.DictReader(open(root / "case" / "evidence.csv", encoding="utf-8")))
    out = []
    for row in rows:
        path = TEXT / f"{row['source_id']}.txt"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        tier = tiers.get(row["source_id"], "")
        found, reason = evaluate(row["quote"], text, tier)
        out.append({"evidence_id": row["evidence_id"], "quote_found": found, "reason": reason,
                    "source_id": row["source_id"], "tier": tier, "chars_in_text": len(text),
                    "quote_words": len(row["quote"].split())})
    (root / "results").mkdir(exist_ok=True)
    with open(root / "results" / "evidence_check.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    return out


def main() -> None:
    out = run()
    failed = [r for r in out if not r["quote_found"]]
    print(f"{len(out) - len(failed)} of {len(out)} rows pass the check")
    for r in failed:
        print(f"  FAIL {r['evidence_id']} ({r['source_id']}, tier {r['tier'] or '?'}): {r['reason']}")


if __name__ == "__main__":
    main()
