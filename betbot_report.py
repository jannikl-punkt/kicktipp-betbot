"""Render a betbot run report as Markdown from predictions.json.

Deterministic, no AI involved. The research step writes predictions.json,
the tipping step places the bets, and this script turns the same file into
a comment body for the betbot-report issue.

Usage:
    python betbot_report.py <titel> [predictions.json]
e.g.
    python betbot_report.py "Auto-Tipps" predictions.json
"""

import json
import os
import sys
from datetime import datetime


def _tip_and_reason(value):
    """Accept both [h, a] and {"tip": [h, a], "reason": "..."}."""
    if isinstance(value, dict):
        return value.get("tip"), value.get("reason", "")
    return value, ""


def render(title, predictions):
    today = datetime.now().strftime("%d.%m.%Y %H:%M")
    lines = [f"## 🤖 Betbot – {title} ({today})", ""]
    if not predictions:
        lines.append("_Keine Spiele in diesem Lauf getippt._")
        return "\n".join(lines)

    lines.append("| Spiel | Tipp | Kurzbegründung |")
    lines.append("|-------|------|----------------|")
    for match, value in predictions.items():
        tip, reason = _tip_and_reason(value)
        tip_str = f"{tip[0]}:{tip[1]}" if tip else "?"
        lines.append(f"| {match} | {tip_str} | {reason or '–'} |")
    return "\n".join(lines)


def main():
    title = sys.argv[1] if len(sys.argv) > 1 else "Tipps"
    path = sys.argv[2] if len(sys.argv) > 2 else "predictions.json"
    predictions = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            predictions = json.load(f)
    print(render(title, predictions))


if __name__ == "__main__":
    main()
