# Research Watch

A self-updating evidence base for the Co-Produced AI Governance curriculum.

It watches the nine sources the curriculum is built on for changes, discovers new
research each week, scores candidates against a relevance rubric, and emails a digest.
Approved items regenerate the foundations block on the citation reference page.

**Nothing enters the evidence base without an explicit approval step.** The system
discovers and drafts. A human decides.

## What it watches

Eleven records sit in `data/registry.json`: the ten foundational and standards sources
plus TRAIGA, which is watched for change and held out of the published sources list
because it is law the curriculum references and not a source it is built on.

## Three streams

Every record carries an `applies_to` map keyed by line of work. A stream is omitted
when it does not apply, so absence is meaningful.

```json
"applies_to": {
  "curriculum":      { "refs": ["W2-S1", "toolkit-rubric"], "note": "" },
  "rootwork":        { "refs": [], "note": "Why this matters to infrastructure work." },
  "case_management": { "refs": [], "note": "Why this matters to the software line." }
}
```

`curriculum` uses the segment vocabulary (`W1-S1` through `W3-S2`, `toolkit-*`). The other
two are tagged at stream level for now, with the note carrying the specifics, until those
work streams have a defined component structure. Adding refs later needs no migration.

Curriculum keeps its explanation in the top-level `why_it_matters`, which is the line the
public page renders. The per-stream `note` fields are internal.

```bash
python -m src.render     # public: output/reference.md + foundations.html, curriculum only
python -m src.streams    # internal: output/streams.md, all three streams
```

## Three folders, three jobs

- `data/` and `output/` are the watch loop. Machine-maintained, publicly rendered.
- `digests/` holds long-form reads of individual sources. Human-written, never rendered.
- `landscape/` holds competitor and market intelligence. Human-written, deliberately
  excluded from public output. See `landscape/README.md` for the rule.

`BUILD-BRIEF.md` is the orientation file for whoever starts building the curriculum.
Read that first.

Tier A checks the existing base for revisions, errata, and retractions. Tier B searches
arXiv, OpenAlex, and Semantic Scholar for new work on AI literacy, governance in
mission-driven organizations, participatory and co-produced AI, and procurement rubrics.

## Running it

```bash
pip install -r requirements.txt

python -m src.seed                 # one time: load the evidence base
python -m src.fetch                # collect candidates
python -m src.score                # score them against config/rubric.md
python -m src.digest               # build output/digest.md
python -m src.digest --send        # and email it
python -m src.approve              # decide on each item
python -m src.render               # regenerate the foundations block
```

Useful flags while testing: `src.fetch --dry-run` skips the network,
`src.score --offline` uses a keyword stub so no API key is needed, and
`src.approve --list` shows pending items without deciding.

## Updating the citation reference page

```bash
python -m src.render --inject ../intentional-data-citation-reference.html
```

This replaces only the foundations block, between the
`<!-- research-watch:foundations:start -->` and `<!-- research-watch:foundations:end -->`
markers. The interactive segment map above it stays hand maintained. On the first run
the markers do not exist yet, so the script finds the existing `div.foundations` block
and inserts them.

## Credentials you need to add

These are yours to set. The code reads them from the environment and never stores them.

| Secret | Used by | Where to set it |
|---|---|---|
| `ANTHROPIC_API_KEY` | `src.score` | GitHub repo settings, Secrets and variables, Actions |
| `SMTP_HOST` | `src.digest --send` | same |
| `SMTP_PORT` | `src.digest --send` | same, defaults to 465 |
| `SMTP_USER` | `src.digest --send` | same |
| `SMTP_PASSWORD` | `src.digest --send` | same, use an app password |

Without `ANTHROPIC_API_KEY` the scorer falls back to a keyword stub and says so.
Without the SMTP values the digest is written to `output/digest.md` and nothing is sent.

## Schedule

The workflow file must sit at the **repository root** in `.github/workflows/watch.yml`, since GitHub Actions only reads that location. A staging copy lives in this folder at `.github/workflows/watch.yml`. It already sets `working-directory: research-watch`, so it works from the root. It runs Mondays at 13:00 UTC, which is 08:00 Central during
daylight time. It commits changes to `data/` and `output/` back to the repo, so every
week is diffable in git history. Trigger it by hand from the Actions tab to test.

## House style

`src/common.py` enforces the rules on everything generated: no em dashes, no
"X, not Y" construction, no "rather than" contrast, and no banned strings.
`src.render` exits non-zero on a violation, so a bad generation cannot be published.

## Layout

```
config/     sources.yaml, rubric.md, branding.yaml
data/       registry.json (the evidence base), seen.json, pending.json
src/        seed, fetch, score, digest, approve, render, common
templates/  foundations.html.j2, reference.md.j2, digest.md.j2
output/     generated artifacts
```
