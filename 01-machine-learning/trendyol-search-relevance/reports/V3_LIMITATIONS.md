# V3 Limitations

- The index is a deterministic bounded broad catalogue, not all 962,873 products.
- Judgments are incomplete; unlabelled results may still be relevant.
- Semantic quality is measured, but standalone E5 materially trails TF-IDF and requires an ignored local model cache.
- The medium dense index is reproducible but ignored; only the reasonably sized demo index is a repository artifact candidate.
- No cross-encoder, online A/B test, business impact, production traffic or SLA is claimed.
- Cold build latency differs from warm cached-query latency.
- The 5,000-product demo met warm semantic/hybrid latency budgets; cold model/index load is approximately four seconds.
