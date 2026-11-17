"""Build site/index.html and the result block of README.md from the generated results.
No number is typed by hand.

    py -3.12 site/build.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from htw import analysis, figures  # noqa: E402

REPO = "https://github.com/nikhilsehgal3333/days-of-warning"


def esc(t) -> str:
    return html.escape(str(t), quote=False)


def headline(res: dict) -> list[str]:
    o = res["observers"]
    a_any = (f"Its first connected signal of any kind was {o[0]['first_connected_any']}, "
             f"{o[0]['first_connected_any_lead']} days before the stop." if o[0]["first_connected_any"] else "")
    return [
        f"Map value: **{res['map_value']} days**.",
        f"Observer B (full map) could act on event {o[2]['first_event']}, public on {o[2]['public_date']}, "
        f"{o[2]['lead_days']} days before the first production stop on {res['t_stop']}.",
        f"Observer A (public map, named links) had no connected signal early enough to act. {a_any}",
        f"Needed lead time in the grid: {res['needed'][0]} to {res['needed'][-1]} days.",
        f"Generic variant (\"used in the automotive industry\" counts as a link): map value "
        f"{res['map_value_generic']} days. Public data connected the early signal to the industry, "
        "but not to any named supplier or part.",
    ]


def readme_block(res: dict) -> str:
    lines = [f"- {h}" for h in headline(res)]
    lines += ["", "| Event | Channel | Public date | Lead time (days) | Actionable share | A | B |",
              "|---|---|---|---|---|---|---|"]
    for r in res["lead_rows"]:
        lines.append(f"| {r['event_id']} {r['relation']} ({r['subject']}) | {r['channel']} | {r['public_date']} | "
                     f"{r['lead_days']} | {r['actionable_share']} | {'yes' if r['connected_A'] else 'no'} | "
                     f"{'yes' if r['connected_B'] else 'no'} |")
    lines += ["", "Full tables: [`results/RESULTS.md`](results/RESULTS.md). Figures: `site/`."]
    return "\n".join(lines)


def md_inline(t: str) -> str:
    t = esc(t)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)


def readme_section(readme: str, title: str) -> str:
    m = re.search(rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)", readme, re.S | re.M)
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
            flush(); continue
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


def page(res: dict, readme: str) -> str:
    svg = {n: (ROOT / "site" / f"{n}.svg").read_text(encoding="utf-8") for n in ("timeline", "timeline_zoom", "map")}
    lead = [dict(r, connected_A="yes" if r["connected_A"] else "no",
                 connected_B="yes" if r["connected_B"] else "no") for r in res["lead_rows"]]
    links = sorted(res["links"].values(), key=lambda l: (l["link_id"], l["level"]))
    links = [dict(l, link=f"{l['subject']} {l['relation']} {l['object']}") for l in links]
    hl = "".join(f"<li>{md_inline(h)}</li>" for h in headline(res))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Days of warning</title>
<meta name="description" content="How many days of warning was a hidden-tier supply chain map worth in the 2025 Nexperia chip disruption? An independent public-data backtest.">
<style>
:root {{ --ink:#1f2328; --muted:#57606a; --line:#d0d7de; --bg:#ffffff; --soft:#f6f8fa; --accent:#0b5cad; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.55 Arial, Helvetica, sans-serif; }}
main {{ max-width:960px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:1.9rem; line-height:1.2; margin:0.2em 0 0.3em; }}
h2 {{ font-size:1.3rem; margin:2em 0 0.5em; border-bottom:1px solid var(--line); padding-bottom:4px; }}
.lede {{ font-size:1.15rem; }}
.note {{ background:var(--soft); border-left:4px solid var(--accent); padding:10px 14px; color:var(--muted); }}
.headline {{ background:var(--soft); border:1px solid var(--line); border-radius:8px; padding:8px 20px; }}
figure {{ margin:1.2em 0; }} figure svg {{ width:100%; height:auto; border:1px solid var(--line); border-radius:6px; }}
figcaption {{ color:var(--muted); font-size:0.9rem; }}
.scroll {{ overflow-x:auto; }} table {{ border-collapse:collapse; width:100%; font-size:0.92rem; }}
th, td {{ border-bottom:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }}
th {{ background:var(--soft); }} a {{ color:var(--accent); }}
code {{ background:var(--soft); padding:1px 4px; border-radius:4px; }}
</style></head>
<body><main>
<p class="note">Independent study by Nikhil Sehgal, using public data only. Not a product of Daimler Truck, the University of St.Gallen, BMW Group, Ulm University or Catena-X. Proof of concept, version 0.1. Illustrative backtest of one case, not a forecast.</p>
<h1>Days of warning</h1>
<p class="lede">How many days of warning was a hidden-tier supply chain map worth in the 2025 Nexperia chip disruption?</p>
<h2>Result</h2>
<div class="headline"><ul>{hl}</ul></div>
<figure>{svg['timeline']}<figcaption>Public signals by channel. The dashed lines mark the latest start of action for the shortest and longest need.</figcaption></figure>
<figure>{svg['timeline_zoom']}<figcaption>The crisis weeks in detail.</figcaption></figure>
<figure>{svg['map']}<figcaption>When each link of the map was first named in a public source.</figcaption></figure>
<h2>The case</h2>{md_to_html(readme_section(readme, 'The case'))}
<h2>The question</h2>{md_to_html(readme_section(readme, 'The question'))}
<h2>Signals before the first stop</h2>
{table(lead, [('Event', 'event_id'), ('Type', 'relation'), ('Firm', 'subject'), ('Channel', 'channel'), ('Public date', 'public_date'), ('Lead time (days)', 'lead_days'), ('Actionable share', 'actionable_share'), ('Connected: A', 'connected_A'), ('Connected: B', 'connected_B')])}
<h2>When the map became public</h2>
{table(links, [('Link', 'link_id'), ('Relation', 'link'), ('Level', 'level'), ('Visible from', 'visible_from'), ('First source', 'first_source_id')])}
<h2>Method</h2>{md_to_html(readme_section(readme, 'Method, in short'))}
<h2>Reading of the author</h2>{md_to_html(readme_section(readme, 'Reading of the author'))}
<h2>Limits</h2>{md_to_html(readme_section(readme, 'Limits'))}
<h2>Data and code</h2>
<p>Code, inputs and all generated tables: <a href="{REPO}">{REPO}</a>. Every number on this page is generated by the scripts. Licence: MIT.</p>
</main></body></html>
"""


def main() -> None:
    res = analysis.run()
    figures.run(res)
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    block = "<!-- RESULTS:START -->\n" + readme_block(res) + "\n<!-- RESULTS:END -->"
    readme = re.sub(r"<!-- RESULTS:START -->.*?<!-- RESULTS:END -->", lambda _: block, readme, flags=re.S)
    readme_path.write_text(readme, encoding="utf-8")
    (ROOT / "site" / "index.html").write_text(page(res, readme), encoding="utf-8")
    print("Wrote site/index.html and the result block of README.md")


if __name__ == "__main__":
    main()
