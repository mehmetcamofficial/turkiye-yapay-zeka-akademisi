# V5 Limitations

- Live scope is 5,000 products; offline evaluation scope is 63,841 products and 1,000 complete queries.
- Relevance judgments are incomplete; no online A/B test, production SLA, or business impact exists.
- Cross-encoder inference is CPU-only; cold model load exceeds several seconds.
- The cross-encoder reranker does not improve candidate recall; it only reorders the retrieved pool.
- Cross-encoder scores are raw logits, not calibrated probabilities.
- Exact-match queries (brand, model codes, numbers) may be demoted by the cross-encoder.
- Turkish language support depends on the multilingual model's training data.
- Memory usage increases with model load; peak RSS may exceed 1.4 GB.
- Latency for pool=100 may exceed 1 second on CPU; pool=20 or 50 is recommended for live demo.
- No production SLA is claimed.
- The cross-encoder is an experimental reranker, not a production ranking model.
- Fine-tuning is optional and may not be justified by the dataset size.
- Score normalization is per-query min-max, which may be unstable for short candidate lists.
- The hybrid blend alpha is tuned on validation only; generalization to unseen queries is not guaranteed.
- Runtime coexistence with E5 semantic model and XGBoost worker must be verified.
- Not Production Promoted.
