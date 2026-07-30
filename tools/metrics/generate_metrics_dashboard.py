#!/usr/bin/env python3
"""Generate deterministic Markdown and HTML metric dashboards."""

from __future__ import annotations

from html import escape
from pathlib import Path

from validate_metrics_history import ROOT, load_history, validate

OUTPUT_MD = ROOT / "metrics/dashboard.md"
OUTPUT_HTML = ROOT / "metrics/dashboard.html"
HEADER = "Generated from metrics/history.json; do not edit directly."


def display(record: dict) -> str:
    value = record["value"]
    if value is None:
        return "Unknown"
    denominator = record["denominator"]
    return f"{value}/{denominator}" if denominator is not None else str(value)


def main() -> int:
    data = load_history()
    errors = validate(data)
    if errors:
        raise SystemExit("\n".join(errors))
    records = sorted((r for r in data["records"] if r["confidence"] == "confirmed"), key=lambda r: (r["date"], r["phase"], r["metric"], r["commit"]))
    copilot = [r for r in records if r["phase"] == "copilot" and r["metric"] == "retrieval_at_5"]

    md = [f"<!-- {HEADER} -->", "# Metrics Dashboard", "", "> Metrics from unrelated tasks are not directly comparable.", "", "## Copilot Retrieval@5 evolution", "", "| Date | Version | Value | Commit | Task | Source |", "|---|---|---:|---|---|---|"]
    for r in copilot:
        md.append(f'| {r["date"]} | {r["version"] or "Unknown"} | {display(r)} | `{r["commit"]}` | {r["task"]} | `{r["source"]}` |')
    md.extend(["", "## Confirmed repository metrics", "", "| Date | Phase | Metric | Value | Commit | Task | Confidence | Source |", "|---|---|---|---:|---|---|---|---|"])
    for r in records:
        md.append(f'| {r["date"]} | {r["phase"]} | {r["metric"]} | {display(r)} | `{r["commit"]}` | {r["task"]} | {r["confidence"]} | `{r["source"]}` |')
    OUTPUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    rows = "\n".join(
        "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in (r["date"], r["phase"], r["metric"], display(r), r["commit"], r["task"], r["confidence"], r["source"])) + "</tr>"
        for r in records
    )
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Repository Metrics Dashboard</title><style>body{{font-family:system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#18212b}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ccd4dc;padding:.5rem;text-align:left}}th{{background:#eef3f7}}caption{{text-align:left;font-weight:700;margin:1rem 0}}code{{background:#eef3f7;padding:.1rem .25rem}}</style></head>
<body><!-- {HEADER} --><h1>Repository Metrics Dashboard</h1><p>Confirmed records only. Metrics from unrelated tasks are not directly comparable. Null values are shown as Unknown.</p>
<table><caption>Confirmed metric history</caption><thead><tr><th>Date</th><th>Phase</th><th>Metric</th><th>Value</th><th>Commit</th><th>Task</th><th>Confidence</th><th>Source</th></tr></thead><tbody>{rows}</tbody></table></body></html>'''
    OUTPUT_HTML.write_text(html + "\n", encoding="utf-8")
    print(f"Generated dashboards from {len(records)} confirmed records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
