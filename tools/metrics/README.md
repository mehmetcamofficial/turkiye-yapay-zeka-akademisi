# Metrics Documentation Tooling

Run from the repository root:

```bash
python tools/metrics/validate_metrics_history.py
python tools/metrics/generate_metrics_dashboard.py
```

The tools read `metrics/history.json` and generate deterministic Markdown and
self-contained HTML. They use only the Python standard library, no network,
analytics, external CSS, or JavaScript.

