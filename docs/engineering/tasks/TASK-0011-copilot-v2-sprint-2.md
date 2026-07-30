# TASK-0011 — Copilot V2 Sprint 2

- record_type: reconstructed
- confidence: confirmed
- problem/context: Configured multiword aliases were unreachable token-by-token.
- goal: Activate exact contiguous phrase aliases without substring matching.
- evidence: `17b512fb`, `engineering/copilot/v2-sprint-2-analysis.md`.
- alternatives: new alias, prefix matching, and Turkish stemming rejected.
- decision: exact Unicode-aware token-window matching.
- implementation: phrase expansion helper and boundary/dedup tests.
- validation/metrics: Retrieval@5 23/28; GQ29 new hit; no regressions.
- affected files: retriever, Copilot tests, Sprint 2 report.
- merge: `d7d88438`.
- lessons/follow-up: `geçitleri` correctly does not equal `geçit`.

