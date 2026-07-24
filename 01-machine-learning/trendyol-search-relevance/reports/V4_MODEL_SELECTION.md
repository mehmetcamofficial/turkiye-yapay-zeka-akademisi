# V4 Model and Policy Selection

**Selected: fixed `k=20` Hybrid RRF retrieval-only** with candidate pool `100` and deterministic item-id tie-break. It is the Best Pipeline Research Candidate and remains Not Production Promoted. V1 scoring is integrated as an optional observable stage, but is not the default final order because paired evidence shows material ranking degradation.

The verified V1 classifier remains valuable for relevance classification, but applying its probability directly as a reranking policy degraded Recall@50, NDCG@10 and MRR in the V4 candidate pipeline.

The experimental ranker is not selected: persisted feature contracts are incompatible with the V4 live candidate contract. Blended weights were not tuned because a non-zero ranker weight would fabricate compatibility; the safe fallback is V1, which also degraded. Historical XGBRanker artifacts remain valid historical research artifacts; V4 ranker scoring is intentionally not executed. V1 remains the unchanged Verified Champion classifier, not a ranking model.
