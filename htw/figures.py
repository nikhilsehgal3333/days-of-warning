"""Draw the figures from the results. Standard library only.

site/timeline.svg       the full window, 2024-11-01 to 2025-11-30
site/timeline_zoom.svg  the crisis weeks, 2025-09-25 to 2025-11-05
site/map.svg            when each link of the map became public
"""
from __future__ import annotations

import csv
import html
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
SITE = ROOT / "site"
FULL = (date(2024, 11, 1), date(2025, 11, 30))
ZOOM = (date(2025, 9, 25), date(2025, 11, 5))
CHANNELS = ["regulatory", "legal", "trade", "association", "operational", "attention"]
INK, MUTED, GRID, ACCENT, STOP = "#1f2328", "#57606a", "#d0d7de", "#0b5cad", "#b42318"


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def timeline(res: dict, start: date, end: date, zoom: bool) -> str:
    W, left, right, top = 1000, 130, 30, 40
    row_h, chart_h = 40, 80
    width = W - left - right
    rows_y = {c: top + 40 + i * row_h for i, c in enumerate(CHANNELS)}
    chart_top = top + 40 + len(CHANNELS) * row_h + 10
    H = chart_top + chart_h + 50

    def x(day: date) -> float:
        return left + (day - start).days / (end - start).days * width

    t_stop = date.fromisoformat(res["t_stop"])
    title = ("The crisis weeks: public signals before the first stop" if zoom
             else "Public signals before the first production stop, Nexperia 2025")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
           f'font-family="Arial, sans-serif" font-size="13">', f"<title>{esc(title)}</title>",
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    if zoom:
        ticks = [start + timedelta(days=i) for i in range((end - start).days + 1)
                 if (start + timedelta(days=i)).weekday() == 0]
        fmt = "%d %b"
    else:
        ticks = [date(2024 + (10 + m) // 12, (10 + m) % 12 + 1, 1) for m in range(13)]
        fmt = "%b %y"
    for day in ticks:
        out.append(f'<line x1="{x(day):.1f}" y1="{top + 15}" x2="{x(day):.1f}" y2="{chart_top + chart_h}" stroke="{GRID}"/>')
        out.append(f'<text x="{x(day) + 3:.1f}" y="{top + 10}" fill="{MUTED}" font-size="12">{day.strftime(fmt)}</text>')
    if not zoom:
        lo, hi = res["needed"][0], res["needed"][-1]
        for days in (lo, hi):
            xv = x(t_stop - timedelta(days=days))
            out.append(f'<line x1="{xv:.1f}" y1="{top + 20}" x2="{xv:.1f}" y2="{chart_top + chart_h}" '
                       f'stroke="{ACCENT}" stroke-dasharray="5 4"/>')
            out.append(f'<text x="{xv - 4:.1f}" y="{top + 30}" fill="{ACCENT}" font-size="12" '
                       f'text-anchor="end">act by: {days} days before</text>')
        z0, z1 = x(ZOOM[0]), x(min(ZOOM[1], end))
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
        in_zoom_window = ZOOM[0] <= day <= ZOOM[1]
        if not zoom and in_zoom_window:
            continue  # labelled in the zoom figure
        px, slot = last.get(e["channel"], (-1e9, 1))
        slot = -slot if x(day) - px < 40 else -1
        last[e["channel"]] = (x(day), slot)
        ly = y - 10 if slot < 0 else y + 20
        out.append(f'<text x="{x(day):.1f}" y="{ly}" fill="{MUTED}" font-size="11" text-anchor="middle">'
                   f'{esc(e["event_id"])}</text>')
    views = [r for r in csv.DictReader(open(RESULTS / "attention.csv", encoding="utf-8"))
             if start <= date.fromisoformat(r["date"]) <= end]
    vmax = max(int(r["views"]) for r in views)
    pts = " ".join(f'{x(date.fromisoformat(r["date"])):.1f},{chart_top + chart_h - int(r["views"]) / vmax * chart_h:.1f}'
                   for r in views)
    out.append(f'<polyline points="{pts}" fill="none" stroke="{MUTED}" stroke-width="1.2"/>')
    out.append(f'<text x="{left - 10}" y="{chart_top + chart_h / 2:.0f}" fill="{INK}" text-anchor="end">page views</text>')
    note = ("Dots: public date of each signal. Grey line: daily Wikipedia views of \"Nexperia\" "
            f"(max {vmax:,}).")
    out.append(f'<text x="{left}" y="{H - 28}" fill="{MUTED}" font-size="12">{esc(note)}</text>')
    if not zoom:
        out.append(f'<text x="{left}" y="{H - 12}" fill="{MUTED}" font-size="12">Dashed lines: latest start of '
                   f'action. Shaded: the crisis weeks, shown in the second figure.</text>')
    out.append("</svg>")
    return "\n".join(out)


def network_map(res: dict) -> str:
    W, H = 1000, 330
    names = {"VM": "Vehicle makers", "T1": "Tier-1 module suppliers", "NEX": "Nexperia (NL)",
             "NEXCN": "Nexperia China (assembly)", "WT": "Wingtech (owner, CN)"}
    pos = {"VM": (90, 160), "T1": (350, 160), "NEX": (610, 160), "NEXCN": (880, 70), "WT": (880, 250)}
    bw, bh = 160, 46
    named = {(l["subject"], l["object"]): l for l in res["links"].values() if l["level"] == "named"}
    generic = {(l["subject"], l["object"]): l for l in res["links"].values() if l["level"] == "generic"}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
           f'font-family="Arial, sans-serif" font-size="13">',
           "<title>When each link of the map became public</title>",
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
    for (sub, obj), l in named.items():
        (x1, y1), (x2, y2) = pos[sub], pos[obj]
        colour = ACCENT if l["visible_from"] < "2024-12-02" else STOP
        out.append(f'<line x1="{x1 - bw / 2:.0f}" y1="{y1}" x2="{x2 + bw / 2:.0f}" y2="{y2}" stroke="{colour}" '
                   f'stroke-width="2.5"/>')
        mx, my = (x1 - bw / 2 + x2 + bw / 2) / 2, (y1 + y2) / 2
        dx = -38 if y1 != y2 else 0  # move labels of slanted links away from the line
        out.append(f'<text x="{mx + dx:.0f}" y="{my - 22:.0f}" fill="{colour}" text-anchor="middle" font-size="12">named</text>')
        out.append(f'<text x="{mx + dx:.0f}" y="{my - 8:.0f}" fill="{colour}" text-anchor="middle" font-size="12">'
                   f'{esc(l["visible_from"])}</text>')
        if (sub, obj) in generic:
            out.append(f'<text x="{mx:.0f}" y="{my + 20:.0f}" fill="{MUTED}" text-anchor="middle" font-size="12">generic</text>')
            out.append(f'<text x="{mx:.0f}" y="{my + 34:.0f}" fill="{MUTED}" text-anchor="middle" font-size="12">'
                       f'{esc(generic[(sub, obj)]["visible_from"])}</text>')
    for node, (cx, cy) in pos.items():
        out.append(f'<rect x="{cx - bw / 2:.0f}" y="{cy - bh / 2:.0f}" width="{bw}" height="{bh}" rx="6" '
                   f'fill="#f6f8fa" stroke="{INK}"/>')
        out.append(f'<text x="{cx}" y="{cy + 5}" fill="{INK}" text-anchor="middle">{esc(names[node])}</text>')
    out.append(f'<text x="30" y="{H - 20}" fill="{MUTED}" font-size="12">Each line joins a supplier or owner '
               f'(right) to its customer (left). Blue: public before the US listing of 2 Dec 2024. '
               f'Red: public only from Oct 2025.</text>')
    out.append("</svg>")
    return "\n".join(out)


def run(res: dict) -> None:
    SITE.mkdir(exist_ok=True)
    (SITE / "timeline.svg").write_text(timeline(res, *FULL, zoom=False), encoding="utf-8")
    (SITE / "timeline_zoom.svg").write_text(timeline(res, *ZOOM, zoom=True), encoding="utf-8")
    (SITE / "map.svg").write_text(network_map(res), encoding="utf-8")


if __name__ == "__main__":
    from .analysis import run as analyse
    run(analyse())
    print("wrote site/timeline.svg, site/timeline_zoom.svg and site/map.svg")
