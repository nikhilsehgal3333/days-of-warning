"""Signals from public APIs, as set in case/<id>/config.json under "signals":

- "federal_register": list of {"source_id", "term"}, with "federal_register_window" [from, to]
- "csl": {"source_id", "terms"}  (US Consolidated Screening List)
- "pageviews": list of {"source_id", "article", "subject", "start", "end"}  (Wikipedia page views,
  the official Wikimedia statistics; an attention measure, not article text)

Raw responses go to local/<case>/text/ so that the quote check can find numbers in them.

    py -3.12 -m htw.signals [--case <id>] [--refresh]
"""
from __future__ import annotations

import csv
import json
import statistics
from datetime import date
from urllib.parse import quote, urlencode

from . import net, paths

FR_API = "https://www.federalregister.gov/api/v1/documents.json"
CSL_API = "https://data.trade.gov/downloadable_consolidated_screening_list/v1/consolidated.json"
WIKI_API = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
            "all-access/user/{article}/daily/{start}/{end}")
SPIKE_KS = (3, 5, 10)
SPIKE_MIN_VIEWS = 500
BASELINE_DAYS = 28


def cached(case: str, source_id: str, url: str, refresh: bool) -> bytes:
    path = paths.text_dir(case) / f"{source_id}.txt"
    if path.exists() and not refresh:
        return path.read_bytes()
    body, _ = net.get(url, timeout=180)
    path.write_bytes(body)
    return body


def federal_register(case: str, cfg: dict, refresh: bool) -> list[dict]:
    lo, hi = cfg.get("federal_register_window", ["2024-01-01", "2025-12-31"])
    rows = []
    for q in cfg.get("federal_register", []):
        query = urlencode({
            "conditions[term]": q["term"],
            "conditions[agencies][]": "industry-and-security-bureau",
            "conditions[publication_date][gte]": lo,
            "conditions[publication_date][lte]": hi,
            "per_page": 100, "order": "oldest",
            "fields[]": ["document_number", "publication_date", "effective_on", "title", "html_url"],
        }, doseq=True)
        for d in json.loads(cached(case, q["source_id"], f"{FR_API}?{query}", refresh)).get("results", []):
            if d["document_number"] not in {r["document_number"] for r in rows}:
                rows.append({k: d.get(k) or "" for k in
                             ["document_number", "publication_date", "effective_on", "title", "html_url"]})
    return sorted(rows, key=lambda r: r["publication_date"])


def screening_list(case: str, cfg: dict, refresh: bool) -> list[dict]:
    spec = cfg.get("csl")
    if not spec:
        return []
    data = json.loads(cached(case, spec["source_id"], CSL_API, refresh))
    out = []
    for r in data["results"]:
        blob = json.dumps(r).lower()
        if any(term in blob for term in spec["terms"]):
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


def page_views(case: str, spec: dict, refresh: bool) -> list[dict]:
    url = WIKI_API.format(article=quote(spec["article"].replace(" ", "_")), start=spec["start"], end=spec["end"])
    items = json.loads(cached(case, spec["source_id"], url, refresh))["items"]
    series = [(date(int(i["timestamp"][:4]), int(i["timestamp"][4:6]), int(i["timestamp"][6:8])),
               i["views"]) for i in items]
    return spikes(series)


def write(case: str, name: str, rows: list[dict]) -> None:
    if not rows:
        return
    with open(paths.results_dir(case) / name, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(case: str, refresh: bool = False) -> dict:
    cfg = paths.config(case).get("signals", {})
    fr = federal_register(case, cfg, refresh)
    csl = screening_list(case, cfg, refresh)
    write(case, "fr_documents.csv", fr)
    write(case, "csl_entries.csv", csl)
    first = {}
    for spec in cfg.get("pageviews", []):
        att = page_views(case, spec, refresh)
        write(case, f"attention_{spec['source_id']}.csv", att)
        first[spec["article"]] = {k: next((r for r in att if r[f"spike_k{k}"]), None) for k in SPIKE_KS}
    return {"fr": fr, "csl": csl, "first_spike": first}


if __name__ == "__main__":
    chosen, refresh = paths.selected()
    for case in chosen:
        out = run(case, refresh)
        print(f"[{case}] Federal Register:", [(r["document_number"], r["publication_date"]) for r in out["fr"]])
        print(f"[{case}] Screening list:", [(r["name"], r["start_date"]) for r in out["csl"]])
        for article, f in out["first_spike"].items():
            print(f"[{case}] first spike k=5 for {article}:", f[5] and (f[5]["date"], f[5]["views"]))
