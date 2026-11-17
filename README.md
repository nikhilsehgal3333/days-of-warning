# Days of warning

**How many days of warning was a hidden-tier supply chain map worth in the 2025 Nexperia chip disruption?**

This is an independent study by Nikhil Sehgal. It uses public data only. It is not a product of
Daimler Truck, the University of St.Gallen, BMW Group, Ulm University or Catena-X. It is an
illustrative backtest of one case, not a forecast and not a monitoring tool.

Status: proof of concept, version 0.1.

## The case

Nexperia makes standard chips that tier-1 suppliers build into the modules they sell to vehicle
makers. In autumn 2025 a dispute between the Netherlands and China over Nexperia, a subsidiary of
the Chinese firm Wingtech, stopped deliveries from Nexperia's China plant. Vehicle makers learned
that they depended on a supplier that few of them could see in their own supply chain. Honda
stopped vehicle production in Mexico on 28 October 2025.

## The question

Two observers watch the same public signals.

- **Observer A** knows only the links of the supply chain that a public source named on each date.
- **Observer B** knows all links from the start. A multi-tier mapping tool or supplier compliance
  data could give a firm this map.

For each observer, the study finds the first public signal that the observer could connect to its
own supply chain early enough to act. The **map value** is the lead time of B minus the lead time of
A, in days.

## Result

<!-- RESULTS:START -->
- Map value: **330 days**.
- Observer B (full map) could act on event E01, public on 2024-12-02, 330 days before the first production stop on 2025-10-28.
- Observer A (public map, named links) had no connected signal early enough to act. Its first connected signal of any kind was E07, 12 days before the stop.
- Needed lead time in the grid: 48 to 166 days.
- Generic variant ("used in the automotive industry" counts as a link): map value 0 days. Public data connected the early signal to the industry, but not to any named supplier or part.

| Event | Channel | Public date | Lead time (days) | Actionable share | A | B |
|---|---|---|---|---|---|---|
| E01 listed (WT) | regulatory | 2024-12-02 | 330 | 1.0 | no | yes |
| E03 rule (NEX) | regulatory | 2025-09-30 | 28 | 0.0 | no | yes |
| E04 order (NEX) | legal | 2025-10-12 | 16 | 0.0 | no | yes |
| A01 attention (NEX) | attention | 2025-10-12 | 16 | 0.0 | no | yes |
| E06 ruling (NEX) | legal | 2025-10-13 | 15 | 0.0 | no | yes |
| E07 warning (VM) | association | 2025-10-16 | 12 | 0.0 | yes | yes |
| E05 ban (NEXCN) | trade | 2025-10-17 | 11 | 0.0 | yes | yes |
| E15 warning (NEX) | operational | 2025-10-17 | 11 | 0.0 | yes | yes |
| E09 warning (T1) | operational | 2025-10-24 | 4 | 0.0 | yes | yes |

Full tables: [`results/RESULTS.md`](results/RESULTS.md). Figures: `site/`.
<!-- RESULTS:END -->

## Method, in short

- **Point-in-time evidence.** Every link and every event has a source with a date, and a quote of 30
  words or fewer that a program finds word for word in the downloaded text (`htw/checks.py`). Most
  sources are pinned to an exact copy in the Wayback Machine.
- **Source rule.** Evidence comes from primary or official sources (regulators, courts, company
  documents, official statistics) or, where none exists, from established secondary sources (wire
  services, trade press, industry associations). Wikipedia, blogs and aggregators are never evidence;
  the check rejects them. Wikipedia page views are used only as a measure of public attention.
- **Public date.** A signal counts from the first day an outsider could know it. The Dutch state
  order took effect on 30 September 2025 but became public on 12 October 2025.
- **Time to act.** The European vehicle makers' association said that stocks would last "only a few
  weeks" and that approving new suppliers "would take several months". The study turns these words
  into a grid: time to survive of 14, 28 or 42 days, and time to recover of 90, 135 or 180 days. A
  signal is actionable in a grid cell if its lead time is at least the time to recover minus the time
  to survive. These values are an assumption of this study.
- **Connection.** An observer can connect a signal on a firm if a chain of known links joins the
  firm to the vehicle makers. Observer A counts a link only when a source names it. Before the
  crisis, public sources said only that Nexperia chips are "used in the automotive industry". The
  results also show this generic variant.
- **Attention.** Daily Wikipedia page views of "Nexperia". An attention signal needs three or more
  spike days in a row. This rule was added after seeing the data, because two single spike days in
  2024 were not followed by any event.
- **Human check.** Nikhil Sehgal checked all map links and a random sample of 10 events against the
  sources before the analysis. Three map links were replaced later under the source rule and wait for
  the same check.

## Reading of the author

This is interpretation, not a proven finding.

1. In this case, the decisive early signal did not concern the chip maker itself. It concerned its
   owner, two steps away from the vehicle makers' parts.
2. Public data showed that the automotive industry depended on Nexperia. It did not show which
   suppliers, modules or parts did. That gap, not a lack of warnings, is what made the warning
   useless to an outside observer.
3. Public attention came late. It rose sharply only when the Dutch order became public, shortly
   before the first stop. Earlier single spikes were false alarms.
4. For a firm, the value of a multi-tier map lies in connecting outside signals to its own parts.
   This one case cannot say how often such signals are false alarms.

## Limits

- **One case, chosen after the fact.** The case was chosen because a disruption happened, so lead
  times look better than a live monitor would see. One case gives no false-alarm rate.
- **The December 2024 listing did not apply to Nexperia itself.** It was a signal on the owner. The
  first US rule that covered Nexperia came on 29 September 2025.
- **Public sources found by one person.** An earlier public source may exist for a link. The study
  found the Dongguan plant named only in sources after the crisis.
- **The time-to-act grid is an assumption** based on one statement by the vehicle makers' association.
- **Observer B is an ideal.** Real multi-tier maps are incomplete, and a firm still has to read and
  act on a signal.
- **No firm-specific claim.** The study makes no claim about the suppliers or the exposure of any
  named vehicle maker other than what the cited sources say.

## Run it

Python 3.10 or later. Install the two packages, then run the study:

```
py -m pip install -r requirements.txt
py -m unittest            # unit tests
py run_all.py             # download the sources, check the quotes, calculate, draw
py site/build.py          # build site/index.html and the result block of this README
```

`case/` holds the hand-made inputs: nodes, sources, evidence and the time-to-act grid. `results/`
holds the generated files. Source texts are downloaded to `local/`, which is not part of the
repository.

## Licence

MIT, see `LICENSE`.
