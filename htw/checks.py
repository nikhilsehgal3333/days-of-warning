"""Check every evidence row of a case.

A row passes only if
- its source is tier 1 (primary or official) or tier 2 (established secondary), never tier 3
  (Wikipedia, blogs, aggregators), and
- its quote, 30 words or fewer, occurs word for word in the downloaded text.

    py -3.12 -m htw.checks [--case <id>]
"""
from __future__ import annotations

import csv

from . import paths
from .textnorm import quote_in_text

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


def run(case: str) -> list[dict]:
    cdir, tdir = paths.case_dir(case), paths.text_dir(case)
    tiers = {r["source_id"]: r.get("tier", "")
             for r in csv.DictReader(open(cdir / "sources.csv", encoding="utf-8"))}
    out = []
    for row in csv.DictReader(open(cdir / "evidence.csv", encoding="utf-8")):
        path = tdir / f"{row['source_id']}.txt"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        tier = tiers.get(row["source_id"], "")
        found, reason = evaluate(row["quote"], text, tier)
        out.append({"evidence_id": row["evidence_id"], "quote_found": found, "reason": reason,
                    "source_id": row["source_id"], "tier": tier, "chars_in_text": len(text),
                    "quote_words": len(row["quote"].split())})
    with open(paths.results_dir(case) / "evidence_check.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    return out


def check_assumptions(case: str) -> list[dict]:
    """Check the source quotes behind the time-to-act grid (columns basis_* and basis2_*)."""
    cdir, tdir = paths.case_dir(case), paths.text_dir(case)
    tiers = {r["source_id"]: r.get("tier", "")
             for r in csv.DictReader(open(cdir / "sources.csv", encoding="utf-8"))}
    out = []
    for row in csv.DictReader(open(cdir / "assumptions.csv", encoding="utf-8")):
        for prefix in ("basis", "basis2"):
            sid, quote = row.get(f"{prefix}_source_id") or "", row.get(f"{prefix}_quote") or ""
            if not sid:
                continue
            path = tdir / f"{sid}.txt"
            text = path.read_text(encoding="utf-8") if path.exists() else ""
            found, reason = evaluate(quote, text, tiers.get(sid, ""))
            out.append({"name": row["name"], "source_id": sid, "quote_found": found, "reason": reason})
    if out:
        with open(paths.results_dir(case) / "assumption_check.csv", "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(out[0]))
            writer.writeheader()
            writer.writerows(out)
    return out


def main() -> None:
    chosen, _ = paths.selected()
    for case in chosen:
        out = run(case)
        failed = [r for r in out if not r["quote_found"]]
        print(f"[{case}] {len(out) - len(failed)} of {len(out)} rows pass the check")
        for r in failed:
            print(f"  FAIL {r['evidence_id']} ({r['source_id']}, tier {r['tier'] or '?'}): {r['reason']}")


if __name__ == "__main__":
    main()
