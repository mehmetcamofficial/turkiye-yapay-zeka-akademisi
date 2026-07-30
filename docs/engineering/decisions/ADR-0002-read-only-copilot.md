# ADR-0002 — Read-Only Repository-Grounded Copilot

- status: accepted
- context: A repository assistant must answer from evidence without mutating or
  exposing repository state.
- decision: Allowlisted local indexing, extractive answers, validated citations,
  repository path boundaries, secret exclusion, and no shell execution.
- evidence: Copilot indexer/answer/citation/safety modules and tests.
- alternatives: ungrounded generation or write-capable agent; not implemented.
- consequences: inspectable answers and bounded risk; limited synthesis.
- risks: corpus/chunking gaps and stale indexes.
- related code/tasks: `portfolio/copilot/`; TASK-0008.
- author-confirmation status: confirmed by implementation and tests.

