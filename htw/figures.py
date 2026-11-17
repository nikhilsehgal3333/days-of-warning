"""Draw the figures of one case from its results. Standard library only.

site/<case>/timeline.svg       the full window, config "figure" -> "full"
site/<case>/timeline_zoom.svg  the crisis weeks, config "figure" -> "zoom"
site/<case>/map.svg            when each link of the map became public; layout from nodes.csv
                               (tier gives the column, order of rows gives the position in it)
"""
from __future__ import annotations

import csv
import html
from datetime import date, timedelta

from . import paths

INK, MUTED, GRID, ACCENT, STOP = "#1f2328", "#57606a", "#d0d7de", "#0b5cad", "#b42318"


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def month_starts(start: date, end: date) -> list[date]:
    out, y, m = [], start.year, start.month
    while date(y, m, 1) <= end:
        if date(y, m, 1) >= start:
            out.append(date(y, m, 1))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def timeline(res: dict, start: date, end: date, zoom: bool) -> str:
    cfg = res["config"]
    channels = cfg["figure"]["channels"]
    zoom_window = [date.fromisoformat(x) for x in cfg["figure"]["zoom"]]
    W, left, right, top = 1000, 130, 30, 40
    row_h, chart_h = 40, 80
    width = W - left - right
    rows_y = {c: top + 40 + i * row_h for i, c in enumerate(channels)}
    chart_top = top + 40 + len(channels) * row_h + 10
    H = chart_top + chart_h + 50

    def x(day: date) -> float:
        return left + (day - start).days / (end - start).days * width

    t_stop = date.fromisoformat(res["t_stop"])
    title = ("The crisis weeks: public signals before the first stop" if zoom
             else f"Public signals before the first production stop: {cfg['title']}")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
           f'font-family="Arial, sans-serif" font-size="13">', f"<title>{esc(title)}</title>",
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    if zoom:
        ticks = [start + timedelta(days=i) for i in range((end - start).days + 1)
                 if (start + timedelta(days=i)).weekday() == 0]
        fmt = "%d %b"
    else:
        ticks, fmt = month_starts(start, end), "%b %y"
    step = 3 if len(ticks) > 15 else 1  # long windows: label every third month
    for i, day in enumerate(ticks):
        out.append(f'<line x1="{x(day):.1f}" y1="{top + 15}" x2="{x(day):.1f}" y2="{chart_top + chart_h}" stroke="{GRID}"/>')
        if i % step == 0:
            out.append(f'<text x="{x(day) + 3:.1f}" y="{top + 10}" fill="{MUTED}" font-size="12">{day.strftime(fmt)}</text>')
    if not zoom:
        lo, hi = res["needed"][0], res["needed"][-1]
        for days in (lo, hi):
            xv = x(t_stop - timedelta(days=days))
            if xv < left:
                continue
            out.append(f'<line x1="{xv:.1f}" y1="{top + 20}" x2="{xv:.1f}" y2="{chart_top + chart_h}" '
                       f'stroke="{ACCENT}" stroke-dasharray="5 4"/>')
            out.append(f'<text x="{xv - 4:.1f}" y="{top + 30}" fill="{ACCENT}" font-size="12" '
                       f'text-anchor="end">act by: {days} days before</text>')
        z0, z1 = x(max(zoom_window[0], start)), x(min(zoom_window[1], end))
        out.append(f'<rect x="{z0:.1f}" y="{top + 15}" width="{z1 - z0:.1f}" height="{chart_top + chart_h - top - 15}" '
                   f'fill="{ACCENT}" fill-opacity="0.06"/>')
    xs = x(t_stop)
    out.append(f'<line x1="{xs:.1f}" y1="{top + 20}" x2="{xs:.1f}" y2="{chart_top + chart_h}" stroke="{STOP}" stroke-width="2"/>')
    out.append(f'<text x="{xs + 5:.1f}" y="{chart_top + 12}" fill="{STOP}" font-size="12">first stop</text>')
    out.append(f'<text x="{xs + 5:.1f}" y="{chart_top + 27}" fill="{STOP}" font-size="12">{res["t_stop"]}</text>')
    for c, y in rows_y.items():
        out.append(f'<text x="{left - 10}" y="{y + 4}" fill="{INK}" text-anchor="end">{esc(c)}</text>')
        out.append(f'<line x1="{left}" y1="{y}" x2="{W - right}" y2="{y}" stroke="{GRID}" stroke-dasharray="2 3"/>')
    last: dict[str, tuple[float, int]] = {}
    for e in sorted(res["events"], key=lambda e: (e["public_date"], e["event_id"])):
        day = date.fromisoformat(e["public_date"])
        if not (start <= day <= end) or e["channel"] not in rows_y:
            continue
        y = rows_y[e["channel"]]
        colour = STOP if e["relation"] == "production_stop" else INK
        out.append(f'<circle cx="{x(day):.1f}" cy="{y}" r="5" fill="{colour}"><title>{esc(e["event_id"])} '
                   f'{esc(e["relation"])}, public {esc(e["public_date"])}</title></circle>')
        if not zoom and zoom_window[0] <= day <= zoom_window[1]:
            continue  # labelled in the zoom figure
        px, slot = last.get(e["channel"], (-1e9, 1))
        slot = -slot if x(day) - px < 40 else -1
        last[e["channel"]] = (x(day), slot)
        ly = y - 10 if slot < 0 else y + 20
        out.append(f'<text x="{x(day):.1f}" y="{ly}" fill="{MUTED}" font-size="11" text-anchor="middle">'
                   f'{esc(e["event_id"])}</text>')
    pv = cfg.get("signals", {}).get("pageviews", [])
    vmax = 0
    if pv:
        views = [r for r in csv.DictReader(open(paths.results_dir(res["case"]) / f"attention_{pv[0]['source_id']}.csv",
                                                encoding="utf-8"))
                 if start <= date.fromisoformat(r["date"]) <= end]
        vmax = max(int(r["views"]) for r in views)
        pts = " ".join(f'{x(date.fromisoformat(r["date"])):.1f},{chart_top + chart_h - int(r["views"]) / vmax * chart_h:.1f}'
                       for r in views)
        out.append(f'<polyline points="{pts}" fill="none" stroke="{MUTED}" stroke-width="1.2"/>')
        out.append(f'<text x="{left - 10}" y="{chart_top + chart_h / 2:.0f}" fill="{INK}" text-anchor="end">page views</text>')
    note = "Dots: public date of each signal."
    if pv:
        note += f' Grey line: daily Wikipedia views of "{pv[0]["article"]}" (max {vmax:,}).'
    out.append(f'<text x="{left}" y="{H - 28}" fill="{MUTED}" font-size="12">{esc(note)}</text>')
    if not zoom:
        out.append(f'<text x="{left}" y="{H - 12}" fill="{MUTED}" font-size="12">Dashed lines: latest start of '
                   f'action. Shaded: the crisis weeks, shown in the second figure.</text>')
    out.append("</svg>")
    return "\n".join(out)


def network_map(res: dict) -> str:
    cfg = res["config"]
    nodes = list(csv.DictReader(open(paths.case_dir(res["case"]) / "nodes.csv", encoding="utf-8")))
    tiers = sorted({int(n["tier"]) for n in nodes})
    W, bw, bh = 1000, 160, 46
    col_x = {t: 90 + i * (W - 180) / max(1, len(tiers) - 1) for i, t in enumerate(tiers)}
    per_tier = {t: [n for n in nodes if int(n["tier"]) == t] for t in tiers}
    rows_max = max(len(v) for v in per_tier.values())
    H = 140 + rows_max * 110
    pos, names = {}, {}
    for t, members in per_tier.items():
        for j, n in enumerate(members):
            pos[n["node_id"]] = (col_x[t], H / 2 - 30 + (j - (len(members) - 1) / 2) * 180)
            names[n["node_id"]] = n.get("label") or n["name"]
    ref = cfg["map_reference"]
    named = {(l["subject"], l["object"]): l for l in res["links"].values() if l["level"] == "named"}
    generic = {(l["subject"], l["object"]): l for l in res["links"].values() if l["level"] == "generic"}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
           f'font-family="Arial, sans-serif" font-size="13">',
           "<title>When each link of the map became public</title>",
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    pairs = sorted(set(named) | set(generic))
    for sub, obj in pairs:
        if sub not in pos or obj not in pos:
            continue
        (x1, y1), (x2, y2) = pos[sub], pos[obj]
        mx, my = (x1 - bw / 2 + x2 + bw / 2) / 2, (y1 + y2) / 2
        if y1 == y2:
            lx, ly = mx, my - 22
        else:  # slanted link: label beside the supplier end, on the side away from the line
            lx, ly = x1 - bw / 2 - 72, (y1 + 30 if y1 > y2 else y1 - 44)
        if (sub, obj) in named:
            l = named[(sub, obj)]
            colour = ACCENT if l["visible_from"] < ref["date"] else STOP
            out.append(f'<line x1="{x1 - bw / 2:.0f}" y1="{y1:.0f}" x2="{x2 + bw / 2:.0f}" y2="{y2:.0f}" '
                       f'stroke="{colour}" stroke-width="2.5"/>')
            out.append(f'<text x="{lx:.0f}" y="{ly:.0f}" fill="{colour}" text-anchor="middle" font-size="12">named</text>')
            out.append(f'<text x="{lx:.0f}" y="{ly + 14:.0f}" fill="{colour}" text-anchor="middle" font-size="12">'
                       f'{esc(l["visible_from"])}</text>')
        else:
            out.append(f'<line x1="{x1 - bw / 2:.0f}" y1="{y1:.0f}" x2="{x2 + bw / 2:.0f}" y2="{y2:.0f}" '
                       f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="4 4"/>')
        if (sub, obj) in generic:
            out.append(f'<text x="{mx:.0f}" y="{my + 20:.0f}" fill="{MUTED}" text-anchor="middle" font-size="12">generic</text>')
            out.append(f'<text x="{mx:.0f}" y="{my + 34:.0f}" fill="{MUTED}" text-anchor="middle" font-size="12">'
                       f'{esc(generic[(sub, obj)]["visible_from"])}</text>')
    for node, (cx, cy) in pos.items():
        out.append(f'<rect x="{cx - bw / 2:.0f}" y="{cy - bh / 2:.0f}" width="{bw}" height="{bh}" rx="6" '
                   f'fill="#f6f8fa" stroke="{INK}"/>')
        out.append(f'<text x="{cx:.0f}" y="{cy + 5:.0f}" fill="{INK}" text-anchor="middle">{esc(names[node])}</text>')
    out.append(f'<text x="30" y="{H - 20}" fill="{MUTED}" font-size="12">Each line joins a supplier or owner '
               f'(right) to its customer (left). Blue: named in public before {esc(ref["label"])}. '
               f'Red: named only later. Dashed grey: only a generic public statement.</text>')
    out.append("</svg>")
    return "\n".join(out)


def run(res: dict) -> None:
    cfg = res["config"]
    full = [date.fromisoformat(x) for x in cfg["figure"]["full"]]
    zoom = [date.fromisoformat(x) for x in cfg["figure"]["zoom"]]
    out = paths.site_dir(res["case"])
    (out / "timeline.svg").write_text(timeline(res, *full, zoom=False), encoding="utf-8")
    (out / "timeline_zoom.svg").write_text(timeline(res, *zoom, zoom=True), encoding="utf-8")
    (out / "map.svg").write_text(network_map(res), encoding="utf-8")


if __name__ == "__main__":
    from .analysis import run as analyse
    chosen, _ = paths.selected()
    for case in chosen:
        run(analyse(case))
        print(f"[{case}] wrote site/{case}/timeline.svg, timeline_zoom.svg and map.svg")
