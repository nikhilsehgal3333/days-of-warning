"""Visibility, signals, lead times, the time-to-act grid, connection and the map value.

Rows that share an id prefix (E04a, E04b) describe one event or link. The event or link takes the
earliest public date of its checked rows.

    py -3.12 -m htw.analysis
"""
from __future__ import annotations

import csv
import re
from collections import deque
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
SUSTAINED_DAYS = 3  # added after seeing the data: one-day spikes in 2024 were noise


def d(text: str) -> date:
    return date.fromisoformat(text)


def group_id(evidence_id: str) -> str:
    return re.sub(r"[a-z]+$", "", evidence_id)


def load_checked() -> list[dict]:
    ok = {r["evidence_id"] for r in csv.DictReader(open(RESULTS / "evidence_check.csv", encoding="utf-8"))
          if r["quote_found"] == "True"}
    return [r for r in csv.DictReader(open(ROOT / "case" / "evidence.csv", encoding="utf-8"))
            if r["evidence_id"] in ok]


def grid() -> list[tuple[int, int]]:
    a = {r["name"]: [int(v) for v in r["values"].split(";")]
         for r in csv.DictReader(open(ROOT / "case" / "assumptions.csv", encoding="utf-8"))}
    return [(tts, ttr) for tts in a["tts_days"] for ttr in a["ttr_days"]]


def links_of(rows: list[dict]) -> dict:
    links = {}
    for r in rows:
        if r["type"] != "link":
            continue
        level = "generic" if "level=generic" in r["note"] else "named"
        key = (group_id(r["evidence_id"]), level)
        item = links.setdefault(key, {"link_id": key[0], "level": level, "subject": r["subject"],
                                      "relation": r["relation"], "object": r["object"], "rows": []})
        item["rows"].append(r)
    for item in links.values():
        first = min(item["rows"], key=lambda r: r["public_date"])
        item["visible_from"] = first["public_date"]
        item["first_source_id"] = first["source_id"]
        item["n_evidence"] = len(item["rows"])
    return links


def events_of(rows: list[dict]) -> list[dict]:
    events = {}
    for r in rows:
        if r["type"] != "event":
            continue
        events.setdefault(group_id(r["evidence_id"]), []).append(r)
    out = []
    for gid, rs in events.items():
        first = min(rs, key=lambda r: r["public_date"])
        out.append({"event_id": gid, "subject": first["subject"], "relation": first["relation"],
                    "channel": first["channel"], "event_date": min(r["event_date"] for r in rs),
                    "public_date": first["public_date"], "source_id": first["source_id"],
                    "note": first["note"]})
    return sorted(out, key=lambda e: e["public_date"])


def attention_event() -> tuple[dict | None, list[str]]:
    rows = list(csv.DictReader(open(RESULTS / "attention.csv", encoding="utf-8")))
    spike_days = [r["date"] for r in rows if r["spike_k5"] == "True"]
    run, isolated = [], []
    for i, r in enumerate(rows):
        if r["spike_k5"] != "True":
            continue
        window = rows[i:i + SUSTAINED_DAYS]
        if len(window) == SUSTAINED_DAYS and all(w["spike_k5"] == "True" for w in window):
            run = [r]
            break
    first_run = run[0] if run else None
    if first_run:
        isolated = [s for s in spike_days if s < first_run["date"]]
    event = None
    if first_run:
        event = {"event_id": "A01", "subject": "NEX", "relation": "attention", "channel": "attention",
                 "event_date": first_run["date"], "public_date": first_run["date"],
                 "source_id": "wiki_pageviews",
                 "note": f"first of {SUSTAINED_DAYS}+ spike days in a row (k=5): {first_run['views']} views"}
    return event, isolated


def connected(target: str, links: list[dict], on: str | None) -> bool:
    usable = [l for l in links if on is None or l["visible_from"] <= on]
    seen, queue = {"VM"}, deque(["VM"])
    while queue:
        node = queue.popleft()
        if node == target:
            return True
        for l in usable:
            if l["object"] == node and l["subject"] not in seen:
                seen.add(l["subject"])
                queue.append(l["subject"])
    return False


def run() -> dict:
    rows = load_checked()
    links = links_of(rows)
    named = [l for l in links.values() if l["level"] == "named"]
    every = list(links.values())
    events = events_of(rows)
    att, isolated = attention_event()
    if att:
        events = sorted(events + [att], key=lambda e: e["public_date"])
    stops = [e for e in events if e["relation"] == "production_stop"]
    warns = [e for e in events if e["relation"] == "warning"]
    t_stop = min(e["public_date"] for e in stops)
    t_warn = min(e["public_date"] for e in warns) if warns else ""
    cells = grid()
    needed = sorted({ttr - tts for tts, ttr in cells})
    lead_rows = []
    for e in events:
        if e["public_date"] >= t_stop:
            continue
        lead = (d(t_stop) - d(e["public_date"])).days
        share = sum(lead >= ttr - tts for tts, ttr in cells) / len(cells)
        lead_rows.append({
            "event_id": e["event_id"], "subject": e["subject"], "relation": e["relation"],
            "channel": e["channel"], "public_date": e["public_date"], "lead_days": lead,
            "actionable_share": round(share, 3),
            "connected_A": connected(e["subject"], named, e["public_date"]),
            "connected_A_generic": connected(e["subject"], every, e["public_date"]),
            "connected_B": connected(e["subject"], named, None),
        })
    observers = []
    for name, col in [("A (public map, named links)", "connected_A"),
                      ("A, variant with generic links", "connected_A_generic"),
                      ("B (full map)", "connected_B")]:
        first = next((r for r in lead_rows if r[col] and r["actionable_share"] > 0), None)
        first_any = next((r for r in lead_rows if r[col]), None)
        observers.append({"observer": name, "first_event": first["event_id"] if first else "",
                          "public_date": first["public_date"] if first else "",
                          "lead_days": first["lead_days"] if first else 0,
                          "first_connected_any": first_any["event_id"] if first_any else "",
                          "first_connected_any_lead": first_any["lead_days"] if first_any else 0})
    map_value = observers[2]["lead_days"] - observers[0]["lead_days"]
    map_value_generic = observers[2]["lead_days"] - observers[1]["lead_days"]
    write("visibility.csv", [{k: l[k] for k in ["link_id", "level", "subject", "relation", "object",
                                                 "visible_from", "n_evidence", "first_source_id"]}
                             for l in sorted(links.values(), key=lambda l: (l["link_id"], l["level"]))])
    write("events.csv", [{k: e[k] for k in ["event_id", "subject", "relation", "channel", "event_date",
                                             "public_date", "source_id"]} for e in events])
    write("lead_times.csv", lead_rows)
    write("map_value.csv", observers + [{"observer": "map value (B minus A), days",
                                         "first_event": "", "public_date": "", "lead_days": map_value,
                                         "first_connected_any": "", "first_connected_any_lead": ""}])
    return {"t_stop": t_stop, "t_warn": t_warn, "needed": needed, "links": links, "events": events,
            "lead_rows": lead_rows, "observers": observers, "map_value": map_value,
            "map_value_generic": map_value_generic, "isolated_spikes": isolated}


def write(name: str, rows: list[dict]) -> None:
    RESULTS.mkdir(exist_ok=True)
    with open(RESULTS / name, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown(res: dict) -> str:
    o = res["observers"]
    lines = [
        "## Result",
        "",
        f"- First production stop (t_stop): **{res['t_stop']}**. First public warning of stops: {res['t_warn']}.",
        f"- Needed lead time (time to recover minus time to survive): {res['needed'][0]} to {res['needed'][-1]} days.",
        f"- **Map value: {res['map_value']} days.** Observer B (full map) could act on {o[2]['first_event']} "
        f"({o[2]['public_date']}), {o[2]['lead_days']} days before the first stop. Observer A (public map, "
        f"named links) had no connected signal early enough to act"
        + (f"; its first connected signal of any kind was {o[0]['first_connected_any']}, "
           f"{o[0]['first_connected_any_lead']} days before the stop." if o[0]['first_connected_any'] else "."),
        f"- Variant with generic links (\"used in the automotive industry\"): map value {res['map_value_generic']} days.",
        "",
        "## Signals before the first stop",
        "",
        "| Event | Channel | Public date | Lead time (days) | Actionable share | Connected: A | A generic | B |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in res["lead_rows"]:
        lines.append(f"| {r['event_id']} {r['relation']} ({r['subject']}) | {r['channel']} | {r['public_date']} | "
                     f"{r['lead_days']} | {r['actionable_share']} | {'yes' if r['connected_A'] else 'no'} | "
                     f"{'yes' if r['connected_A_generic'] else 'no'} | {'yes' if r['connected_B'] else 'no'} |")
    lines += ["", "## When the map became public", "", "| Link | Level | Visible from | Rows | First source |",
              "|---|---|---|---|---|"]
    for l in sorted(res["links"].values(), key=lambda l: (l["link_id"], l["level"])):
        lines.append(f"| {l['link_id']} {l['subject']} {l['relation']} {l['object']} | {l['level']} | "
                     f"{l['visible_from']} | {l['n_evidence']} | {l['first_source_id']} |")
    lines += ["", "## Attention", "",
              f"Page views of the Wikipedia article \"Nexperia\". An attention signal needs {SUSTAINED_DAYS} or more "
              "spike days in a row (views at least 5 times the 28-day median and at least 500). This rule was "
              "added after seeing the data. "
              f"Single spike days before the first run: {', '.join(res['isolated_spikes']) or 'none'}. "
              "They are not followed by any event in this case, so they count as false alarms of attention data."]
    return "\n".join(lines)


if __name__ == "__main__":
    res = run()
    print(markdown(res))
