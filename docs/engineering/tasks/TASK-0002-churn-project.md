# TASK-0002 — Customer Churn Project

- record_type: reconstructed
- confidence: confirmed
- problem/context: Build an end-to-end binary classification project.
- goal: Train, evaluate, persist, and expose churn predictions.
- evidence: project README/source/artifacts; `bdbd1b2c`, `12a2115e`.
- alternatives: Logistic Regression, Decision Tree, Random Forest, Gradient Boosting.
- decision: Logistic Regression selected using validation evidence.
- implementation: training pipeline, feature engineering, Streamlit dashboard.
- validation/metrics: held-out ROC AUC 0.8440; 60/20/20 split.
- affected files: `customer-churn-prediction/`, portfolio churn service/page.
- related commit or PR: `bdbd1b2c`; PR #1 merge `9100637b`.
- lessons/follow-up: persist preprocessing with model; report imbalance.

