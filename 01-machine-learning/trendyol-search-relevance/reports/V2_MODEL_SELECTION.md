# V2 Model Selection

Random Forest is retained as the classification challenger and `rank_ndcg_topk` as the ranking challenger because each led its own validation objective. Neither replaces V1. Classification weakened materially on holdout, while ranking failed to beat the leakage-safe first-stage baseline. Artifacts are stored separately under `models/v2/`; V1 files and metrics were not modified.
