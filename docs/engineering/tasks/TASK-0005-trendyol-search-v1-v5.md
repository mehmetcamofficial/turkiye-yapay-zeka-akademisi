# TASK-0005 — Trendyol Search V1–V5

- record_type: reconstructed
- confidence: confirmed
- problem/context: Separate relevance classification, retrieval, and reranking.
- goal: Evaluate a governed end-to-end product search pipeline.
- evidence: project README/reports/tests and commits `377fbe8a`, `35357283`,
  `4f168992`, `f70e398a`, `4db73a6b`.
- alternatives: linear/tree/XGBoost models, TF-IDF, BM25, E5, RRF, cross-encoder.
- decision: V4 Hybrid RRF retrieval-only; V5 best reranking research candidate.
- implementation: versioned evaluation, artifacts, services, pages, fallbacks.
- validation/metrics: V5 NDCG@10 0.6785 and MRR 0.7720.
- affected files: `trendyol-search-relevance/`, related portfolio services/pages.
- related PRs: #4–#8.
- lessons/follow-up: non-promotion is an engineering result, not a failure to report.

