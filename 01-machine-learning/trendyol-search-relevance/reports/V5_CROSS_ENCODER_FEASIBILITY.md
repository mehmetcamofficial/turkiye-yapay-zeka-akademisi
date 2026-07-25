# V5 Cross-Encoder Reranker Feasibility

## Objective

Test whether a small multilingual cross-encoder can improve top-of-list
ranking quality (NDCG@10, MRR) while preserving candidate recall from the
verified V4 Hybrid RRF pipeline.

## Usable Candidate Fields

From the V4 Hybrid RRF candidate records and the bounded 5,000-product live
catalogue:

- query (normalized Turkish text)
- item_id (stable identifier)
- title (Turkish product title)
- category (hierarchical path)
- brand (string)
- gender, age_group (bounded strings)
- attributes (key-value string, bounded)
- source retrievers (lexical, semantic)
- fused rank (RRF)
- original retrieval score
- relevance label where available (binary 0/1)

## Label Availability

- File: `outputs/v3/evaluation_judgments.csv`
- Rows: 52,423 query-product pairs
- Labels: binary `relevance_label` (0 = Alakasız, 1 = Alakalı)
- Groups: 1,000 complete query groups
- Seeds: 42, 52, 62, 72, 82 (group-safe)
- Split: train/validation/holdout via `v3_evaluate.splits`
- Label quality: bounded competition snapshot; incomplete judgments for
  non-candidate items

## Pair-Construction Method

Construct query-document pairs from Hybrid RRF candidate pools (pool sizes
20, 50, 100). Document text is built using bounded templates:

- A. title only
- B. title + category
- C. title + category + brand
- D. title + compact metadata (attributes truncated to 240 chars)

Pairs are deterministic: same query + same candidate pool always produces the
same pair set.

## Candidate Coverage

- 1,000 queries × Hybrid RRF pool of 100 = 100,000 candidate pairs
- Pool sizes 20 and 50 yield 20,000 and 50,000 pairs respectively
- All pairs have query text, title, category, brand, and relevance label
  where judgments exist

## Expected Compute Cost

- Cross-encoder inference: ~1–5 ms per pair on CPU for small models
- 100 pairs at pool=100: ~0.1–0.5 seconds per query
- Full 1,000-query evaluation: ~100–500 seconds (offline)
- Live demo (pool=20): ~0.02–0.1 seconds per query

## Expected Memory Cost

- Model weights: 100–250 MB for small cross-encoders
- Tokenizer: ~10 MB
- Input batch tensors: <10 MB for pool=100
- Total additional memory: <300 MB
- Existing V4 peak RSS: ~1,099 MB
- Estimated V5 peak RSS: ~1,300–1,400 MB (within reasonable bounds)

## Candidate Pool Limits

- Live demo: pool 20 or 50 (latency-bounded)
- Offline evaluation: pool 20, 50, 100
- Pool 100 is benchmark-only if latency is unreasonable for live demo

## Runtime Risks

1. **CPU inference latency**: Small cross-encoders on CPU may exceed 500 ms
   for pool=100. Mitigation: default to pool=20 or 50 for live demo.
2. **Memory pressure**: Cross-encoder + E5 semantic model + XGBoost worker
   must coexist. Streamlit main process loads PyTorch but not XGBoost.
3. **MPS availability**: MPS is available but cross-encoder inference on
   MPS may be slower than CPU for small batches due to transfer overhead.
   CPU is the default; MPS is optional.
4. **Model download**: First run downloads model weights. Must be cached
   locally and pinned to a revision.
5. **Tokenizer cache**: Must be cached and reused.

## Deployment Constraints

- Streamlit main process: PyTorch + cross-encoder + E5 (no XGBoost)
- XGBoost worker: isolated persistent JSON worker (unchanged)
- Registry and Artifact Health: metadata-first (no model load during render)
- No eager XGBoost import in Streamlit
- No deep native reload during page render

## Recommended Model Shortlist

1. **cross-encoder/mmarco-mMiniLMv2-L12-H384-v1** — 12 layers, 384 hidden,
   multilingual, trained on mMARCO, good Turkish support
2. **cross-encoder/mmarco-mMiniLMv2-L6-H384-v1** — 6 layers, 384 hidden,
   lighter, faster, multilingual
3. **BAAI/bge-reranker-v2-m3** — 12 layers, multilingual, strong reranking
   performance, supports 100+ languages
4. **cross-encoder/stsb-distilroberta-base** — English-only fallback only if
   Turkish support is insufficient (not preferred)

## Final Proposed Architecture

```
User Query
→ Query Validation (4.0 contract)
→ Query Normalization
→ TF-IDF Retrieval (V4 verified)
→ E5 Semantic Retrieval (V4 verified)
→ Hybrid RRF Candidate Fusion (k=20, pool=100)
→ Cross-Encoder Reranking (top-N candidates)
→ Deterministic Top-k Response
```

The cross-encoder reranks only the retrieved candidate pool. It does not
affect retrieval generation. Candidate Recall@50 is preserved when reranking
the same pool.
