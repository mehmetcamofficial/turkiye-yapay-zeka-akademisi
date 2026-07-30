# California Housing Regression

- Status: implemented predictive regression project.
- Problem/user: predict median housing value for educational analysis.
- Origin: `5ed3f3a1` (2026-07-21).
- Entry points: `regression-project/train_model.py`, `app.py`, portfolio page.
- Data: tracked California Housing data, 20,640 × 9; scikit-learn/StatLib and
  1990 U.S. Census are documented in `DATA_SOURCE.md`.
- Models: RandomForestRegressor selected over GradientBoostingRegressor.
- Result: MAE 0.3346, RMSE 0.5121, R² 0.8087.
- UI: single/batch prediction, plots, downloadable results.
- Limitations: geographic/time transfer and fairness are not established.
- Evidence: README, training script, outputs, persisted model.
- Unanswered: external deployment and user validation are unknown.

