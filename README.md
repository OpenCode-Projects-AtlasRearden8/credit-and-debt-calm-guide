# The Credit and Debt Calm Guide

A manual for steady credit repair without the fear: pull your own credit
reports safely, dispute errors in plain letters, understand why a credit
freeze beats paid monitoring, see how credit scores actually work in one
simple diagram, and choose a debt-payoff order that respects math *and*
morale. Plus collector-call scripts you can read out loud and a field guide
to spotting credit-repair and debt-settlement scams.

The tone throughout is calm and non-condescending. Credit repair is mostly
paperwork done at a steady pace — not a mystery, and not something anyone
needs to pay a stranger to do.

Written and maintained by **Asdale Dynamics, LLC** as part of its
beginner-friendly guide series (the same spirit behind the book
*The Massive AI Manual*: explain things like a friend would — never
condescending, never alarmist).

## What's inside

| Chapter | What it covers |
|---|---|
| [Start here](docs/index.md) | The calm philosophy and the three moves that matter |
| [Pull your reports safely](docs/01-pull-your-reports-safely.md) | Free reports, avoiding lookalike sites, reading them line by line |
| [Dispute errors in plain letters](docs/02-dispute-errors-plain-letters.md) | What counts as an error, your rights, the 30-day clock |
| [Freezes beat monitoring](docs/03-freezes-beat-monitoring.md) | Why a free freeze blocks more than any paid monitoring service |
| [How scores actually work](docs/04-how-scores-work.md) | The five factors, one diagram, myth-busting |
| [Debt payoff order](docs/05-debt-payoff-order.md) | Avalanche, snowball, and the honest math — with morale respected |
| [Collector-call scripts](docs/06-collector-call-scripts.md) | Word-for-word scripts, your rights, call logging |
| [Spotting repair & settlement scams](docs/07-spotting-credit-and-debt-scams.md) | Red flags, real laws, what legitimate help looks like |
| [Dispute letter templates](docs/dispute-letter-templates.md) | Ready-to-copy letters for bureaus, creditors, and collectors |
| [Worksheets](docs/worksheet-dispute-tracker.md) + two more | Dispute tracker, debt payoff plan, collector call log |
| [Glossary](docs/glossary.md) | Every term, defined like a friend would |

## Read it (local-first, no installs beyond Python)

```bash
# build the static HTML site into site/
python3 build.py

# run the tests
python3 -m unittest discover -s tests -v
```

Then open `site/index.html` in any browser — no server needed (though
`python3 -m http.server -d site` works if you prefer). The site is plain
static HTML: no analytics, no cookies, no third-party scripts, and it works
offline. Worksheets and letters have a print button.

## Companion project

This guide pairs with **`subscription-audit-handbook`** — same gentle
philosophy, opposite direction of money flow. When subscriptions stop
leaking money, there is more left for the minimum payments in chapter 05.

## Project principles

- **Local-first:** plain files, one stdlib Python script, no accounts.
- **Tested:** the build is verified by an automated test suite.
- **Never-condescending:** every term is defined in plain English up front.
- **No secrets:** no API keys, credentials, or personal data in the repo.
- **Education, not advice:** general information about credit and debt in
  the United States — not legal, tax, or financial advice. The chapters
  point to official channels (CFPB, FTC, state Attorney General) for
  serious situations and state-specific rules.

## Where things live

```
docs/                 13 Markdown chapters and worksheets (source of truth)
assets/               stylesheet, favicon, and diagrams, copied into the site
build.py              stdlib-only static site generator (docs/ -> site/)
tests/                converter unit tests + end-to-end build tests
site/                 generated output (not committed; run build.py)
```

## License

MIT — see [`LICENSE`](LICENSE). Copyright (c) 2026 Asdale Dynamics, LLC.
