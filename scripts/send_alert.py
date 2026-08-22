#!/usr/bin/env python3
"""
send_alert.py

Reads data/latest_diff.json (produced by diff_snapshots.py) and posts a
formatted summary to a Slack or Discord webhook, if any changes were found.

Set WEBHOOK_URL as an environment variable (or GitHub Actions secret).
Works with both Slack incoming webhooks and Discord webhooks -- both accept
a simple {"text": "..."} / {"content": "..."} style payload; this script
sends both keys so either platform picks up what it needs.

Usage:
    WEBHOOK_URL=https://hooks.slack.com/services/... python scripts/send_alert.py
"""

import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DIFF_PATH = ROOT / "data" / "latest_diff.json"


def format_message(results: list[dict]) -> str:
    if not results:
        return ""

    lines = ["*Competitor intel update*"]
    for r in results:
        lines.append(f"\n*{r['target']}* — {r['change_count']} change(s)")
        for c in r["changes"][:10]:  # cap so messages don't get huge
            lines.append(f"  • `{c['field']}`: {c['old']} → {c['new']}")
        if r["change_count"] > 10:
            lines.append(f"  ...and {r['change_count'] - 10} more")

    return "\n".join(lines)


def send(webhook_url: str, message: str):
    payload = {"text": message, "content": message}
    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()


def main():
    if not DIFF_PATH.exists():
        print("No diff file found. Run scripts/diff_snapshots.py first.")
        return

    with open(DIFF_PATH) as f:
        results = json.load(f)

    if not results:
        print("No changes detected this run — nothing to alert.")
        return

    message = format_message(results)
    print(message)

    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        print("\n[warn] WEBHOOK_URL not set — printed above but not sent anywhere.")
        return

    send(webhook_url, message)
    print("\nAlert sent.")


if __name__ == "__main__":
    main()
