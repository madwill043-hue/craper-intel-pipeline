# Agent rules for this repo

## Do not rebuild scrapers that already exist

Collector IDs are pinned in `config/targets.yaml`. If a target already has a
non-placeholder `collector_id`, DO NOT run `bdata scraper create` again for
it — reuse the existing Collector ID with `bdata scraper run` or
`bdata scraper heal`. Creating a new scraper for the same target wastes
credits and breaks the "same Collector ID, nothing downstream changes"
story this project depends on.

## When a scrape fails

1. Check whether it's a real structural break (site HTML changed) vs. a
   transient network issue (retry once first).
2. If structural: `bdata scraper heal <collector_id> "<describe what broke>"`
3. Never delete a Collector ID and recreate from scratch unless explicitly
   asked — the whole point of this project is stable IDs across repairs.

## Adding a new target

1. `bdata scraper create <url> "<what to extract>"`
2. Paste the returned Collector ID into `config/targets.yaml`
3. Run `python scripts/run_pipeline.py --target <name>` once to confirm it
   captures clean data before relying on the scheduled job.

## Scope

Public pages only. No login-walled sites, no paywalled content, no personal
data. Keep API tokens out of the repo — use `.env` (already gitignored) or
GitHub Actions secrets, never hardcoded.
