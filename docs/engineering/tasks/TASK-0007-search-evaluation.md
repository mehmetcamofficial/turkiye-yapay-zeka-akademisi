# TASK-0007 — Search Evaluation Framework

- record_type: reconstructed
- confidence: confirmed
- problem/context: Search quality needed reproducible evidence and release gates.
- goal: Add golden queries, metrics, reports, ranking diffs, and quality gates.
- evidence: commit `78942d7b`; `evaluation/search/`; tests.
- alternatives: manual review alone was insufficient (inferred from evidence).
- decision: deterministic offline evaluation with protected inputs.
- implementation: dataset/schema/evaluator/metrics/CLI/report/gates.
- validation: search evaluation and mutation tests.
- affected files: `evaluation/search/`, `tests/test_search_evaluation.py`.
- lessons/follow-up: preserve denominator and matcher semantics.

