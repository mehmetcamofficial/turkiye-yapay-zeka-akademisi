# TASK-0008 — AI Project Copilot V1

- record_type: reconstructed
- confidence: confirmed
- problem/context: Repository knowledge was spread across code and documents.
- goal: Add a read-only grounded assistant with citations and release gates.
- evidence: `3e9be63d`, `7de65f19`, source/tests/project docs.
- alternatives: external/ungrounded generation rejected by implemented design;
  original rationale requires confirmation.
- decision: deterministic local indexing/retrieval and extractive answers.
- implementation: Copilot package, page, canonical benchmark.
- validation: V1 public tests/evaluation; exact historical count in V1 records.
- affected files: `portfolio/copilot/`, page, tests, evaluation.
- related PR: #15 merge `ad77d40a`.
- lessons/follow-up: freshness must not depend on ignored local artifacts.

