"""Check every evidence row: its quote must occur word for word in the downloaded text.

    py -3.12 -m htw.checks
"""
from __future__ import annotations

import csv
from pathlib import Path

from .textnorm import quote_in_text

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "local" / "text"
MAX_WORDS = 30


def run() -> list[dict]:
    rows = list(csv.DictReader(open(ROOT / "case" / "evidence.csv", encoding="utf-8")))
    out = []
    for row in rows:
        path = TEXT / f"{row['source_id']}.txt"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        words = len(row["quote"].split())
        found = quote_in_text(row["quote"], text) and words <= MAX_WORDS
        out.append({"evidence_id": row["evidence_id"], "quote_found": found,
                    "source_id": row["source_id"], "chars_in_text": len(text), "quote_words": words})
    (ROOT / "results").mkdir(exist_ok=True)
    with open(ROOT / "results" / "evidence_check.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    return out


def main() -> None:
    out = run()
    failed = [r for r in out if not r["quote_found"]]
    print(f"{len(out) - len(failed)} of {len(out)} rows pass the quote check")
    for r in failed:
        print(f"  FAIL {r['evidence_id']} ({r['source_id']}, {r['chars_in_text']} chars, "
              f"{r['quote_words']} words)")


if __name__ == "__main__":
    main()
