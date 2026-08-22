# Self-Healing Competitor Intel Pipeline

A scheduled scraper pipeline that watches competitor pricing and changelog
pages, alerts your team when something changes, and **repairs itself** when
a target site's HTML structure shifts — without you touching anything
downstream.

Built on [Bright Data Scraper Studio](https://brightdata.com).

## The problem

Competitor pricing and changelog pages change without notice. Teams either
check manually (slow, easy to miss) or build brittle scrapers that silently
break the first time a competitor redesigns their pricing table. This
project solves both: it's automated, and when it breaks, it heals itself
from a one-line description instead of a rewrite.

## How it works

```
config/targets.yaml          you list the pages to watch (long-tail, public only)
        │
        ▼
scripts/run_pipeline.py      calls `bdata scraper run <collector_id> <url>`
        │                    for each target, saves a timestamped JSON snapshot
        ▼
scripts/diff_snapshots.py    compares this run to the previous one, field
        │                    by field — new tiers, price changes, new
        │                    changelog entries, anything that shifted
        ▼
scripts/send_alert.py        posts a summary to Slack/Discord if anything
        │                    changed
        ▼
GitHub Actions (weekly cron) runs the whole chain on a schedule and commits
                              new snapshots back to the repo
```

Every scraper is created once with `bdata scraper create`, which hands back
a Collector ID (`c_*`). That ID is what the entire pipeline is built
around — it's a live production endpoint (`POST /dca/trigger`), not a
one-off script. If a target site changes its markup and the scrape breaks,
the fix is:

```bash
bdata scraper heal <collector_id> "<what broke>"
```

**Same Collector ID. Nothing downstream changes.** The diff logic, the
alert webhook, the CI schedule — none of it needs to know a repair
happened. See `demo/break_and_heal_playbook.md` for exactly how this is
demonstrated on camera.

## Structured output

Each snapshot is stored as JSON at `data/snapshots/<target>/<date>.json`:

```json
{
  "target": "example-tool-pricing",
  "captured_at": "2026-08-22T06:00:00Z",
  "data": {
    "tiers": [
      { "name": "Starter", "price": "$19/mo", "features": ["..."] },
      { "name": "Pro", "price": "$49/mo", "features": ["..."] }
    ]
  }
}
```

Diffs are written to `data/latest_diff.json`:

```json
[
  {
    "target": "example-tool-pricing",
    "compared": "2026-08-15 -> 2026-08-22",
    "change_count": 2,
    "changes": [
      { "field": "tiers[1].price", "old": "$49/mo", "new": "$59/mo" }
    ]
  }
]
```

## Setup

1. Create a Bright Data account (free tier: 5,000 credits/month, no card).
   Apply promo code `wemakedevs` for extra hackathon credits.
2. `npx -p @brightdata/cli bdata login`
3. Pick 2–5 long-tail target pages (avoid sites already covered by Bright
   Data's 800+ pre-built scrapers) and for each:
   ```bash
   bdata scraper create <url> "<what data you want>"
   ```
4. Paste the returned Collector IDs into `config/targets.yaml`.
5. `pip install -r requirements.txt`
6. `python scripts/run_pipeline.py` — first snapshot.
7. Wait a cycle (or stage a break — see the playbook) and run again to see
   `diff_snapshots.py` produce real output.
8. Copy `.env.example` to `.env`, fill in `WEBHOOK_URL`, and add
   `BRIGHTDATA_API_KEY` / `WEBHOOK_URL` as GitHub Actions secrets to enable
   the weekly cron in `.github/workflows/weekly-scrape.yml`.

## Project layout

```
config/targets.yaml              target sites + Collector IDs
scripts/run_pipeline.py          runs the scrape, saves snapshots
scripts/diff_snapshots.py        compares snapshots, finds changes
scripts/send_alert.py            posts changes to Slack/Discord
demo/break_and_heal_playbook.md  how the self-healing demo is staged
.github/workflows/                weekly scheduled run
CLAUDE.md                        agent rules — reuse Collector IDs, don't rebuild
```

## Scope & rules followed

- Public pages only — no login walls, no paywalled content, no personal data
- API tokens live in `.env` (gitignored) / GitHub Actions secrets, never
  committed or shown on camera
- Targets are chosen to be long-tail, not sites already covered by Bright
  Data's pre-built scraper library
- The terminal + CLI is the primary interface, per the "terminal is the UI"
  guidance — no dashboard required to operate this
