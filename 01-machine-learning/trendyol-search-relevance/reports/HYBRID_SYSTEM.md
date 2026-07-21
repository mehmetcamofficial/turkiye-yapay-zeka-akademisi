# Hybrid Search

The evaluated architecture is `query → bounded candidate set → leakage-safe classifier score → XGBoost reranker → ordered results`. Candidate generation is outside this repository; the playground only uses holdout candidates already present locally.

On holdout, reranking changed NDCG@10 from 0.8477 to 0.8044 and Recall@10 from 0.6986 to 0.6771. Ten of 18 queries worsened, three improved and five were unchanged. Consequently the final deployed path remains the V1 classifier; V2 is an offline challenger only.
