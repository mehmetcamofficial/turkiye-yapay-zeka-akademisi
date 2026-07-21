# V3.1 Hybrid Results

Weighted normalized fusion, Reciprocal Rank Fusion (RRF) and candidate union were evaluated with real semantic scores. Parameters were selected separately on each seed's validation groups; holdout groups were never used for tuning.

RRF was the strongest hybrid: mean Recall@50 `0.831392`, Recall@100 `0.900276`, NDCG@10 `0.618014`, MRR `0.713382`. Validation selected RRF `k=20` for seeds 42, 52, 72 and 82, and `k=100` for seed 62. Recall@50 by seed was `0.827187`, `0.842445`, `0.805833`, `0.849126`, `0.832369`.

Weighted fusion reached Recall@50 `0.829845`; validation selected lexical alpha `0.80` for four seeds and `0.65` for seed 82. Candidate union reached `0.791763` and reduced Recall@100, so it was rejected.

RRF is labelled **Best Research Candidate · Not Promoted · Bounded Demo · Offline Evaluation**. Its Recall@50 delta versus TF-IDF is positive on four of five seeds, but the repeated-seed interval includes a small negative value; direct superiority is not established.
