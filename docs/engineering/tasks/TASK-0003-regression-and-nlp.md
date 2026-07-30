# TASK-0003 — Regression and NLP Projects

- record_type: reconstructed
- confidence: confirmed
- problem/context: Expand beyond churn to regression and text classification.
- goal: Complete housing and sentiment workflows with artifacts and apps.
- evidence: project READMEs/source; commit `5ed3f3a1`.
- alternatives: RF versus gradient boosting; Logistic/SVC/NB for sentiment.
- decision: Random Forest regression and MultinomialNB sentiment selected.
- implementation: downloaders, training scripts, outputs, models, Streamlit.
- validation/metrics: housing RMSE 0.5121/R² 0.8087; sentiment F1 0.8212.
- affected files: `regression-project/`, `nlp-project/`.
- related commit or PR: `5ed3f3a1`, merge `fe61d53e`.
- lessons/follow-up: document data origin and task-specific limitations.

