# TASK-0010 — Copilot V2 Sprints 1A and 1B

- record_type: reconstructed
- confidence: confirmed
- problem/context: Improve Retrieval@5 with zero regressions.
- goal: Recover low-risk misses using general evidence.
- evidence: `75929c01`, `df3171ed`, `engineering/copilot/v2-sprint-1b.md`.
- alternatives: broad weights, penalties, and diversification rejected.
- decision: alias coverage in 1A; exact filename-stem bonus once per file in 1B.
- implementation: retriever plus focused tests and documentation.
- validation/metrics: 19/28 after 1A; 22/28 after 1B; no regressions.
- affected files: retriever, Copilot tests, README/report.
- related merges: `511f6993`, `c236debc`.
- lessons/follow-up: per-file signals must not multiply across chunks.

