# V3.1 Limitations

- Evaluation uses a deterministic 63,841-product bounded catalogue, not all 962,873 products.
- Relevance labels are incomplete; unlabelled retrieved products may be relevant.
- Standalone semantic retrieval materially trails TF-IDF and drifts on short exact-brand/formulation queries.
- RRF Recall@50 is lower on one seed and its repeated-seed delta interval includes a small negative value.
- Unit-query evidence was insufficient in the evaluated holdouts for a separate reliable segment result.
- The model cache is approximately 470 MiB and intentionally excluded from Git; offline semantic inference requires the pinned cache.
- The 98,059,904-byte medium dense index is ignored; it must be rebuilt locally from documented commands.
- No catalogue-wide evaluation, cross-encoder, online A/B test, production traffic, business impact or SLA is claimed.
