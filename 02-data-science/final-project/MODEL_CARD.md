# Model Card — Trendyol Search Relevance Intelligence v1.0.0

- Status: First validated bounded baseline
- Task: Binary query-product relevance classification
- Data: 100,000-row deterministic sample of the public Datathon dataset
- Primary split: GroupShuffleSplit by `term_id`; term overlap 0
- Selected model: combined word/character TF-IDF + explicit similarity features + Logistic Regression
- Validation: F1 0.6260, precision 0.7406, recall 0.5422, PR AUC 0.7165, ROC AUC 0.9100
- Score: calibrated-by-model Logistic Regression probability; decision threshold 0.5
- Artifact: `01-machine-learning/trendyol-search-relevance/models/trendyol_relevance_pipeline.pkl`

The model is a lexical educational baseline. It does not rank the full Trendyol catalogue and is not evidence of production search quality. See `RISK_AND_LIMITATIONS.md` and the project error analysis.
