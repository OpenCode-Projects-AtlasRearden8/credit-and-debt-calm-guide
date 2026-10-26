# STATUS — The Credit and Debt Calm Guide

*Last updated: 2026-10-26*

## What was built

A complete, local-first beginner manual for steady credit repair without fear,
written in the house style (plain English, never condescending, never
alarmist), with a static HTML site generated from the Markdown source by a
stdlib-only build script.

**Core chapters (docs/):**

- `index.md` — Start here: the calm premise, the three moves that matter, a route map.
- `01-pull-your-reports-safely.md` — soft vs. hard pulls, annualcreditreport.com vs.
  lookalikes, line-by-line report reading, local PDF storage, pull cadence.
- `02-dispute-errors-plain-letters.md` — what is disputable, your FCRA baseline,
  30-day clock, online-vs-certified-mail choice, letter anatomy, escalation path.
- `03-freezes-beat-monitoring.md` — the doorbell-vs-lock argument, freeze mechanics
  at all three bureaus (+ Innovis), thawing on purpose, freeze vs. lock vs. fraud
  alert, when monitoring still earns its keep.
- `04-how-scores-work.md` — one simple diagram (`assets/scores-diagram.svg`), the
  five factors in plain paragraphs, report-vs-score distinction, myth-busting.
- `05-debt-payoff-order.md` — avalanche (math), snowball (morale), a hybrid plan,
  a worked example, consolidation fine print, state-specific debt types, and the
  "can't make minimums" path via vetted nonprofit counseling.
- `06-collector-call-scripts.md` — FDCPA rights in plain words, five ground rules,
  five word-for-word scripts, the 30-day validation window, the partial-payment
  statute-of-limitations trap (state AG as the verification source).
- `07-spotting-credit-and-debt-scams.md` — CROA and settlement fee rules, translated
  red-flag quotes (accurate-info deletion, guaranteed scores, CPN scam, dispute
  mills), the honest version of debt settlement, a 5-step vetting routine.

**Practical extras:**

- `dispute-letter-templates.md` — three copy-and-fill letters (bureau dispute,
  direct creditor dispute, collector validation request) + a 30-day rhythm checklist.
- `worksheet-dispute-tracker.md`, `worksheet-debt-payoff-plan.md`,
  `worksheet-collector-call-log.md` — printable worksheets (print button on site).
- `glossary.md` — 26 plain-English definitions, each cross-linked to its chapter.

**Infrastructure:**

- `build.py` — stdlib-only Markdown → static HTML site generator into `site/`
  (no third-party packages; curated page order; nav; prev/next; print buttons;
  disclaimer + exact copyright in every page footer).
- `assets/` — stylesheet, favicon, and the hand-written scores diagram (`SVG`,
  validated XML).
- `tests/test_build.py` — 45 automated tests (see Verification below).
- `README.md`, `LICENSE` (MIT, exact line `Copyright (c) 2026 Asdale Dynamics,
  LLC`), `.gitignore` (generated `site/` not committed).

The guide complements **subscription-audit-handbook** (mentioned in README and
in chapters 04/05): trim recurring charges to free up payoff money.

## How to run it

```bash
python3 build.py                              # docs/ + assets/ -> site/
python3 build.py --out SOME/DIR               # build anywhere else
python3 -m unittest discover -s tests -v      # run the test suite
```

Then open `site/index.html` in any browser. No server needed
(`python3 -m http.server -d site` works too). Works fully offline;
no analytics, cookies, or third-party scripts.

## Verification results

- `python3 -m unittest discover -s tests` — **45/45 passing.**
- Coverage includes: converter unit tests (headings, inline, links, tables,
  task lists, fences), content coverage (all 13 required pages exist and are
  registered in the build's page order), end-to-end build into a temp dir
  (every page renders, nav/prev-next correct, every internal link and image
  resolved, no duplicate heading ids, no unconverted `.md` links), print
  buttons only on worksheets/letters, exact copyright line in LICENSE and on
  every page footer, LLC credit in README, the diagram asset validated
  (percentages + factor labels present, referenced by chapter 04), and scans
  for secret-shaped (`sk-`, `AKIA`, `ghp_`, …) and SSN-shaped strings in the
  repo sources. Companion guide (`subscription-audit-handbook`) presence tested.
- `python3 build.py --out DIR` verified in a temp directory: 16 files.
- All 13 generated HTML pages pass an HTML tag-balance check (0 errors).
- Both SVG assets parse as valid XML.

## Known gaps

- **Not legal, tax, or financial advice.** The guide states this on every
  generated page and points serious situations to CFPB, FTC/identitytheft.gov,
  and state Attorneys General. It deliberately does not quote state-specific
  statutes of limitations or bureau mailing addresses, which change; it shows
  the process for verifying them instead.
- **Score weights are the classic textbook pattern** (35/30/15/10/10) for one
  typical model family; other models version-shift the numbers. The diagram
  and chapter say so.
- The static site is button-light by design; the only JavaScript anywhere is
  the optional print button (`window.print()`).
- `site/` is generated and intentionally not committed (`.gitignore`); run
  `python3 build.py` after cloning.
- Coverage deliberately centers US federal consumer-credit basics; state and
  non-US specifics (garnishment thresholds, collection licensing, etc.) are
  out of scope, with pointer-to-official-source handling instead.
