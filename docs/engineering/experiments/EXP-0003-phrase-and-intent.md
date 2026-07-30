# EXP-0003 — Phrase Activation and File-Intent Routing

- hypothesis: dormant exact phrase aliases and explicit file intent can recover
  misses without global scoring changes.
- method: strict boundary tests and canonical counterfactual ranking.
- evidence: Sprint 2/3 engineering reports.
- result: GQ29 and GQ12 became new hits in successive sprints; no regressions.
- decision: retain strict phrase equality and explicit file-location precedence.
- related tasks/commits: TASK-0011/TASK-0012; `17b512fb`, `e3bbaf43`.

