# Ranking Results

Ranking feasibility was confirmed on all 1,000,000 raw rows: 17,968 queries, median 28 candidates/query, and every query had both labels. V2 uses complete groups and removes 59,650 duplicate query-item pairs before splitting.

The validation winner was XGBoost `rank:ndcg` with top-k pair construction. Holdout: NDCG@1 0.7667, NDCG@3 0.7913, NDCG@5 0.7915, NDCG@10 0.8044, MRR 0.8519, Precision@10 0.5407, Recall@10 0.6771 and MAP@10 0.8190. The leakage-safe first-stage scorer achieved NDCG@10 0.8477, so the ranker was not promoted.
