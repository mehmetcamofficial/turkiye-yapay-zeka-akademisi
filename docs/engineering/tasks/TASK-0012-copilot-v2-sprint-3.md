# TASK-0012 — Copilot V2 Sprint 3

- record_type: reconstructed
- confidence: confirmed
- problem/context: Explicit file-location wording was forced to locate-symbol.
- goal: Prefer `find_file` unless a declaration cue is present.
- evidence: `e3bbaf43`, `engineering/copilot/v2-sprint-3-analysis.md`.
- alternatives: Turkish morphology and compound-symbol changes modeled/rejected.
- decision: generic file-location intent precedence.
- implementation: intent classifier constants/guard and focused tests.
- validation/metrics: Retrieval@5 24/28, intent 29/30, concept recall 39/48;
  GQ12 new hit, no regressions.
- affected files: intent classifier, Copilot tests, report.
- merge: `ae7d9404`.
- lessons/follow-up: fix semantic routing before changing ranking weights.

