"""Visibility, signals, lead times, the time-to-act grid, connection and the map value, for one case.

Rows that share an id prefix (E04a, E04b) describe one event or link. The event or link takes the
earliest public date of its checked rows. Settings come from case/<id>/config.json:
"observer", "lookback_days" and "sensitivity_lookback_days".

    py -3.12 -m htw.analysis [--case <id>]
"""
from __future__ import annotations

import csv
import re
from collections import deque
from datetime import date, timedelta

from . import paths

SUSTAINED_DAYS = 3  # added after seeing the case-1 data: single spike days in 2024 were noise


def d(text: str) -> date:
    return date.fromisoformat(text)


def group_id(evidence_id: str) -> str:
    return re.sub(r"[a-z]+$", "", evidence_id)


def load_checked(case: str) -> list[dict]:
    check = paths.results_dir(case) / "evidence_check.csv"
    ok = {r["evidence_id"] for r in csv.DictReader(open(check, encoding="utf-8")) if r["quote_found"] == "True"}
    return [r for r in csv.DictReader(open(paths.case_dir(case) / "evidence.csv", encoding="utf-8"))
            if r["evidence_id"] in ok]


def grid(case: str) -> list[tuple[int, int]]:
    a = {r["name"]: [int(v) for v in r["values"].split(";")]
         for r in csv.DictReader(open(paths.case_dir(case) / "assumptions.csv", encoding="utf-8"))}
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


def attention_events(case: str, cfg: dict) -> tuple[list[dict], dict]:
    """One attention event per configured article: the first day of SUSTAINED_DAYS or more spike days
    in a row (k=5). Also return the single spike days before that run, per article."""
    events, isolated = [], {}
    for i, spec in enumerate(cfg.get("signals", {}).get("pageviews", [])):
        path = paths.results_dir(case) / f"attention_{spec['source_id']}.csv"
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        first = None
        for k in range(len(rows)):
            window = rows[k:k + SUSTAINED_DAYS]
            if len(window) == SUSTAINED_DAYS and all(w["spike_k5"] == "True" for w in window):
                first = rows[k]
                break
        spike_days = [r["date"] for r in rows if r["spike_k5"] == "True"]
        isolated[spec["article"]] = [s for s in spike_days if first is None or s < first["date"]]
        if first:
            events.append({"event_id": f"A{i + 1:02d}", "subject": spec["subject"], "relation": "attention",
                           "channel": "attention", "event_date": first["date"], "public_date": first["date"],
                           "source_id": spec["source_id"],
                           "note": f"{spec['article']}: first of {SUSTAINED_DAYS}+ spike days in a row (k=5), "
                                   f"{first['views']} views"})
    return events, isolated


def connected(target: str, links: list[dict], on: str | None, observer: str = "VM") -> bool:
    usable = [l for l in links if on is None or l["visible_from"] <= on]
    seen, queue = {observer}, deque([observer])
    while queue:
        node = queue.popleft()
        if node == target:
            return True
        for l in usable:
            if l["object"] == node and l["subject"] not in seen:
                seen.add(l["subject"])
                queue.append(l["subject"])
    return False


def lead_table(events: list[dict], t_stop: str, lookback: int, cells: list[tuple[int, int]],
               named: list[dict], every: list[dict], observer: str) -> list[dict]:
    earliest = (d(t_stop) - timedelta(days=lookback)).isoformat()
    rows = []
    for e in events:
        if e["public_date"] >= t_stop or e["public_date"] < earliest:
            continue
        if e["relation"] == "response":
            continue  # a firm's own action is reported, but it is not a signal
        lead = (d(t_stop) - d(e["public_date"])).days
        share = sum(lead >= ttr - tts for tts, ttr in cells) / len(cells)
        rows.append({
            "event_id": e["event_id"], "subject": e["subject"], "relation": e["relation"],
            "channel": e["channel"], "public_date": e["public_date"], "lead_days": lead,
            "actionable_share": round(share, 3),
            "connected_A": connected(e["subject"], named, e["public_date"], observer),
            "connected_A_generic": connected(e["subject"], every, e["public_date"], observer),
            "connected_B": connected(e["subject"], named, None, observer),
        })
    return rows


def observer_summary(lead_rows: list[dict]) -> list[dict]:
    out = []
    for name, col in [("A (public map, named links)", "connected_A"),
                      ("A, variant with generic links", "connected_A_generic"),
                      ("B (full map)", "connected_B")]:
        first = next((r for r in lead_rows if r[col] and r["actionable_share"] > 0), None)
        first_any = next((r for r in lead_rows if r[col]), None)
        out.append({"observer": name, "first_event": first["event_id"] if first else "",
                    "public_date": first["public_date"] if first else "",
                    "lead_days": first["lead_days"] if first else 0,
                    "first_connected_any": first_any["event_id"] if first_any else "",
                    "first_connected_any_lead": first_any["lead_days"] if first_any else 0})
    return out


def run(case: str) -> dict:
    cfg = paths.config(case)
    observer = cfg.get("observer", "VM")
    rows = load_checked(case)
    links = links_of(rows)
    named = [l for l in links.values() if l["level"] == "named"]
    every = list(links.values())
    events = events_of(rows)
    att, isolated = attention_events(case, cfg)
    events = sorted(events + att, key=lambda e: e["public_date"])
    stops = [e for e in events if e["relation"] == "production_stop"]
    warns = [e for e in events if e["relation"] == "warning"]
    t_stop = min(e["public_date"] for e in stops)
    t_warn = min(e["public_date"] for e in warns) if warns else ""
    cells = grid(case)
    needed = sorted({ttr - tts for tts, ttr in cells})
    lookback = cfg.get("lookback_days", 730)
    lead_rows = lead_table(events, t_stop, lookback, cells, named, every, observer)
    observers = observer_summary(lead_rows)
    map_value = observers[2]["lead_days"] - observers[0]["lead_days"]
    map_value_generic = observers[2]["lead_days"] - observers[1]["lead_days"]
    sensitivity = []
    for lb in cfg.get("sensitivity_lookback_days", [lookback]):
        o = observer_summary(lead_table(events, t_stop, lb, cells, named, every, observer))
        sensitivity.append({"lookback_days": lb, "map_value": o[2]["lead_days"] - o[0]["lead_days"],
                            "first_event_B": o[2]["first_event"], "lead_B": o[2]["lead_days"],
                            "first_event_A": o[0]["first_event"], "lead_A": o[0]["lead_days"]})
    out = paths.results_dir(case)
    write(out / "visibility.csv", [{k: l[k] for k in ["link_id", "level", "subject", "relation", "object",
                                                       "visible_from", "n_evidence", "first_source_id"]}
                                   for l in sorted(links.values(), key=lambda l: (l["link_id"], l["level"]))])
    write(out / "events.csv", [{k: e[k] for k in ["event_id", "subject", "relation", "channel", "event_date",
                                                   "public_date", "source_id"]} for e in events])
    write(out / "lead_times.csv", lead_rows)
    write(out / "map_value.csv", observers + [{"observer": "map value (B minus A), days",
                                               "first_event": "", "public_date": "", "lead_days": map_value,
                                               "first_connected_any": "", "first_connected_any_lead": ""}])
    write(out / "map_value_sensitivity.csv", sensitivity)
    return {"case": case, "config": cfg, "t_stop": t_stop, "t_warn": t_warn, "needed": needed,
            "links": links, "events": events, "lead_rows": lead_rows, "observers": observers,
            "map_value": map_value, "map_value_generic": map_value_generic, "isolated_spikes": isolated,
            "lookback": lookback, "sensitivity": sensitivity}


def write(path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown(res: dict) -> str:
    o = res["observers"]
    lines = [
        "## Result",
        "",
        f"- First production stop (t_stop): **{res['t_stop']}**. First public warning of stops: {res['t_warn'] or 'none'}.",
        f"- Needed lead time (time to recover minus time to survive): {res['needed'][0]} to {res['needed'][-1]} days.",
        f"- **Map value: {res['map_value']} days.** Observer B (full map) could act on {o[2]['first_event'] or 'no signal'}"
        + (f" ({o[2]['public_date']}), {o[2]['lead_days']} days before the first stop." if o[2]['first_event'] else ".")
        + (f" Observer A (public map, named links) could act on {o[0]['first_event']} ({o[0]['public_date']}), "
           f"{o[0]['lead_days']} days before the stop." if o[0]['first_event'] else
           " Observer A (public map, named links) had no connected signal early enough to act"
           + (f"; its first connected signal of any kind was {o[0]['first_connected_any']}, "
              f"{o[0]['first_connected_any_lead']} days before the stop." if o[0]['first_connected_any'] else ".")),
        f"- Variant with generic links: map value {res['map_value_generic']} days.",
        f"- Signals count from {res['lookback']} days before the first stop. Map value with other windows: "
        + "; ".join(f"{s['lookback_days']} days: {s['map_value']}" for s in res["sensitivity"]) + ".",
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
              f"Daily Wikipedia page views (official Wikimedia statistics, an attention proxy). An attention "
              f"signal needs {SUSTAINED_DAYS} or more spike days in a row (views at least 5 times the 28-day "
              "median and at least 500). This rule was added after seeing the case-1 data."]
    for article, days in res["isolated_spikes"].items():
        lines.append(f"- \"{article}\": single spike days before the first run: {', '.join(days) or 'none'}.")
    return "\n".join(lines)


if __name__ == "__main__":
    chosen, _ = paths.selected()
    for case in chosen:
        print(markdown(run(case)))
