# AI & Data Intelligence Platform

End-to-end machine-learning systems across classification, regression, NLP, search relevance, model evaluation and model operations. Designed and developed by Mehmet Cam as a production-oriented AI engineering portfolio.

[Portfolio](https://mehmetcamofficial.com.tr/) · [LinkedIn](https://www.linkedin.com/in/mehmet-cam09/) · [GitHub](https://github.com/mehmetcamofficial)

## Live capabilities

- Single and bounded batch inference for churn, housing, sentiment and query-product relevance
- Artifact-driven Model Registry and cached Artifact Health checks
- Group-safe validation, deterministic sampling and explicit leakage audits
- Classification, calibration, ranking, hard-negative and query-bootstrap evaluation
- Semantic HTML tables without Streamlit Arrow-backed table components

## Project map

| Project | Task | Artifact | Evidence |
|---|---|---|---|
| Customer Churn Intelligence | Binary classification | Persisted pipeline | ROC AUC, recall and batch inference |
| Housing Value Forecasting | Regression | Persisted pipeline | RMSE, residual analysis and local California Housing data |
| Sentiment Intelligence | English NLP classification | Persisted pipeline | UCI source, TF-IDF terms and live inference |
| Trendyol Search & Product Intelligence | Relevance classification, ranking and retrieval research | V1 champion + V2–V5 experimental challengers | term-group split, NDCG, bootstrap CI and governance |

## Featured evidence: Trendyol

The stable V1 uses word/character TF-IDF, explicit similarity features and Logistic Regression on a deterministic 100,000-row sample. `term_id` validation overlap is zero: F1 `0.626047`, precision `0.7406`, recall `0.5422`, PR AUC `0.716490`.

V2 challengers were not promoted. Random Forest holdout F1 was `0.638384` with PR AUC `0.690896`; the XGBoost ranker reached NDCG@10 `0.804408`, below the leakage-safe first-stage `0.847707`. The query-bootstrap delta was `-0.043298`, 95% CI `[-0.096936, 0.013904]`.

V2.1 Offline Evaluation used 1,000 complete groups across five seeds. HistGradientBoosting was the Best Research Candidate: mean F1 `0.753935`, standard deviation `0.006349`, 95% CI `[0.746053, 0.761817]`. It was Not Promoted because V1 uses a Different historical split and Direct superiority is not established; the selected HGB object was not persisted because it was no longer available without retraining. The Bounded Candidate Sample baseline mean NDCG@10 was `0.871041`; `rank_ndcg_topk` delta `-0.007469`, CI `[-0.023354, 0.008416]`; `rank_pairwise` delta `-0.002659`, CI `[-0.010400, 0.005082]`. Robust hard-negative F1 values were original `0.617633`, weighted `0.476246`, enriched `0.420103`, weighted+enriched `0.200427`.

V3/V3.1 adds candidate retrieval as a separate experimental layer. Five group-safe seeds evaluate 1,000 complete queries against a deterministic 63,841-product bounded broad catalogue with 100% judged-relevant-item availability. Combined enriched TF-IDF reaches Recall@50 `0.817239`; standalone multilingual E5 Small reaches `0.725147` and is not selected. Validation-selected RRF hybrid reaches Recall@50 `0.831392`, Recall@100 `0.900276`, NDCG@10 `0.618014` and MRR `0.713382`. Its Recall@50 delta CI versus TF-IDF is `[-0.006188, 0.034494]`, so it is a Best Research Candidate but Not Promoted. The live 5,000-product demo uses cached lexical and real local semantic indexes.

V4 adds one bounded end-to-end contract: validated query → retrieval → fixed `RRF k=20` fusion → provenance → optional unchanged V1 scoring → deterministic policy/fallback → response. Selected policy is Hybrid RRF retrieval-only (pool 100, item-id tie-break) at Recall@50 `0.834640`, NDCG@10 `0.619136` and MRR `0.713543`. The verified V1 classifier remains valuable for relevance classification, but applying its probability directly as a reranking policy degraded Recall@50, NDCG@10 and MRR. V4 is an offline research pipeline, not production promoted.

V5 adds experimental cross-encoder reranking. `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` revision `1427fd65` is the selected model, scoring Hybrid RRF candidates (pool 20) with `title_compact_metadata` document text. The pure cross-encoder policy was selected via validation alpha grid (alpha=1.0). On the frozen 150-query V5 holdout, NDCG@10 increased from `0.6121` to `0.6785`, an absolute gain of `+0.0664` (+10.8%). The paired 95% CI was `[0.0368, 0.0960]`; 74 queries improved, 42 worsened. V5 is a Best Reranking Research Candidate, Not Production Promoted.

## Architecture

```text
Data Sources → Validation → Feature Engineering → Training
             → Evaluation → Artifact Registry → Live Inference → Monitoring
```

```text
Query → Bounded Candidates → Lexical Scoring → V1 Probability
      → Experimental Ranker → Ranked Results
```

```text
Query → Normalization ─→ Lexical Retrieval ─┐
                    └→ Semantic (planned) ──┤→ Candidate Fusion
                                            → V1 Scoring → Ranking → Results
```

```text
Champion → Challenger → Holdout → Confidence Interval → Decision
                                                ↘ Promote / retain

```text
Query → Hybrid RRF (pool 20) → Cross-Encoder → Reranked Results
                              → (or fallback: retrieval-only)
```
```

## Run

```bash
./.venv/bin/python -m streamlit run 01-machine-learning/portfolio_app.py \
  --server.fileWatcherType none --server.headless true
```

## Verify

```bash
./.venv/bin/python -m compileall -q 01-machine-learning 02-data-science
PYTHONPATH=01-machine-learning/trendyol-search-relevance \
  ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/inference.py
git diff --check
```

See [Repository Guide](01-machine-learning/REPOSITORY_GUIDE.md) for structure, reproducibility, V1/V2/V2.1 boundaries and limitations.

## Status and limitations

The Streamlit experience is a portfolio application, not evidence of commercial production traffic. Trendyol results use a public competition snapshot and bounded candidates; they do not establish online search impact, fairness, causal business value or catalogue-wide retrieval quality.
