# V4 Limitations

- Live scope is 5,000 products; offline evaluation scope is 63,841 products and 1,000 complete queries.
- Relevance judgments are incomplete; no online A/B test, production SLA or business impact exists.
- Semantic measurements are CPU-only and cold start exceeds five seconds.
- The verified V1 classifier remains valuable for relevance classification, but applying its probability directly as a reranking policy degraded Recall@50, NDCG@10 and MRR.
- Historical XGBRanker artifacts are valid research artifacts, but feature contracts are incompatible with the V4 live candidate contract; ranker scoring is intentionally not executed and worker policies degrade explicitly.
- Filter values depend on bounded catalogue metadata quality.
- Local Pipeline Diagnostics are not production monitoring.
