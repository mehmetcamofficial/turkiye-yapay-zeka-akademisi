# Trendyol Search Relevance

- Status: implemented research system; promotion status varies by version.
- Problem: classify relevance, generate candidates, and rerank product results.
- Origin: V1 `377fbe8a`; V2 `35357283`; V3 `4f168992`; V4 `f70e398a`; V5
  `4db73a6b`.
- Entry points: `train.py`, `v21_evaluation.py`, `v3_evaluate.py`,
  `v31_evaluate.py`, `v4_evaluate.py`, `v5_evaluate.py`, pipeline services.
- Data: tracked samples and evaluation judgments plus bounded catalog artifacts;
  see project README and V5 dataset construction report.
- Models: TF-IDF Logistic Regression champion; tree/linear/XGBoost challengers;
  TF-IDF/BM25/E5 retrieval; Hybrid RRF; mMARCO MiniLM cross-encoder.
- Result: V5 NDCG@10 0.6785 versus Hybrid RRF 0.6121; MRR 0.7720 versus
  0.7176. V5 remains a research candidate.
- UI: relevance, search demo, policy comparison, live inference, V5 pages.
- Tests: `trendyol-search-relevance/tests/`; semantic tests require local assets.
- Failures/lessons: standalone semantic underperformed lexical; uncertainty and
  runtime constraints prevented automatic promotion.
- Evidence: project README, reports, outputs, tests, model metadata.
- Unanswered: original raw-data licensing boundaries and production use.

