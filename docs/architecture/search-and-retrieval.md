# Search and Retrieval

Two search systems are distinct:

- Trendyol product search uses sparse TF-IDF/BM25, multilingual E5 semantic
  retrieval, Hybrid RRF, optional XGBoost policies, and V5 cross-encoder
  reranking.
- Portfolio/Copilot search indexes repository resources and uses lexical,
  symbol, path, heading, project, filename, and configured alias evidence.

The Trendyol V4 selected policy is Hybrid RRF retrieval-only; V5 is documented
as the best reranking research candidate, not production promoted. Copilot V2
improvements were constrained to zero-regression, general rules.

