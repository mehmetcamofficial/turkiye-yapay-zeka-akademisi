# Trendyol Data Profile

- Status: implemented profiling pipeline with tracked reports.
- Entry point: `02-data-science/trendyol-profile/run_profile.py`.
- Pipeline: inventory, schema inspection, quality checks, numeric/categorical
  summaries, duplicates, missingness, text length, and Markdown reporting.
- UI: portfolio Trendyol Profile and data-science overview pages.
- Models: none; this is a statistical/data-quality subsystem.
- Outputs: CSV/JSON/Markdown summaries under `outputs/`.
- Limitation: raw source files may be local/ignored; provenance is bounded by
  `DATA_SOURCE.md`.

