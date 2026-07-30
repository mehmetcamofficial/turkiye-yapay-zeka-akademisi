# ADR-0001 — Persisted Artifact Runtime

- status: accepted
- context: Portfolio pages need bounded inference without training at import.
- decision: Training pipelines persist models/reports; services load them lazily
  and expose unavailable states when required assets are absent.
- evidence: model pickles, training scripts, `portfolio/loaders.py`, runtime fixes.
- alternatives: runtime retraining; rejected by implemented architecture, but
  original rationale is inferred from repository evidence.
- consequences: repeatable UI and faster startup; artifact compatibility risk.
- risks: ignored semantic caches and stale artifacts can block tests/runtime.
- related code/tasks: loaders/services; TASK-0002–TASK-0005.
- author-confirmation status: rationale strongly inferred, not directly recorded.

