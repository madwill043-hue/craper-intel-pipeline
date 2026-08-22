#!/usr/bin/env python3
"""
run_pipeline.py

Runs `bdata scraper run <collector_id> <url> --pretty` for every target in
config/targets.yaml, and saves the result as a timestamped JSON snapshot
under data/snapshots/<target_name>/<YYYY-MM-DD>.json

This is the thing GitHub Actions calls on a schedule. It is also exactly
what you run locally to sanity-check a target before wiring up CI.

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --target example-tool-pricing
"""

import argparse
import json
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "targets.yaml"
SNAPSHOT_DIR = ROOT / "data" / "snapshots"


def load_targets():
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    return cfg["targets"]


def run_scraper(collector_id: str, url: str) -> dict:
    """Shell out to the Bright Data CLI and parse the JSON it returns."""
    import platform

    if platform.system() == "Windows":
        cmd = f'bdata scraper run "{collector_id}" "{url}" --pretty'
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=180
        )
    else:
        cmd = ["bdata", "scraper", "run", collector_id, url, "--pretty"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    if result.returncode != 0:
        raise RuntimeError(
            f"bdata scraper run failed for {collector_id} ({url}):\n{result.stderr}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Could not parse JSON from bdata output for {collector_id}:\n"
            f"{result.stdout[:500]}"
        ) from e


def save_snapshot(target_name: str, payload: dict, run_date: date):
    out_dir = SNAPSHOT_DIR / target_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{run_date.isoformat()}.json"

    wrapped = {
        "target": target_name,
        "captured_at": datetime.utcnow().isoformat() + "Z",
        "data": payload,
    }
    with open(out_path, "w") as f:
        json.dump(wrapped, f, indent=2)

    latest_path = out_dir / "latest.json"
    with open(latest_path, "w") as f:
        json.dump(wrapped, f, indent=2)

    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="Only run a single target by name", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print what would run without calling bdata")
    args = parser.parse_args()

    targets = load_targets()
    if args.target:
        targets = [t for t in targets if t["name"] == args.target]
        if not targets:
            sys.exit(f"No target named '{args.target}' found in targets.yaml")

    run_date = date.today()
    failures = []

    for t in targets:
        name, url, cid = t["name"], t["url"], t["collector_id"]

        if cid.startswith("REPLACE_ME"):
            print(f"[skip] {name}: no collector_id set yet in targets.yaml")
            continue

        print(f"[run]  {name} -> {url} (collector {cid})")

        if args.dry_run:
            print(f"  (dry run, skipping actual scrape)")
            continue

        try:
            payload = run_scraper(cid, url)
            path = save_snapshot(name, payload, run_date)
            print(f"  saved -> {path}")
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failures.append(name)

    if failures:
        print(f"\n{len(failures)} target(s) failed: {', '.join(failures)}")
        print("If this is a structural break (site changed HTML), run:")
        print('  bdata scraper heal <collector_id> "<describe what broke>"')
        sys.exit(1)

    print("\nPipeline run complete.")


if __name__ == "__main__":
    main()