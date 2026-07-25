# Employer-Friendly Repository Guide

## What is here

This repository contains four runnable machine-learning case studies—churn classification, California housing regression, English sentiment classification, and Trendyol query-product relevance—plus data-science assignments and an artifact-driven Streamlit portfolio.

## Start the platform

```bash
./.venv/bin/python -m streamlit run 01-machine-learning/portfolio_app.py --server.fileWatcherType none
```

Projects live under `01-machine-learning/`; raw Trendyol sources stay ignored under `02-data-science/midterm-assignment/data/`. Models are under each project's `models/`, saved metrics under `outputs/`, and provenance/evaluation documentation under `reports/`.

## Reproduce and verify

Training scripts prefer local data. Run `python -m compileall`, project tests and fresh-process `joblib.load` checks before using artifacts. The Registry reads actual paths and metrics; Artifact Health caches checksum results keyed by file metadata.

## Leakage control

Trendyol validation splits complete `term_id` groups so the same query cannot appear in train and evaluation. V2/V2.1 model-score training features are group-safe out-of-fold predictions. Holdout groups are never used for hyperparameter selection.

## V1, V2 and V2.1

- V1: stable sparse Logistic Regression classifier and live inference champion.
- V2: bounded classical classification and XGBoost ranking challengers; neither promoted.
- V2.1: Offline Evaluation on 1,000 complete groups and five group-safe seeds. HistGradientBoosting is the Best Research Candidate (mean F1 `0.753935`, CI `[0.746053, 0.761817]`) but was Not Promoted; Different historical split means Direct superiority is not established. Its selected object was not available after aggregation, so no classifier artifact was fabricated or retrained. The XGBoost ranker is research-only on a Bounded Candidate Sample.
- V3/V3.1 retrieval branch: five group-safe seeds evaluate 1,000 queries against 63,841 bounded products. Combined enriched TF-IDF is the Experimental Retrieval Baseline at Recall@50 `0.817239`; pinned multilingual E5 Small reaches `0.725147`; validation-selected RRF hybrid reaches `0.831392` with delta CI `[-0.006188, 0.034494]`. RRF is the Best Research Candidate but Not Promoted. Dense indexes use normalized float32 NumPy matrices; model cache and medium index remain ignored and reproducibly rebuildable.
- V4 pipeline branch: versioned contracts orchestrate retrieval, fixed `RRF k=20`, candidate pool 100, item-id tie-break, provenance, optional unchanged V1 scoring, fallbacks and stage timings. Hybrid retrieval-only is retained at Recall@50 `0.834640`, NDCG@10 `0.619136` and MRR `0.713543`. The verified V1 classifier remains valuable for relevance classification, but applying its probability as a reranker degraded ordering. The isolated XGBoost worker remains feature-incompatible with V4 candidates. V4 is bounded, offline and Not Production Promoted.

V5 cross-encoder reranking: experimental multilingual reranker applied after Hybrid RRF candidate fusion (pool 20). Model: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` pinned at revision `1427fd65`. Document variant: `title_compact_metadata`. Selected policy: pure cross-encoder (alpha=1.0) from validation grid. Holdout: NDCG@10 `0.6785`, absolute gain `+0.0664` vs Hybrid RRF baseline `0.6121`. Best Reranking Research Candidate, Not Production Promoted. Cold load ~1.6 s; warm pool-20 latency p95 ~433 ms.

## Limitations

Competition-snapshot results are not production business impact. The bounded catalogue is not a retrieval engine, V2 artifacts are research contracts, and lexical features miss some semantic intent.

V3 reproduction:

```bash
./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v3_evaluate.py --mode retrieval_smoke
./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v3_evaluate.py --mode retrieval_medium
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v3_summarize.py
./.venv/bin/python -m pip install -r 01-machine-learning/trendyol-search-relevance/requirements-semantic.txt
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v31_build_semantic.py
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v31_evaluate.py
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v4_evaluate.py
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v4_benchmark.py
```
