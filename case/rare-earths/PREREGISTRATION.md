# Pre-registration: case 2, China's 2025 rare-earth magnet export controls

**Written and committed on 17 November 2026, before any evidence row of this case exists.** The Git
commit time of this file proves the order. Every later change goes into the change log at the end,
with a date and a reason. Approved by Nikhil Sehgal (Checkpoint 0, 17 November 2026).

## Why this case

Case 1 (Nexperia, 2025) gave a map value of 330 days for one hidden firm. Case 2 tests the method on
a different kind of hidden node: a country-level supply of a material. It also tests what does not
work, with a count of false alarms. The case is close to vehicle powertrains: rare-earth magnets
sit in electric motors, actuators and e-drives.

## The case

- **Trigger.** On 4 April 2025, China's Ministry of Commerce and General Administration of Customs
  (Announcement No. 18 of 2025) put export licensing on seven medium and heavy rare earths, including
  terbium- and dysprosium-containing NdFeB magnet materials and samarium-cobalt magnet materials.
- **Observer.** Vehicle makers (`VM`).
- **Nodes and links.**
  - `CNRE` (rare-earth separation and magnet supply in China) supplies `MAG` (makers of rare-earth
    magnets).
  - `MAG` supplies `T1` (tier-1 suppliers of motors, actuators and e-drives).
  - `T1` supplies `VM`.
- **Event types.** `control` (an export-control measure), `rule` (a regulation), `warning`,
  `production_stop`, `supply_stop`, `suspension`, `exemption`, `response`. A `response` is a firm's
  own action, such as building inventory. It is reported but is not a signal.

## Questions

- **Q1.** Does the map value work for a country-level material node, not only for one firm?
- **Q2.** Of the seven measures in the signal class below, how many were followed by a production
  stop within 6 months? This is the false-alarm test.
- **Q3.** Did the trigger itself leave enough time to act?

## Predictions (checked after the analysis and reported either way)

- **P1.** Generic links (China supplies most rare earths; magnets go into vehicle parts) were public
  years before the trigger. Named links (which suppliers or parts depend on Chinese magnets) became
  public only in May or June 2025.
- **P2.** Observer B's first actionable connected signal comes many months before the first stop, so
  the map value is large.
- **P3.** Only 1 of the 7 class measures was followed by a stop within 6 months.
- **P4.** Public attention reacted within days of the trigger, unlike in case 1.

## Rules

- **R0. Sources.** Evidence comes only from tier-1 sources (regulators, governments, company
  documents, official statistics, intergovernmental reports) or tier-2 sources (wire services,
  trade press, industry associations, law-firm briefings for dates). Tier 3 (Wikipedia, blogs,
  aggregators) is never evidence.
- **R1. Window.** Signals count from 730 days before the first stop. Sensitivity runs use 365 and
  1095 days.
- **R2. Relevance.** A signal on `CNRE` counts if it restricts the export of rare earths, their
  alloys or magnets, or gives the state control over that export.
- **R3. Attention.** Daily Wikipedia page views of "Rare-earth element" and of "Dysprosium". An
  attention signal needs 3 or more spike days in a row (views at least 5 times the 28-day median and
  at least 500). The two articles were chosen after a probe of the page views on 17 November 2026.
  The probe also looked at "Neodymium magnet", which had no spike days. This is said openly here.
- **R4. Connection.** Observer A uses only links that a source names. The variant with generic
  links is reported too.
- **R5. First stop.** The earliest public date of a tier-1 or tier-2 report of an actual production
  stop or cut at a vehicle maker or a tier-1 supplier, which the source attributes to rare-earth or
  magnet supply. A threat of a stop does not count. The candidate known at registration is the
  CLEPA statement of 4 June 2025; an earlier qualifying report replaces it.
- **R6. Time to act.** The grid:
  - time to survive (stocks): 14, 30 or 60 days;
  - time to recover (an export licence or another source): 63, 126 or 180 days. 63 days is 45
    working days, the licence review time. 126 days is two such rounds. 180 days is an upper bound
    and an assumption of this study.

  Each value gets a source quote in `assumptions.csv` before the analysis. The needed lead time is
  then 3 to 166 days.
- **R7. False-alarm test.**
  - The signal class is the seven Chinese export-control measures on materials from July 2023 to
    October 2025:
    1. gallium and germanium, announced 3 July 2023;
    2. graphite, announced 20 October 2023;
    3. antimony, announced 15 August 2024;
    4. the ban on gallium, germanium, antimony and superhard materials to the United States,
       3 December 2024;
    5. tungsten, tellurium, bismuth, molybdenum and indium, 4 February 2025;
    6. the seven medium and heavy rare earths and their magnets, 4 April 2025;
    7. the extension of the rare-earth controls, announced 9 October 2025.
  - The outcome of a measure is a tier-1 or tier-2 report of an actual production stop at a vehicle
    maker or a tier-1 supplier, attributed to that measure, within 6 months of its effective date
    (or of its announcement, if it was suspended before it took effect).
  - Where no report is found, the result is "no stop found", not "no stop".
  - Search protocol for each measure, logged in `search_log.csv` with the date and the result:
    - "<material> export controls production halt automaker"
    - "<material> shortage automotive plant stop"
    - "<material> export controls vehicle production"

    Searched: a general web search, and the press archives of ACEA, CLEPA and VDA.
  - The company-specific Chinese export ban on Nexperia China (October 2025) is not a material
    measure and is not in the class.
- **R8. Case 1 stays fixed.** The case-1 rules and numbers do not change because of case 2. A
  regression test guards them.

## What counts as "works" and "does not work"

- **Q1 works** if the named-link rule separates observer A from observer B with a map value that
  stays within 180 days across the three windows (R1). If the map value moves by more than 180 days
  between windows, the result is "window-dependent": the metric does not find one clear warning for
  a chronic risk.
- **Q2.** A class precision of 2 in 7 or lower means that this kind of warning alone does not
  justify action. A firm that acts on every such measure would mostly act on false alarms.
- **Q3 works** if the trigger has an actionable share above 0 in the grid (R6).

## Change log

- *(empty at registration)*
