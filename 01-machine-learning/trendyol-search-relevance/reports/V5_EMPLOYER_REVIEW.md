# V5 Employer Review

## Problem

Given a user query and a set of candidate products retrieved by Hybrid RRF fusion, produce a reranked list that places the most relevant products at the top. The reranker must not degrade candidate recall, must run on CPU within bounded latency, and must degrade gracefully on failure.

## System design

V5 places a cross-encoder after the existing Hybrid RRF retrieval stage. Each candidate is paired with the query using a `title_compact_metadata` template (title, category, brand, bounded attributes). Pairs are scored in batches by `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`, pinned at an immutable revision. Scores are min-max normalized per query and replace the original RRF rank as the sort key.

Key design choices:

- **Retrieval/reranking separation** — Reranking operates on an already-retrieved pool and cannot improve recall; it only reorders.
- **Validation-only selection** — Alpha blend weight and document variant were selected on 150 validation queries; the final 150 holdout queries were never used during tuning.
- **Pure cross-encoder policy** — Alpha grid showed pure cross-encoder (alpha=1.0) achieved the highest validation NDCG@10. Hybrid blend was not selected.
- **Lazy loading** — The model and tokenizer are loaded only when the V5 page executes, keeping startup time low.
- **Deterministic inference** — Fixed batch order, seed, and model revision produce identical scores across runs.

## Measurable result

| Metric | Hybrid RRF | Cross-Encoder | Delta |
|---|---|---|---|
| NDCG@10 | 0.6121 | 0.6785 | +0.0664 (+10.8%) |
| MRR | 0.7176 | 0.7720 | +0.0544 (+7.6%) |

- Paired NDCG@10 95% CI: [0.0368, 0.0960] — improvement is statistically detectable at the query level.
- 74 of 150 queries improved, 42 worsened, 34 unchanged.
- Candidate Recall@20 was preserved at 0.6795 in both policies.

## Engineering trade-offs

- **Pool size** — Pool 20 was selected for the live demo; pool 100 was benchmarked but increases latency without changing the governance conclusion.
- **Batch size** — Batch 8 was selected as the best throughput/latency trade-off. Batch 16 added latency without proportional throughput gain on CPU.
- **Cold start** — ~1.6 s for first model load (tokenizer + model download); subsequent loads use HuggingFace cache.
- **Score semantics** — Raw logits, not probabilities. Logits are compared only within the same query; cross-query comparison is not meaningful.
- **Latency budget** — Warm pool-20 p95 ~433 ms, mean ~313 ms on CPU. Acceptable for a bounded local demo; not a production SLA.

## Failure modes

| Failure | Behavior |
|---|---|
| Model load timeout | Fallback to retrieval-only order |
| Inference exception | Fallback to retrieval-only order |
| Empty candidate pool | Pipeline returns empty result (no scores to fabricate) |
| Unknown document variant | Raises explicit `ValueError` (fail fast, not silently) |

## Runtime design

The cross-encoder runs in the Streamlit process alongside the E5 semantic encoder. XGBoost remains in its own persistent worker process to avoid OpenMP runtime conflicts. Model and tokenizer are cached via `st.cache_resource` with explicit hash-based invalidation. Memory was measured as stable after warm-up (no uncontrolled growth across repeated inference cycles).

## What remains before production

- Online A/B testing with business metrics (CTR, conversion, revenue)
- GPU acceleration for acceptable latency at catalogue scale
- Fine-tuning on domain-specific query-product pairs
- Calibration of raw logits into interpretable relevance scores
- Robustness testing across query segments (exact brand match, rare categories, misspellings)
- Monitoring for semantic drift as the catalogue evolves
