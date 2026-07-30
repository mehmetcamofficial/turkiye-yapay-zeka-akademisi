# FAIL-0001 — Missing Semantic Runtime Assets

- observed: semantic tests/runtime fail when ignored model snapshots are absent.
- expected: controlled availability or a complete local snapshot.
- impact: repository-root workspace tests are not fully portable.
- evidence: semantic loader/tests and Sprint 2/3 validation output.
- root cause: model weights are intentionally not fully tracked.
- attempted approaches: local-only loading and graceful service failures.
- status: unresolved environment dependency.
- prevention/lesson: separate public portable tests from asset-required checks.

