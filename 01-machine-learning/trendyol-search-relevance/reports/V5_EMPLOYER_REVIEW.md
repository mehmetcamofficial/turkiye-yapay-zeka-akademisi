# V5 Employer Review

## Recruiter View

Can a recruiter understand that Mehmet built:

- **Lexical retrieval** — TF-IDF and BM25 candidate discovery (V3/V4)
- **Semantic retrieval** — E5 multilingual embedding search (V3/V4)
- **Hybrid fusion** — RRF candidate fusion with deterministic tie-breaking (V4)
- **Cross-encoder reranking** — V5 query-document pair scoring for top-of-list quality
- **End-to-end orchestration** — Versioned 4.0 contracts, validation, normalization,
  retrieval, fusion, reranking, fallback, and serialization
- **Fallback-safe runtime** — Explicit degradation to retrieval-only when components fail

## ML Engineer View

Can they inspect:

- **Candidate generation** — Hybrid RRF with k=20, pool=100
- **Pair construction** — Deterministic query-document pairs with bounded text templates
- **Model revision** — Pinned HuggingFace revision for reproducibility
- **Batching** — Batch sizes 1/4/8/16 with latency/throughput measurement
- **Score normalization** — Min-max per-query normalization for hybrid blend
- **Validation-only selection** — Alpha grid tuned on validation groups only
- **Holdout evaluation** — Final evaluation on unseen query groups
- **Paired bootstrap** — 95% confidence intervals for NDCG@10 and MRR

## Search Engineer View

Can they distinguish:

- **Retrieval recall** — Candidate Recall@50 preserved (reranker does not affect recall)
- **Reranking quality** — NDCG@10 and MRR improvements from cross-encoder
- **Candidate pool** — Pool sizes 20/50/100 evaluated
- **Top-k metrics** — Recall@10/20/50/100, Precision@10, MAP@10
- **Exact-match failure** — Cross-encoder may demote brand/model-code queries
- **Semantic drift** — Cross-encoder may fix or worsen semantic mismatches
- **Latency/quality trade-off** — Pool 20 for live demo, pool 100 for benchmark

## Platform Engineer View

Can they inspect:

- **Lazy model loading** — Cross-encoder loaded only when V5 page executes
- **Cache reuse** — Model and tokenizer cached after first load
- **Memory growth** — Peak and ending RSS measured; no uncontrolled growth
- **Timeout fallback** — Cross-encoder timeout preserves Hybrid RRF order
- **Native runtime boundaries** — PyTorch in Streamlit, XGBoost in isolated worker
- **Worker coexistence** — E5, cross-encoder, and XGBoost worker coexist safely

## Governance

- **Role**: Experimental Cross-Encoder Reranker
- **Status**: Best Reranking Research Candidate (if supported by metrics)
- **Promotion**: Not Production Promoted
- **Scope**: Bounded 5,000-product demo, 63,841-product offline evaluation
- **SLA**: No production SLA claimed
- **Business impact**: No online A/B test or measured business impact
