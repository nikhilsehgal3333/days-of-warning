"""Build the site and the result block of README.md from the generated results.
No number is typed by hand.

site/index.html          overview of all cases
site/<case>/index.html   one page per case (text from case/<case>/narrative.md)

    py -3.12 site/build.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from htw import analysis, compare, falsealarm, figures, paths  # noqa: E402

REPO = "https://github.com/nikhilsehgal3333/days-of-warning"
NOTE = ("Independent study by Nikhil Sehgal, using public data only. Not a product of Daimler Truck, the "
        "University of St.Gallen, BMW Group, Ulm University or Catena-X. Proof of concept. Illustrative "
        "backtests of single cases, not forecasts.")
CSS = """:root { --ink:#1f2328; --muted:#57606a; --line:#d0d7de; --bg:#ffffff; --soft:#f6f8fa; --accent:#0b5cad; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 Arial, Helvetica, sans-serif; }
main { max-width:960px; margin:0 auto; padding:24px 16px 64px; }
h1 { font-size:1.9rem; line-height:1.2; margin:0.2em 0 0.3em; }
h2 { font-size:1.3rem; margin:2em 0 0.5em; border-bottom:1px solid var(--line); padding-bottom:4px; }
.lede { font-size:1.15rem; }
.note { background:var(--soft); border-left:4px solid var(--accent); padding:10px 14px; color:var(--muted); }
.headline { background:var(--soft); border:1px solid var(--line); border-radius:8px; padding:8px 20px; }
.cards { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:16px; }
.card { border:1px solid var(--line); border-radius:8px; padding:12px 16px; }
figure { margin:1.2em 0; } figure svg { width:100%; height:auto; border:1px solid var(--line); border-radius:6px; }
figcaption { color:var(--muted); font-size:0.9rem; }
.scroll { overflow-x:auto; } table { border-collapse:collapse; width:100%; font-size:0.92rem; }
th, td { border-bottom:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }
th { background:var(--soft); } a { color:var(--accent); }
code { background:var(--soft); padding:1px 4px; border-radius:4px; }"""


def esc(t) -> str:
    return html.escape(str(t), quote=False)


def md_inline(t: str) -> str:
    t = esc(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)


def section(md: str, title: str) -> str:
    m = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", md, re.S | re.M)
    return m.group(1).strip() if m else ""


def md_to_html(md: str) -> str:
    out, para, items, kind = [], [], [], None

    def flush():
        nonlocal para, items, kind
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
        if items:
            out.append(f"<{kind}>" + "".join(f"<li>{md_inline(i)}</li>" for i in items) + f"</{kind}>")
        para, items, kind = [], [], None

    for line in md.splitlines():
        s = line.strip()
        if not s:
            flush()
            continue
        m = re.match(r"^(-|\d+\.)\s+(.*)", s)
        if m:
            if para:
                flush()
            kind = kind or ("ol" if m.group(1)[0].isdigit() else "ul")
            items.append(m.group(2))
        elif items:
            items[-1] += " " + s
        else:
            para.append(s)
    flush()
    return "\n".join(out)


def table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h, _ in cols)
    body = "".join("<tr>" + "".join(f"<td>{esc(r[k])}</td>" for _, k in cols) + "</tr>" for r in rows)
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def headline(res: dict) -> list[str]:
    o = res["observers"]
    b = (f"Observer B (full map) could act on event {o[2]['first_event']}, public on {o[2]['public_date']}, "
         f"{o[2]['lead_days']} days before the first production stop on {res['t_stop']}."
         if o[2]["first_event"] else f"Observer B (full map) had no actionable signal before the first stop on {res['t_stop']}.")
    if o[0]["first_event"]:
        a = (f"Observer A (public map, named links) could act on event {o[0]['first_event']}, "
             f"{o[0]['lead_days']} days before the stop.")
    else:
        a = ("Observer A (public map, named links) had no connected signal early enough to act."
             + (f" Its first connected signal of any kind was {o[0]['first_connected_any']}, "
                f"{o[0]['first_connected_any_lead']} days before the stop." if o[0]["first_connected_any"] else ""))
    return [f"Map value: **{res['map_value']} days**.", b, a,
            f"Needed lead time in the grid: {res['needed'][0]} to {res['needed'][-1]} days.",
            f"Variant with generic links: map value {res['map_value_generic']} days."]


def page(res: dict, method_md: str) -> str:
    case, cfg = res["case"], res["config"]
    narrative = (paths.case_dir(case) / "narrative.md").read_text(encoding="utf-8")
    sdir = paths.site_dir(case)
    svg = {n: (sdir / f"{n}.svg").read_text(encoding="utf-8") for n in ("timeline", "timeline_zoom", "map")}
    lead = [dict(r, connected_A="yes" if r["connected_A"] else "no",
                 connected_B="yes" if r["connected_B"] else "no") for r in res["lead_rows"]]
    links = [dict(l, link=f"{l['subject']} {l['relation']} {l['object']}")
             for l in sorted(res["links"].values(), key=lambda l: (l["link_id"], l["level"]))]
    hl = "".join(f"<li>{md_inline(h)}</li>" for h in headline(res))
    fa = falsealarm.run(case)
    fa_html = ""
    if fa:
        rows = [dict(r, outcome=r["outcome"] + (" (borderline case recorded)"
                     if r["borderline"] and r["outcome"] != "stop found" else "")) for r in fa["rows"]]
        fa_html = ("<h2>False-alarm test</h2>" + md_to_html(
            f"Of {fa['n']} Chinese export-control measures on materials (July 2023 to October 2025), "
            f"**{fa['stops']}** was followed by a production stop within 6 months. With the borderline case "
            f"counted: {fa['stops'] + fa['borderline']} of {fa['n']}. No stop found means that a logged search "
            "found no public report; it does not prove that no stop happened.")
            + table(rows, [("Measure", "measure_id"), ("Material", "material"), ("Announced", "announced"),
                           ("Outcome", "outcome")]))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Days of warning: {esc(cfg['short'])}</title>
<meta name="description" content="{esc(cfg['question'])}">
<style>{CSS}</style></head>
<body><main>
<p class="note">{esc(NOTE)} <a href="../index.html">All cases</a>.</p>
<h1>{esc(cfg['title'])}</h1>
<p class="lede">{esc(cfg['question'])}</p>
<h2>Result</h2>
<div class="headline"><ul>{hl}</ul></div>
<figure>{svg['timeline']}<figcaption>Public signals by channel. The dashed lines mark the latest start of action for the shortest and longest need.</figcaption></figure>
<figure>{svg['timeline_zoom']}<figcaption>The crisis weeks in detail.</figcaption></figure>
<figure>{svg['map']}<figcaption>When each link of the map was first named in a public source.</figcaption></figure>
<h2>The case</h2>{md_to_html(section(narrative, 'The case'))}
<h2>The question</h2>{md_to_html(section(narrative, 'The question'))}
<h2>Signals before the first stop</h2>
{table(lead, [('Event', 'event_id'), ('Type', 'relation'), ('Firm or node', 'subject'), ('Channel', 'channel'), ('Public date', 'public_date'), ('Lead time (days)', 'lead_days'), ('Actionable share', 'actionable_share'), ('Connected: A', 'connected_A'), ('Connected: B', 'connected_B')])}
<h2>When the map became public</h2>
{table(links, [('Link', 'link_id'), ('Relation', 'link'), ('Level', 'level'), ('Visible from', 'visible_from'), ('First source', 'first_source_id')])}
<h2>Sensitivity to the window</h2>
{table(res['sensitivity'], [('Window (days before the stop)', 'lookback_days'), ('Map value (days)', 'map_value'), ('First event, B', 'first_event_B'), ('First event, A', 'first_event_A')])}
{fa_html}
<h2>Method</h2>{md_to_html(method_md)}
<h2>Reading of the author</h2>{md_to_html(section(narrative, 'Reading of the author'))}
<h2>Limits</h2>{md_to_html(section(narrative, 'Limits'))}
<h2>Data and code</h2>
<p>Code, inputs and all generated tables: <a href="{REPO}">{REPO}</a>. Every number on this page is generated by the scripts. Licence: MIT.</p>
</main></body></html>
"""


def md_table_to_html(md: str) -> str:
    out, rows = [], []
    for line in md.splitlines() + [""]:
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(set(c) <= set("-") for c in cells):
                rows.append(cells)
            continue
        if rows:
            head = "".join(f"<th>{md_inline(c)}</th>" for c in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{md_inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
            out.append(f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
            rows = []
        if line.strip():
            out.append("<p>" + md_inline(line) + "</p>")
    return "\n".join(out)


def overview(results: list[dict], cmp_md: str = "", works_md: str = "") -> str:
    cards = []
    for res in results:
        cfg = res["config"]
        cards.append(f'<div class="card"><h3><a href="{res["case"]}/index.html">{esc(cfg["title"])}</a></h3>'
                     f'<p>{esc(cfg["question"])}</p><p>First stop: {esc(res["t_stop"])}. '
                     f'<strong>Map value: {res["map_value"]} days.</strong> Generic variant: '
                     f'{res["map_value_generic"]} days.</p></div>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Days of warning</title>
<meta name="description" content="How many days of warning is a hidden-tier supply chain map worth? Independent public-data backtests of real disruptions.">
<style>{CSS}</style></head>
<body><main>
<p class="note">{esc(NOTE)}</p>
<h1>Days of warning</h1>
<p class="lede">How many days of warning is a hidden-tier supply chain map worth? Each case compares an observer who knows only the public map with an observer who knows the full map.</p>
<h2>Cases</h2>
<div class="cards">{''.join(cards)}</div>
<h2>What works and what does not</h2>
{md_to_html(works_md)}
<h2>Comparison</h2>
{md_table_to_html(cmp_md)}
<h2>Data and code</h2>
<p><a href="{REPO}">{REPO}</a>. Every number on this site is generated by the scripts. Licence: MIT.</p>
</main></body></html>
"""


def readme_block(results: list[dict]) -> str:
    lines = []
    for res in results:
        lines.append(f"**{res['config']['title']}**")
        lines.append("")
        lines += [f"- {h}" for h in headline(res)]
        lines.append("")
    lines.append("Full tables: `results/<case>/RESULTS.md`. Figures: `site/<case>/`.")
    return "\n".join(lines)


def works_text(cmp: dict) -> str:
    rows = {r["case"]: r for r in cmp["rows"]}
    n, r = rows.get("nexperia"), rows.get("rare-earths")
    fa = cmp.get("false_alarms")
    lines = []
    if n and r:
        lines.append(f"- **Works: the map value.** It was {n['map_value']} days for one hidden firm and {r['map_value']} "
                     "days for a country-level material supply, and it stayed the same across the 12-, 24- and "
                     "36-month windows. In both cases the early signal was a state measure.")
        lines.append(f"- **Does not work: generic public knowledge.** The generic variant gives a map value of "
                     f"{n['map_value_generic']} and {r['map_value_generic']} days: the industry-level dependency was public, "
                     f"but the named public map first reached the hidden node only on {n['named_public_map_connects'] or 'no date'} "
                     f"and {r['named_public_map_connects'] or 'no date'}, after the first stop.")
        lines.append(f"- **Mixed: the trigger.** It left {n['trigger_lead']} days in the Nexperia case (actionable share "
                     f"{n['trigger_actionable_share']}) and {r['trigger_lead']} days in the rare-earth case (share "
                     f"{r['trigger_actionable_share']}).")
    if fa:
        lines.append(f"- **Does not work: acting on every warning.** Only {fa['stops']} of {fa['n']} Chinese export controls "
                     f"on materials from 2023 to 2025 was followed by a vehicle production stop "
                     f"({fa['stops'] + fa['borderline']} of {fa['n']} with a borderline case).")
    if cmp["predictions"]:
        held = ", ".join(f"{p['id']} {p['held']}" for p in cmp["predictions"])
        lines.append(f"- **Pre-registered predictions of case 2:** {held}.")
    return "\n".join(lines)


def main() -> None:
    results = []
    for case in paths.cases():
        res = analysis.run(case)
        figures.run(res)
        results.append(res)
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    method = section(readme, "Method, in short")
    for res in results:
        (paths.site_dir(res["case"]) / "index.html").write_text(page(res, method), encoding="utf-8")
    fas = {r["case"]: falsealarm.run(r["case"]) for r in results}
    cmp = compare.run(results, {k: v for k, v in fas.items() if v})
    cmp_md = compare.markdown(cmp)
    works = works_text(cmp)
    (ROOT / "site" / "index.html").write_text(overview(results, cmp_md, works), encoding="utf-8")
    block = ("<!-- RESULTS:START -->\n" + readme_block(results) + "\n\n### What works and what does not\n\n"
             + works + "\n\n### Comparison\n\n" + cmp_md + "\n<!-- RESULTS:END -->")
    readme = re.sub(r"<!-- RESULTS:START -->.*?<!-- RESULTS:END -->", lambda _: block, readme, flags=re.S)
    readme_path.write_text(readme, encoding="utf-8")
    print("Wrote site/index.html, " + ", ".join(f"site/{r['case']}/index.html" for r in results)
          + " and the result block of README.md")


if __name__ == "__main__":
    main()
