# V3 Statistical Comparison

The strongest lexical validation configurations were compared on identical holdout queries for seeds 42, 52, 62, 72 and 82. Query-level bootstrap results are in `retrieval_bootstrap_by_seed.csv`; repeated-seed t intervals are in `retrieval_delta_repeated_seed_ci.csv`. The primary metric is Recall@50. The current numerical leader is `tfidf_combined_enriched` at mean Recall@50 0.817239, CI [0.801112, 0.833366]. Semantic and hybrid rows are intentionally absent rather than represented by fabricated zeros.
