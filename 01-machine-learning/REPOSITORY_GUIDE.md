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
- V3: planned semantic retrieval and cross-encoder reranking; not implemented.

## Limitations

Competition-snapshot results are not production business impact. The bounded catalogue is not a retrieval engine, V2 artifacts are research contracts, and lexical features miss some semantic intent.
