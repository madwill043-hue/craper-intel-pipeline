# Break & Heal Demo Playbook

This is the centerpiece of the submission. Judging criterion 5 ("Reliability
and self-healing") and Rule 3 ("show `bdata scraper heal` working... this is
what judges will look for") both point here directly. Do not skip rehearsing
this.

## The problem with "waiting for a real site to break"

You can't schedule a competitor's HTML change to happen during your five
minute demo. Two honest options:

### Option A — catch a real break (best, but not guaranteed)
Run the pipeline daily for several days before recording. If any target's
markup shifts for real, you have authentic footage. Keep the raw failure
output (`bdata` error, or garbled JSON) as evidence.

### Option B — stage a real, verifiable break (recommended, still honest)
Pick ONE target you don't mind being aggressive with. Locally, fetch the
current page HTML, modify the CSS selector Scraper Studio is relying on, OR
simply point the scraper at a mirrored/modified copy of the page with the
structure changed. Run the scraper against that changed version, capture the
real failure, then run `bdata scraper heal` against it for real.

This is NOT faking data — the scraper genuinely breaks and genuinely gets
repaired by the tool. You are only choosing *when* the break happens instead
of waiting for luck. Say this plainly in the demo narration: "I modified the
page structure to force a real break, so I could show you the repair."
Transparency here is a presentation plus, not a minus.

## What to say on camera (script skeleton)

1. "Here's the pipeline running normally — [show `run_pipeline.py` output,
   clean JSON snapshot saved]."
2. "Here's the scheduled GitHub Actions run — [show the workflow file and a
   green run in the Actions tab]."
3. "Now watch what happens when the target site's structure changes —
   [trigger the break]."
4. "The pipeline run fails / returns garbage — [show the actual error or
   corrupted extraction]."
5. "One command: `bdata scraper heal <collector_id> "<what broke>"` — [run
   it live, or show the real recorded run if it takes a few minutes]."
6. "Same Collector ID. Nothing downstream — the diff script, the alert
   webhook, the CI workflow — none of it changed. Re-run the pipeline —
   [show it succeeding again]."

## Commands you'll actually run

```bash
# 1. Normal run
python scripts/run_pipeline.py --target <your-chosen-target>

# 2. (after staging the break) — this should fail or return bad data
python scripts/run_pipeline.py --target <your-chosen-target>

# 3. Heal it — describe the real break you introduced
bdata scraper heal <collector_id> "the pricing table moved from a <table> to a <div> grid layout"

# 4. Confirm it's fixed — same collector_id, same command as step 1
python scripts/run_pipeline.py --target <your-chosen-target>

# 5. Show the diff/alert layer still works untouched
python scripts/diff_snapshots.py --target <your-chosen-target>
```

## Recording checklist

- [ ] `.env` / API tokens masked or on a throwaway key before recording
- [ ] Terminal font size large enough to read on a recorded video
- [ ] Have a pre-recorded backup clip of the heal succeeding, in case the
      live one is slow or the API has a hiccup during recording
- [ ] Show the Collector ID on screen before and after — same ID, visually
- [ ] End on the diff + alert firing, to tie back to "this solves a real
      problem," not just "the tool works"
