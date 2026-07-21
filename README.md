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
| Trendyol Search & Product Intelligence | Relevance classification and ranking research | V1 champion + experimental challengers | term-group split, NDCG, bootstrap CI and governance |

## Featured evidence: Trendyol

The stable V1 uses word/character TF-IDF, explicit similarity features and Logistic Regression on a deterministic 100,000-row sample. `term_id` validation overlap is zero: F1 `0.626047`, precision `0.7406`, recall `0.5422`, PR AUC `0.716490`.

V2 challengers were not promoted. Random Forest holdout F1 was `0.638384` with PR AUC `0.690896`; the XGBoost ranker reached NDCG@10 `0.804408`, below the leakage-safe first-stage `0.847707`. The query-bootstrap delta was `-0.043298`, 95% CI `[-0.096936, 0.013904]`.

V2.1 Offline Evaluation used 1,000 complete groups across five seeds. HistGradientBoosting was the Best Research Candidate: mean F1 `0.753935`, standard deviation `0.006349`, 95% CI `[0.746053, 0.761817]`. It was Not Promoted because V1 uses a Different historical split and Direct superiority is not established; the selected HGB object was not persisted because it was no longer available without retraining. The Bounded Candidate Sample baseline mean NDCG@10 was `0.871041`; `rank_ndcg_topk` delta `-0.007469`, CI `[-0.023354, 0.008416]`; `rank_pairwise` delta `-0.002659`, CI `[-0.010400, 0.005082]`. Robust hard-negative F1 values were original `0.617633`, weighted `0.476246`, enriched `0.420103`, weighted+enriched `0.200427`.

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
Champion → Challenger → Holdout → Confidence Interval → Decision
                                                ↘ Promote / retain
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

The Streamlit experience is a portfolio application, not evidence of commercial production traffic. Trendyol results use a public competition snapshot and bounded candidates; they do not establish online search impact, fairness, causal business value or catalogue-wide retrieval quality. V2.1 remains uncommitted experimental work until review.
