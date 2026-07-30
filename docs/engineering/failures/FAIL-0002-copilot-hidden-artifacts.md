# FAIL-0002 — Copilot Hidden Generated Dependencies

- observed: early fresh checkouts depended on ignored manifests/generated output.
- expected: canonical evaluation works using tracked source and runtime generation.
- impact: V1 public reproducibility blocker.
- evidence: optional manifest logic in `official_evaluation.py`, V1 history.
- root cause: generated provenance/output was treated as an input.
- attempted approaches: optional loading, canonical recreation, fresh-checkout tests.
- resolution: canonical evaluation no longer requires ignored benchmark output.
- prevention/lesson: generated results are outputs, never hidden inputs.

