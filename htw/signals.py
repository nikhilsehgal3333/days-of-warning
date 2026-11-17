"""Signals from public APIs: Federal Register, the US Consolidated Screening List and Wikipedia
page views. Raw responses go to local/text/ so that the quote check can find the numbers.

    py -3.12 -m htw.signals            use local copies if present
    py -3.12 -m htw.signals --refresh  download again
"""
from __future__ import annotations

import csv
import json
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode

from . import net

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "local" / "text"
RESULTS = ROOT / "results"
FR_API = "https://www.federalregister.gov/api/v1/documents.json"
CSL_API = "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.json"
WIKI_API = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
            "all-access/user/Nexperia/daily/20240101/20251231")
SPIKE_KS = (3, 5, 10)
SPIKE_MIN_VIEWS = 500
BASELINE_DAYS = 28


def cached(source_id: str, url: str, refresh: bool) -> bytes:
    path = TEXT / f"{source_id}.txt"
    if path.exists() and not refresh:
        return path.read_bytes()
    body, _ = net.get(url, timeout=180)
    TEXT.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body


def federal_register(refresh: bool) -> list[dict]:
    rows = []
    for sid, term in [("fr_api_wingtech", "Wingtech"), ("fr_api_affiliates", "affiliates")]:
        query = urlencode({
            "conditions[term]": term,
            "conditions[agencies][]": "industry-and-security-bureau",
            "conditions[publication_date][gte]": "2024-01-01",
            "conditions[publication_date][lte]": "2025-12-31",
            "per_page": 100, "order": "oldest",
            "fields[]": ["document_number", "publication_date", "effective_on", "title", "html_url"],
        }, doseq=True)
        for d in json.loads(cached(sid, f"{FR_API}?{query}", refresh)).get("results", []):
            if d["document_number"] not in {r["document_number"] for r in rows}:
                rows.append({k: d.get(k) or "" for k in
                             ["document_number", "publication_date", "effective_on", "title", "html_url"]})
    return sorted(rows, key=lambda r: r["publication_date"])


def screening_list(refresh: bool) -> list[dict]:
    data = json.loads(cached("csl_api", CSL_API, refresh))
    out = []
    for r in data["results"]:
        if "wingtech" in json.dumps(r).lower() or "nexperia" in json.dumps(r).lower():
            out.append({"name": r.get("name", ""), "source": r.get("source", ""),
                        "start_date": r.get("start_date") or "",
                        "federal_register_notice": r.get("federal_register_notice") or "",
                        "countries": ";".join(sorted({a.get("country") or "" for a in r.get("addresses") or []}))})
    return out


def spikes(series: list[tuple[date, int]]) -> list[dict]:
    """Baseline of day t = median of the views on the 28 days before t. Day t is a spike for factor
    k if views >= k * baseline and views >= 500."""
    rows = []
    for i, (day, views) in enumerate(series):
        window = [v for _, v in series[max(0, i - BASELINE_DAYS):i]]
        base = statistics.median(window) if len(window) == BASELINE_DAYS else None
        row = {"date": day.isoformat(), "views": views, "baseline": base,
               "ratio": round(views / base, 2) if base else None}
        for k in SPIKE_KS:
            row[f"spike_k{k}"] = bool(base) and views >= k * base and views >= SPIKE_MIN_VIEWS
        rows.append(row)
    return rows


def page_views(refresh: bool) -> list[dict]:
    items = json.loads(cached("wiki_pageviews", WIKI_API, refresh))["items"]
    series = [(date(int(i["timestamp"][:4]), int(i["timestamp"][4:6]), int(i["timestamp"][6:8])),
               i["views"]) for i in items]
    return spikes(series)


def write(name: str, rows: list[dict]) -> None:
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / name, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(refresh: bool = False) -> dict:
    fr, csl, att = federal_register(refresh), screening_list(refresh), page_views(refresh)
    write("fr_documents.csv", fr)
    write("csl_entries.csv", csl)
    write("attention.csv", att)
    first = {k: next((r for r in att if r[f"spike_k{k}"]), None) for k in SPIKE_KS}
    return {"fr": fr, "csl": csl, "first_spike": first}


if __name__ == "__main__":
    out = run("--refresh" in sys.argv)
    print("Federal Register:", [(r["document_number"], r["publication_date"]) for r in out["fr"]])
    print("Screening list:", [(r["name"], r["start_date"], r["federal_register_notice"]) for r in out["csl"]])
    for k, r in out["first_spike"].items():
        print(f"first spike k={k}:", r and (r["date"], r["views"], r["baseline"]))
