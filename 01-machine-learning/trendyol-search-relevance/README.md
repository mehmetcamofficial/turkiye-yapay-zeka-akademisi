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

## V2.1 robust evaluation

`ranking_medium` evaluates 1,000 complete query groups (52,422 deduplicated rows) on five fixed seeds. Every seed uses 700/150/150 train/validation/final-holdout groups with zero overlap. HistGradientBoosting was the Best Research Candidate: mean F1 `0.753935`, standard deviation `0.006349`, 95% CI `[0.746053, 0.761817]`. It remains an Experimental Challenger and was Not Promoted because V1's published metric belongs to a Different historical split and Direct superiority is not established. Selection occurred after aggregation and the selected trained object was not retained, so no HGB artifact was fabricated or retrained. The leakage-safe Bounded Candidate Sample baseline averaged NDCG@10 `0.871041`; `rank_ndcg_topk` delta was `-0.007469`, CI `[-0.023354, 0.008416]`, and `rank_pairwise` delta was `-0.002659`, CI `[-0.010400, 0.005082]`. Hard-negative F1 values were original `0.617633`, weighted `0.476246`, enriched `0.420103`, and weighted+enriched `0.200427`.

`ranking_large` (5,000 groups) and `ranking_full` remain explicit modes and never run automatically. They were not executed: the mandatory five-seed medium evaluation already showed no reproducible ranker gain, while larger repeated feature/model fitting would add disproportionate runtime and memory without changing the governance threshold.

## V3/V3.1 semantic retrieval and hybrid search

V3 separates candidate discovery from V1 relevance scoring and experimental ranking. It implements Turkish-aware normalization, deterministic product/judgment contracts, sparse word/character TF-IDF, BM25, Recall@K/MRR/MAP/NDCG metrics, query bootstrap and bounded live search. `retrieval_medium` uses 1,000 complete query groups and a 63,841-product broad bounded catalogue made from every labelled relevant product plus independently sampled distractors. Across five group-safe seeds, selected combined enriched TF-IDF reaches Recall@50 `0.817239` (95% CI `[0.801112, 0.833366]`), Recall@100 `0.886018`, MRR `0.686716` and NDCG@10 `0.603232`. Selected BM25 reaches Recall@50 `0.802656`, Recall@100 `0.856537`, MRR `0.716717` and NDCG@10 `0.632878`. TF-IDF remains the Experimental Retrieval Baseline because Recall@50 is the primary selection metric.

V3.1 pins MIT-licensed `intfloat/multilingual-e5-small` revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`, builds normalized float32 NumPy indexes and evaluates real semantic, weighted fusion, RRF and candidate-union retrieval. Standalone semantic Recall@50 is `0.725147`; RRF is the Best Research Candidate at `0.831392` versus TF-IDF `0.817239`, with delta CI `[-0.006188, 0.034494]`. It remains Not Promoted. The UI activates Semantic and Hybrid only with compatible cache/index assets and never silently substitutes lexical scores.

On macOS arm64, semantic inference stays in the Streamlit process while
experimental XGBoost ranker checks use a bounded persistent worker. This keeps
the incompatible PyTorch and XGBoost OpenMP runtimes out of the same
interpreter. Registry and Artifact Health use persisted metadata instead of
eager native artifact reloads.

## Reproduce

```bash
./.venv/bin/python 01-machine-learning/trendyol-search-relevance/train.py --mode smoke
./.venv/bin/python 01-machine-learning/trendyol-search-relevance/train.py --mode sample
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/inference.py
./.venv/bin/python -m pip install -r 01-machine-learning/trendyol-search-relevance/requirements-semantic.txt
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v31_build_semantic.py
PYTHONPATH=01-machine-learning/trendyol-search-relevance ./.venv/bin/python 01-machine-learning/trendyol-search-relevance/v31_evaluate.py
```

The selected complete pipeline, metadata, evaluation, error analysis and bounded catalogue sample are stored locally. Platform integration uses the same inference API and never scans the full catalogue per interaction.

## Limitations

This is a bounded lexical baseline on a public competition snapshot, not production search. Group splitting is not perfectly label-stratified; semantic synonyms, intent ambiguity, rare categories and catalogue drift remain important risks.
