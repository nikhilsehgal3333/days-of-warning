"""False-alarm test for a case that has case/<id>/signal_class.csv (pre-registered rule R7).

Each measure of the signal class has a source quote for its date, and an outcome: "stop found" (with
a source quote) or "no stop found" (after the search protocol in search_log.csv). Quotes pass the
same check as the evidence rows (source tier 1 or 2, quote word for word in the text).

    py -3.12 -m htw.falsealarm [--case <id>]
"""
from __future__ import annotations

import csv

from . import paths
from .checks import evaluate


def count(rows: list[dict]) -> dict:
    """Stops, borderline cases and precision of a signal class."""
    stops = sum(1 for r in rows if r["outcome"] == "stop found")
    borderline = sum(1 for r in rows if r["borderline"] and r["outcome"] != "stop found")
    return {"n": len(rows), "stops": stops, "borderline": borderline,
            "precision": round(stops / len(rows), 3),
            "precision_with_borderline": round((stops + borderline) / len(rows), 3)}


def available(case: str) -> bool:
    return (paths.case_dir(case) / "signal_class.csv").exists()


def run(case: str) -> dict | None:
    if not available(case):
        return None
    cdir, tdir = paths.case_dir(case), paths.text_dir(case)
    tiers = {r["source_id"]: r.get("tier", "") for r in csv.DictReader(open(cdir / "sources.csv", encoding="utf-8"))}

    def check(source_id: str, quote: str) -> tuple[bool, str]:
        path = tdir / f"{source_id}.txt"
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        return evaluate(quote, text, tiers.get(source_id, ""))

    rows = list(csv.DictReader(open(cdir / "signal_class.csv", encoding="utf-8")))
    log = list(csv.DictReader(open(cdir / "search_log.csv", encoding="utf-8"))) if (cdir / "search_log.csv").exists() else []
    out = []
    for r in rows:
        date_ok, date_reason = check(r["source_id"], r["quote"])
        if r["outcome"] == "stop found":
            out_ok, out_reason = check(r["outcome_source_id"], r["outcome_quote"])
        else:
            searches = [s for s in log if s["measure_id"] == r["measure_id"]]
            out_ok, out_reason = (len(searches) > 0, "" if searches else "no search logged")
        out.append({"measure_id": r["measure_id"], "material": r["material"], "announced": r["announced"],
                    "effective": r["effective"], "outcome": r["outcome"],
                    "borderline": "borderline" in r["note"], "date_check": date_ok,
                    "outcome_check": out_ok, "reason": "; ".join(x for x in (date_reason, out_reason) if x),
                    "searches_logged": sum(1 for s in log if s["measure_id"] == r["measure_id"])})
    c = count(out)
    stops, borderline = c["stops"], c["borderline"]
    with open(paths.results_dir(case) / "false_alarms.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out[0]))
        writer.writeheader()
        writer.writerows(out)
    return {"rows": out, "n": len(out), "stops": stops, "borderline": borderline,
            "precision": round(stops / len(out), 3),
            "precision_with_borderline": round((stops + borderline) / len(out), 3),
            "all_checked": all(r["date_check"] and r["outcome_check"] for r in out)}


def markdown(fa: dict) -> str:
    lines = ["## False-alarm test (rule R7)", "",
             f"Of {fa['n']} Chinese export-control measures on materials (July 2023 to October 2025), "
             f"**{fa['stops']}** was followed by a production stop within 6 months, so the class precision is "
             f"**{fa['stops']} of {fa['n']}**. With the borderline case counted as a stop: "
             f"{fa['stops'] + fa['borderline']} of {fa['n']}. "
             + ("All date and outcome quotes pass the check." if fa["all_checked"] else
                "Some quotes fail the check; see false_alarms.csv."),
             "", "| Measure | Material | Announced | Outcome | Searches logged |", "|---|---|---|---|---|"]
    for r in fa["rows"]:
        lines.append(f"| {r['measure_id']} | {r['material']} | {r['announced']} | {r['outcome']}"
                     f"{' (borderline case recorded)' if r['borderline'] and r['outcome'] != 'stop found' else ''} | "
                     f"{r['searches_logged']} |")
    lines += ["", "\"No stop found\" means that the logged search found no tier-1 or tier-2 report of a stop. "
              "It does not prove that no stop happened."]
    return "\n".join(lines)


if __name__ == "__main__":
    chosen, _ = paths.selected()
    for case in chosen:
        fa = run(case)
        if fa:
            print(markdown(fa))
