"""Compare the cases and check the pre-registered predictions and criteria of case 2.

Writes results/comparison.csv and returns the text for the overview and the README.
"""
from __future__ import annotations

import csv
from datetime import date

from . import paths
from .analysis import connected


def first_named_connection(res: dict, target: str) -> str:
    """The first date on which the named public map connects the observer to `target`."""
    named = [l for l in res["links"].values() if l["level"] == "named"]
    for day in sorted({l["visible_from"] for l in named}):
        if connected(target, named, day, res["config"].get("observer", "VM")):
            return day
    return ""


def summary(res: dict) -> dict:
    cfg = res["config"]
    trig = next((e for e in res["events"] if e["event_id"] == cfg.get("trigger")), None)
    hidden = trig["subject"] if trig else ""
    att = [e for e in res["events"] if e["relation"] == "attention"]
    lags = {e["note"].split(":")[0]: (date.fromisoformat(e["public_date"]) - date.fromisoformat(trig["public_date"])).days
            for e in att} if trig else {}
    spread = max(s["map_value"] for s in res["sensitivity"]) - min(s["map_value"] for s in res["sensitivity"])
    trig_row = next((r for r in res["lead_rows"] if trig and r["event_id"] == trig["event_id"]), None)
    return {
        "case": res["case"], "title": cfg["title"], "node_kind": cfg.get("node_kind", ""),
        "t_stop": res["t_stop"], "map_value": res["map_value"], "map_value_generic": res["map_value_generic"],
        "window_spread": spread, "first_signal_B": res["observers"][2]["first_event"],
        "lead_B": res["observers"][2]["lead_days"],
        "named_public_map_connects": first_named_connection(res, hidden) if hidden else "",
        "trigger": cfg.get("trigger", ""), "trigger_lead": trig_row["lead_days"] if trig_row else "",
        "trigger_actionable_share": trig_row["actionable_share"] if trig_row else "",
        "attention_lag_days": "; ".join(f"{k}: {v:+d}" for k, v in lags.items()) or "no attention run",
    }


def predictions(res: dict, s: dict, fa: dict | None) -> list[dict]:
    """Case 2 only. Thresholds stated here were set at analysis time and are logged in
    PREREGISTRATION.md; the results do not lie near them."""
    trig_day = next(e["public_date"] for e in res["events"] if e["event_id"] == res["config"]["trigger"])
    generic_before = all(l["visible_from"] < trig_day for l in res["links"].values() if l["level"] == "generic")
    named_paths = s["named_public_map_connects"]
    p1 = generic_before and (named_paths == "" or named_paths >= "2025-05-01")
    p2 = s["lead_B"] >= 90
    p3 = fa is not None and fa["stops"] == 1
    lag = [int(x.split(":")[1]) for x in s["attention_lag_days"].split("; ") if ":" in x]
    p4_any = any(0 <= v <= 7 for v in lag)
    p4_all = bool(lag) and all(0 <= v <= 7 for v in lag) and len(lag) == len(res["config"]["signals"]["pageviews"])
    return [
        {"id": "P1", "text": "Generic links public years before the trigger; named links only from May or June 2025",
         "held": "yes" if p1 else "no"},
        {"id": "P2", "text": "Observer B's first actionable connected signal comes many months (90 days or more) before the first stop",
         "held": "yes" if p2 else "no"},
        {"id": "P3", "text": "Exactly 1 of the 7 class measures was followed by a stop within 6 months",
         "held": "yes" if p3 else "no"},
        {"id": "P4", "text": "Public attention reacted within 7 days of the trigger",
         "held": "yes" if p4_all else ("partly" if p4_any else "no")},
    ]


def criteria(s: dict, fa: dict | None) -> list[dict]:
    q1 = s["window_spread"] <= 180
    q2 = fa is not None and fa["stops"] / fa["n"] <= 2 / 7
    q3 = isinstance(s["trigger_actionable_share"], float) and s["trigger_actionable_share"] > 0
    return [
        {"id": "Q1", "text": "Map value stable within 180 days across the 12-, 24- and 36-month windows",
         "result": "works" if q1 else "window-dependent"},
        {"id": "Q2", "text": "Class precision of 2 in 7 or lower",
         "result": ("this kind of warning alone does not justify action" if q2 else "precision above 2 in 7")
         if fa else "not tested"},
        {"id": "Q3", "text": "The trigger left time to act (actionable share above 0)",
         "result": "works" if q3 else "does not work"},
    ]


def run(results: list[dict], false_alarms: dict) -> dict:
    rows = [summary(r) for r in results]
    with open(paths.ROOT / "results" / "comparison.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    out = {"rows": rows, "predictions": [], "criteria": []}
    for res, s in zip(results, rows):
        if res["case"] == "rare-earths":
            fa = false_alarms.get(res["case"])
            out["predictions"] = predictions(res, s, fa)
            out["criteria"] = criteria(s, fa)
            out["false_alarms"] = fa
    return out


def markdown(cmp: dict) -> str:
    lines = ["| | " + " | ".join(r["title"] for r in cmp["rows"]) + " |",
             "|---|" + "---|" * len(cmp["rows"])]
    fields = [("Hidden node", "node_kind"), ("First stop", "t_stop"), ("Map value (days)", "map_value"),
              ("Map value, generic variant (days)", "map_value_generic"),
              ("First signal observer B could act on", "first_signal_B"),
              ("Its lead time (days)", "lead_B"),
              ("Named public map first connects the hidden node", "named_public_map_connects"),
              ("Lead time of the trigger (days)", "trigger_lead"),
              ("Trigger actionable share", "trigger_actionable_share"),
              ("Attention lag after the trigger (days)", "attention_lag_days"),
              ("Spread of the map value across windows (days)", "window_spread")]
    for label, key in fields:
        lines.append(f"| {label} | " + " | ".join(str(r[key] or "never before the stop") if key == "named_public_map_connects"
                                                   else str(r[key]) for r in cmp["rows"]) + " |")
    if cmp["predictions"]:
        lines += ["", "**Pre-registered predictions (case 2)**", "", "| | Prediction | Held |", "|---|---|---|"]
        lines += [f"| {p['id']} | {p['text']} | {p['held']} |" for p in cmp["predictions"]]
        lines += ["", "**Pre-registered criteria (case 2)**", "", "| | Criterion | Result |", "|---|---|---|"]
        lines += [f"| {c['id']} | {c['text']} | {c['result']} |" for c in cmp["criteria"]]
    return "\n".join(lines)
