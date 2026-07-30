# ADR-0003 — Protected Zero-Regression Evaluation

- status: accepted
- context: Retrieval gains can displace previously correct evidence.
- decision: Protect golden/matcher/evaluator/gates and accept narrow retrieval
  changes only after canonical new-hit/regression comparison.
- evidence: release gates, canonical matcher, Sprint 1B–3 reports and tests.
- alternatives: global weight tuning and benchmark-specific paths were rejected.
- consequences: slower but auditable improvements; some misses remain deferred.
- risks: benchmark over-focus if corpus health is ignored.
- related tasks: TASK-0010–TASK-0012.
- author-confirmation status: confirmed.

