# Evaluation Architecture

Predictive projects preserve train/validation/test outputs. Trendyol research
adds group-safe splits, multi-seed summaries, bootstrap intervals, Recall@K,
NDCG, MRR, latency, and artifact governance.

Repository search uses golden queries and quality gates. Copilot's canonical
path is `evaluation/search/official_evaluation.py`, with accepted-target logic
in `canonical_match.py` and protected release thresholds in
`release_gates.yaml`. Citation validity, precision, concept recall, intent
accuracy, unsupported claims, and Retrieval@5 are measured separately.

