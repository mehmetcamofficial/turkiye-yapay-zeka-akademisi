# Model Lifecycle

Training scripts own preprocessing, split logic, comparison, tuning, final
evaluation, and persistence. Runtime services load artifacts lazily and expose
failure states instead of silently retraining. Research candidates are labeled
separately from promoted or deployable artifacts.

Confirmed examples include churn Logistic Regression, housing Random Forest,
sentiment MultinomialNB, Trendyol V1 Logistic Regression, V3/V4 Hybrid RRF, and
V5 cross-encoder reranking. See `../models/model-inventory.yaml`.

