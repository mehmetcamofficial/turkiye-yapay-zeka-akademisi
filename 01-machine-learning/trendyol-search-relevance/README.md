# Trendyol Search Relevance Intelligence

Independent classical machine-learning baseline for binary query-product relevance classification using the public Datathon dataset. This project does not imply Trendyol or TEKNOFEST endorsement.

## Problem and data

The model receives query, title, category, brand, gender, age group and attributes, and predicts binary `label`. Source data remains under `02-data-science/midterm-assignment/data/`; it is not duplicated. Data modes are smoke (5,000), sample (100,000) and explicit full mode.

## Leakage prevention and features

Primary validation is a fixed-seed group split by `term_id`; term overlap must be zero. A random stratified split and item-group split are reported for comparison. Features combine conservative Turkish-aware normalization, word/character TF-IDF and explicit lexical similarity. IDs, target and weights are excluded from features.

## Candidates and evaluation

DummyClassifier, LogisticRegression, LinearSVC and MultinomialNB are evaluated. Selection prioritizes group-term F1, precision/recall balance, PR AUC, inference cost and demo suitability—not accuracy alone. LinearSVC scores remain explicitly labeled decision scores.

The first persisted artifact uses the deterministic 100,000-row sample. Combined word/character TF-IDF + explicit similarities with Logistic Regression was selected: group-term validation F1 0.6260, precision 0.7406, recall 0.5422, PR AUC 0.7165 and ROC AUC 0.9100. These are bounded validation results, not production performance.

## V2 challenger research

V2 keeps V1 frozen and evaluates classification and learning-to-rank separately on 7,724 rows from 119 complete query groups. The 70/15/15 `term_id` split has zero overlap. Random Forest is the classification challenger (holdout F1 0.6384); XGBoost `rank:ndcg` top-k is the ranking challenger (holdout NDCG@10 0.8044). It did not beat the leakage-safe first-stage NDCG@10 of 0.8477, so neither challenger is promoted. The Streamlit page exposes bounded benchmark and playground views, while live inference remains V1.

## Reproduce

```bash
./.venv/bin/python 01-machine-learning/trendyol-search-relevance/train.py --mode smoke
./.venv/bin/python 01-machine-learning/trendyol-search-relevance/train.py --mode sample
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/inference.py
```

The selected complete pipeline, metadata, evaluation, error analysis and bounded catalogue sample are stored locally. Platform integration uses the same inference API and never scans the full catalogue per interaction.

## Limitations

This is a bounded lexical baseline on a public competition snapshot, not production search. Group splitting is not perfectly label-stratified; semantic synonyms, intent ambiguity, rare categories and catalogue drift remain important risks.
