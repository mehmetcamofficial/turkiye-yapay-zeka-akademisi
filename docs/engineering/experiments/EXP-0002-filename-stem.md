# EXP-0002 — Exact Filename-Stem Signal

- hypothesis: exact query-token/filename-stem equality is stronger than
  incidental path overlap.
- method: counterfactual bonus modeling and focused equality tests.
- evidence: `engineering/copilot/v2-sprint-1b.md`.
- result: bonus 1.0, applied once per file, recovered GQ04/GQ07/GQ21 without
  regression; 0.9 and per-chunk application were rejected.
- decision: implement fixed per-file exact-stem signal.
- related task/commit: TASK-0010; `df3171ed`.

