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

title_category_brand (Query + title + category + brand)

## Candidate Pool Sizes Tested

- 20 (live demo default)
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

**Experimental Cross-Encoder Reranker · Not Production Promoted**

The cross-encoder is an experimental reranker. It does not improve candidate
recall. It may improve top-of-list ranking quality (NDCG@10, MRR) but this
must be verified with full holdout evaluation.
