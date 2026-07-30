# Benchmark Integrity

Protected Copilot assets:

- `copilot_golden.json`
- `canonical_match.py`
- `official_evaluation.py`
- `release_gates.yaml`

Production code must not branch on golden IDs or accepted paths. Golden data,
matcher semantics, evaluator semantics, and release gates change only under an
explicit evaluation-governance task. Record hashes with milestone metrics.

