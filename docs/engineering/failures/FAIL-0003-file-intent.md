# FAIL-0003 — Explicit File Query Misclassified

- observed: GQ12 classified as `locate_symbol`; accepted files ranked #6/#7.
- expected: explicit file-location wording routes to `find_file`.
- impact: Retrieval@5 miss and intent error.
- evidence: Sprint 3 report and commit `e3bbaf43`.
- root cause: duplicated high-priority intent overrides and generic symbol collision.
- attempted approaches: morphology, compound-symbol, and evidence models compared.
- resolution: generic file-location precedence with declaration exceptions.
- prevention/lesson: test routing semantics before altering scoring.

