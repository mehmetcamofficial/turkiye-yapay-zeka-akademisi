# Robust Ranking V2.1 Results

## Protocol

`ranking_medium` selected 1,000 complete query groups deterministically: 52,422 rows after removing 3,419 duplicate query-item pairs. Five seeds (42, 52, 62, 72, 82) each used 700/150/150 train/validation/holdout groups. Every term overlap and duplicate-pair leakage count was zero. Confidence intervals below are t intervals over five seed-level results; per-seed query bootstrap intervals are preserved separately.

## Classification

The highest mean holdout F1 was **hist_gradient_boosting**, 0.753935 ± 0.006349 (95% CI 0.746053–0.761817); precision 0.680770, recall 0.845319, PR AUC 0.756657. It is the Best Research Candidate but remains an Experimental Challenger and was Not Promoted: the Verified Champion V1 metric belongs to a Different historical split, so Direct superiority is not established. Selection happened after repeated-seed aggregation and no selected trained HGB object remained; therefore it was intentionally not persisted rather than retrained.

## Ranking

The leakage-safe baseline averaged NDCG@10 **0.871041**. `rank_ndcg_topk` delta was -0.007469 (95% CI -0.023354–0.008416); `rank_pairwise` delta was -0.002659 (95% CI -0.010400–0.005082). The numerically highest row was **persisted_v1_reference** at 0.874630; the persisted V1 row is a reference whose historical training snapshot may overlap the sampled data and therefore cannot be treated as independent promotion evidence. No trainable V2.1 ranker produced a repeatable material gain over the leakage-safe baseline.

## Hard negatives

Mean F1 was original 0.617633, weighted 0.476246, enriched 0.420103, and weighted + enriched 0.200427. Weighting and enrichment increased precision but sharply reduced recall and F1 across seeds. Ranking NDCG@10 also stayed below the leakage-safe baseline. The original training policy is retained.

## Decision

V1 remains the live champion. V2.1 classifiers and rankers are research artifacts only. CatBoost was skipped because its optional dependency was unavailable; no additional large runtime was installed. Semantic retrieval is recommended for V3 after a retrieval-quality candidate baseline is established.
