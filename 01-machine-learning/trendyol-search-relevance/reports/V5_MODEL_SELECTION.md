# V5 Model Selection

## Selection Criteria

- NDCG@10 improves credibly or remains non-degrading
- MRR improves credibly or remains non-degrading
- Candidate Recall@50 preserved
- Most seeds stable
- Paired CI does not indicate material degradation
- Exact brand/model-code performance does not materially collapse
- Latency acceptable for bounded demo
- Memory stable after warm-up
- Fallback tests pass
- Five-cycle coexistence passes

## Models Considered

1. **cross-encoder/mmarco-mMiniLMv2-L12-H384-v1** — 12 layers, 384 hidden,
   multilingual, trained on mMARCO, 117.6M params
2. **BAAI/bge-reranker-v2-m3** — 12 layers, multilingual, strong reranking
3. **cross-encoder/stsb-distilroberta-base** — English-only, not preferred

## Models Actually Evaluated

**cross-encoder/mmarco-mMiniLMv2-L12-H384-v1** — smoke test completed.

## Selected Model

**cross-encoder/mmarco-mMiniLMv2-L12-H384-v1**

Rationale:
- Multilingual with Turkish support (mMARCO training)
- 117.6M parameters (small enough for CPU)
- Apache-2.0 license
- Smoke test passed: finite scores, deterministic inference
- Compatible with existing environment (torch 2.13.0, transformers 4.57.6)

## Exact Model ID

cross-encoder/mmarco-mMiniLMv2-L12-H384-v1

## Exact Immutable Model Revision

1427fd652930e4ba29e8149678df786c240d8825

## Verified License

Apache-2.0 (verified from HuggingFace model metadata)

## Architecture

XLMRobertaForSequenceClassification

## Parameter Count

117,641,089

## Maximum Sequence Length

514 (max_position_embeddings)

## Device

CPU (default). MPS available but not used for small batches due to transfer overhead.

## Score Semantics

Raw logits (regression output). NOT probabilities. NOT calibrated.

## Document Variant

title_compact_metadata (Query + title + category + brand + bounded attributes)

Selected via NDCG@10 on 150 validation queries (seed 42, pool 20, pure CE).

Validation variants NDCG@10:
- title_only: 0.4920
- title_category: 0.5086
- title_category_brand: 0.6780
- title_compact_metadata: 0.6926 (selected)

## Candidate Pool Sizes Tested

- 20 (live demo default, selected)
- 50 (live demo alternative)
- 100 (benchmark only)

## Selected Live Candidate Pool

**20** — Balances quality and latency for bounded local demo.

## Batch Sizes Tested

- 1, 4, 8, 16

## Selected Batch Size

**8** — Best throughput/latency trade-off.

## Score Normalization

Min-max normalization per query for hybrid blend. Raw logits are NOT
labeled as probabilities.

## Alpha Selection

Alpha grid evaluated on 150 validation queries (selected variant, pool 20).

Validation alpha NDCG@10:
- 0.50: 0.6843
- 0.65: 0.6878
- 0.80: 0.6907
- 0.90: 0.6878
- 1.00: 0.6926 (selected, pure cross-encoder)

Selected policy: pure cross-encoder (alpha=1.0). Hybrid blend was not
selected because pure cross-encoder achieved the highest NDCG@10 on
the validation set.

## Smoke Test Results

- Tokenizer load: 5.56s
- Model load: 13.23s
- First inference (10 pairs, batch 8): 124.3ms
- Second inference (deterministic): 33.2ms
- Scores finite: True
- Score range: [1.2623, 2.9626]
- Deterministic: True
- No XGBoost import: PASS

## Governance Decision

**Best Reranking Research Candidate · Not Production Promoted**

On the frozen 150-query V5 holdout (seed 42, pool 20):

- Hybrid RRF baseline: NDCG@10 = 0.6121, MRR = 0.7176
- Pure cross-encoder: NDCG@10 = 0.6785, MRR = 0.7720
- Absolute NDCG@10 gain: +0.0664
- Relative NDCG@10 gain: +10.8%
- Paired 95% CI: [0.0368, 0.0960]
- Improved: 74, Unchanged: 34, Worsened: 42

The cross-encoder is an experimental reranker. It does not improve candidate
recall. Candidate Recall@20 is a retrieval property preserved during
reranking of the same pool.
