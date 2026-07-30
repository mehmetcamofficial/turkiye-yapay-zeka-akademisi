# EXP-0001 — Trendyol Lexical, Semantic, and Hybrid Retrieval

- hypothesis: semantic retrieval or fusion can improve lexical candidate recall.
- method: identical judgments, group-safe/multi-seed comparisons, bootstrap CIs.
- evidence: V3/V3.1 reports and outputs.
- result: E5 alone underperformed TF-IDF; RRF reached Recall@50 0.831392 versus
  TF-IDF 0.817239 with uncertainty documented.
- decision: Hybrid RRF became the best research retrieval candidate and V4
  retrieval-only policy.
- related task/commit: TASK-0005; `4f168992`, `f70e398a`.

