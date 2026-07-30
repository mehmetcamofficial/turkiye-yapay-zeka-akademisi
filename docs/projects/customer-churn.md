# Customer Churn Prediction

- Identity/status: binary classification; implemented and persisted.
- Problem/user: estimate telecom churn risk for learners and portfolio users.
- Origin: `bdbd1b2c` (2026-07-21); dashboard milestone `12a2115e`.
- Entry points: `customer-churn-prediction/train_model.py`, `app.py`, and
  `portfolio/pages/churn.py`.
- Data: tracked Telco Customer Churn CSV, 7,043 rows; source characterization
  is documented in the project README, but exact upstream URL/license requires
  confirmation.
- Models: Logistic Regression selected; Decision Tree, Random Forest, and
  Gradient Boosting compared. Median/mode imputation, encoding, engineered
  tenure/spend/support/charge features, and L1 selection are implemented.
- Result: final ROC AUC 0.8440. Train/validation/test split is 60/20/20.
- UI: single and batch prediction, downloadable CSV, performance artifacts.
- Tests/runtime: portfolio integrity tests and persisted pipeline loading.
- Limitations: educational dataset, imbalance, no external deployment evidence.
- Evidence: project README, training script, tracked outputs, model pickle.
- Unanswered: original dataset acquisition and deployment history.

