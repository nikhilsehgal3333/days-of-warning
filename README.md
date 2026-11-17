# Days of warning

**How many days of warning is a hidden-tier supply chain map worth?**

This is an independent study by Nikhil Sehgal. It uses public data only. It is not a product of
Daimler Truck, the University of St.Gallen, BMW Group, Ulm University or Catena-X. It is a set of
illustrative backtests of single cases, not a forecast and not a monitoring tool.

Status: proof of concept, version 0.2. Two cases:

- **The 2025 Nexperia chip disruption** (`case/nexperia/`): one hidden firm and its owner.
- **China's 2025 rare-earth magnet export controls** (`case/rare-earths/`): a country-level supply of
  a material. Its rules were committed before any evidence was collected
  (`case/rare-earths/PREREGISTRATION.md`), and it includes a false-alarm test.

## The question

Two observers watch the same public signals.

- **Observer A** knows only the links of the supply chain that a public source named, firm by firm,
  on each date.
- **Observer B** knows all links from the start. A multi-tier mapping tool or supplier compliance
  data could give a firm this map.

For each observer, the study finds the first public signal that the observer could connect to its
own supply chain early enough to act. The **map value** is the lead time of B minus the lead time of
A, in days. Each case explains its own story, reading and limits in `case/<case>/narrative.md`.

## Result

<!-- RESULTS:START -->
**The 2025 Nexperia chip disruption**

- Map value: **330 days**.
- Observer B (full map) could act on event E01, public on 2024-12-02, 330 days before the first production stop on 2025-10-28.
- Observer A (public map, named links) had no connected signal early enough to act. Its first connected signal of any kind was E07, 12 days before the stop.
- Needed lead time in the grid: 48 to 166 days.
- Variant with generic links: map value 0 days.

**China's 2025 rare-earth magnet export controls**

- Map value: **333 days**.
- Observer B (full map) could act on event E01, public on 2024-07-01, 333 days before the first production stop on 2025-05-30.
- Observer A (public map, named links) had no connected signal early enough to act. Its first connected signal of any kind was E04, 2 days before the stop.
- Needed lead time in the grid: 3 to 166 days.
- Variant with generic links: map value 0 days.

Full tables: `results/<case>/RESULTS.md`. Figures: `site/<case>/`.

### What works and what does not

- **Works: the map value.** It was 330 days for one hidden firm and 333 days for a country-level material supply, and it stayed the same across the 12-, 24- and 36-month windows. In both cases the early signal was a state measure.
- **Does not work: generic public knowledge.** The generic variant gives a map value of 0 and 0 days: the industry-level dependency was public, but the named public map first reached the hidden node only on 2025-10-17 and 2025-06-05, after the first stop.
- **Mixed: the trigger.** It left 11 days in the Nexperia case (actionable share 0.0) and 56 days in the rare-earth case (share 0.333).
- **Does not work: acting on every warning.** Only 1 of 7 Chinese export controls on materials from 2023 to 2025 was followed by a vehicle production stop (2 of 7 with a borderline case).
- **Pre-registered predictions of case 2:** P1 yes, P2 yes, P3 yes, P4 partly.

### Comparison

| | The 2025 Nexperia chip disruption | China's 2025 rare-earth magnet export controls |
|---|---|---|
| Hidden node | one firm and its owner | a country-level supply of a material |
| First stop | 2025-10-28 | 2025-05-30 |
| Map value (days) | 330 | 333 |
| Map value, generic variant (days) | 0 | 0 |
| First signal observer B could act on | E01 | E01 |
| Its lead time (days) | 330 | 333 |
| Named public map first connects the hidden node | 2025-10-17 | 2025-06-05 |
| Lead time of the trigger (days) | 11 | 56 |
| Trigger actionable share | 0.0 | 0.333 |
| Attention lag after the trigger (days) | Nexperia: -5 | Dysprosium: +2; Rare-earth element: +189 |
| Spread of the map value across windows (days) | 0 | 0 |

**Pre-registered predictions (case 2)**

| | Prediction | Held |
|---|---|---|
| P1 | Generic links public years before the trigger; named links only from May or June 2025 | yes |
| P2 | Observer B's first actionable connected signal comes many months (90 days or more) before the first stop | yes |
| P3 | Exactly 1 of the 7 class measures was followed by a stop within 6 months | yes |
| P4 | Public attention reacted within 7 days of the trigger | partly |

**Pre-registered criteria (case 2)**

| | Criterion | Result |
|---|---|---|
| Q1 | Map value stable within 180 days across the 12-, 24- and 36-month windows | works |
| Q2 | Class precision of 2 in 7 or lower | this kind of warning alone does not justify action |
| Q3 | The trigger left time to act (actionable share above 0) | works |
<!-- RESULTS:END -->

## Method, in short

- **Point-in-time evidence.** Every link and every event has a source with a date, and a quote of 30
  words or fewer that a program finds word for word in the downloaded text (`htw/checks.py`). Most
  sources are pinned to an exact copy in the Wayback Machine.
- **Source rule.** Evidence comes from primary or official sources (regulators, courts, company
  documents, official statistics) or, where none exists, from established secondary sources (wire
  services, trade press, industry associations). Wikipedia, blogs and aggregators are never evidence;
  the check rejects them. Wikipedia page views are used only as a measure of public attention.
- **Public date.** A signal counts from the first day an outsider could know it, which can be later
  than the day it took effect.
- **First stop.** The earliest public report of an actual production stop at a vehicle maker or a
  tier-1 supplier that the source links to the case. A threat of a stop does not count.
- **Time to act.** Each case has a grid of the time to survive (how long stocks last) and the time to
  recover (how long a new source or a licence takes), with a source quote for each value in
  `case/<case>/assumptions.csv`. A signal is actionable in a grid cell if its lead time is at least
  the time to recover minus the time to survive. The values are an assumption of this study.
- **Connection.** An observer can connect a signal if a chain of known links joins it to the vehicle
  makers. Observer A counts a link only when a source names a specific firm, or the suppliers of a
  specific firm, on it. The results also show a generic variant, which counts statements about an
  industry or a country.
- **Window.** Signals count from 730 days before the first stop; the results also show 365 and 1095
  days.
- **Attention.** Daily Wikipedia page views. An attention signal needs three or more spike days in a
  row. This rule was added after seeing the case-1 data, because single spike days were not followed
  by any event.
- **False alarms (case 2).** For a class of similar signals, the share that was followed by a stop,
  with a logged search for each signal (`case/rare-earths/search_log.csv`).
- **Human check.** Nikhil Sehgal checked all map links and a random sample of events of each case
  against the sources before the analysis (`case/<case>/gold_check.csv`).

## Run it

Python 3.10 or later. Install the two packages, then run the study:

```
py -m pip install -r requirements.txt
py -m unittest            # unit tests
py run_all.py             # download the sources, check the quotes, calculate, draw
py site/build.py          # build site/index.html and the result block of this README
```

`case/<case>/` holds the hand-made inputs of each case: settings, nodes, sources, evidence, the time-to-act grid, the human check and the narrative. `results/`
holds the generated files. Source texts are downloaded to `local/`, which is not part of the
repository.

## Licence

MIT, see `LICENSE`.
