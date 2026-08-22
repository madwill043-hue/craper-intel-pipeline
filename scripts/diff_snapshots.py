#!/usr/bin/env python3
"""
diff_snapshots.py

Compares the two most recent snapshots for each target and produces a
human-readable summary of what changed: new pricing tiers, price changes,
new changelog entries, removed features, etc.

Outputs a list of change dicts, printed as JSON and also returned for
send_alert.py to consume.

Usage:
    python scripts/diff_snapshots.py
    python scripts/diff_snapshots.py --target example-tool-pricing
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = ROOT / "data" / "snapshots"


def get_last_two_snapshots(target_dir: Path):
    dated = sorted(
        [p for p in target_dir.glob("*.json") if p.stem != "latest"],
        key=lambda p: p.stem,
    )
    if len(dated) < 2:
        return None, None
    return dated[-2], dated[-1]


def load(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)["data"]


def flatten(obj, prefix=""):
    """Flatten nested JSON into {path: value} for simple key-level diffing."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def diff_targets(old: dict, new: dict) -> list[dict]:
    flat_old = flatten(old)
    flat_new = flatten(new)

    changes = []
    for key in sorted(set(flat_old) | set(flat_new)):
        old_val = flat_old.get(key, "<missing>")
        new_val = flat_new.get(key, "<missing>")
        if old_val != new_val:
            changes.append({"field": key, "old": old_val, "new": new_val})
    return changes


def diff_target(target_name: str) -> dict | None:
    target_dir = SNAPSHOT_DIR / target_name
    if not target_dir.exists():
        return None

    prev_path, curr_path = get_last_two_snapshots(target_dir)
    if not prev_path:
        print(f"[{target_name}] only one snapshot so far, nothing to diff yet")
        return None

    old_data = load(prev_path)
    new_data = load(curr_path)
    changes = diff_targets(old_data, new_data)

    return {
        "target": target_name,
        "compared": f"{prev_path.stem} -> {curr_path.stem}",
        "change_count": len(changes),
        "changes": changes,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=None)
    args = parser.parse_args()

    if not SNAPSHOT_DIR.exists():
        print("No snapshots yet. Run scripts/run_pipeline.py first.")
        return

    target_dirs = (
        [SNAPSHOT_DIR / args.target]
        if args.target
        else [d for d in SNAPSHOT_DIR.iterdir() if d.is_dir()]
    )

    all_results = []
    for d in target_dirs:
        result = diff_target(d.name)
        if result and result["change_count"] > 0:
            all_results.append(result)
            print(f"\n=== {d.name} ({result['change_count']} change(s)) ===")
            for c in result["changes"]:
                print(f"  {c['field']}: {c['old']!r} -> {c['new']!r}")
        elif result:
            print(f"[{d.name}] no changes since last run")

    out_path = ROOT / "data" / "latest_diff.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDiff summary written to {out_path}")


if __name__ == "__main__":
    main()
