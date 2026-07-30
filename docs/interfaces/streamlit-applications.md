# Streamlit Applications

| Application | Entry point | Inputs/outputs | Status |
|---|---|---|---|
| Unified portfolio | `01-machine-learning/portfolio_app.py` | navigation, language, project/search/model pages | active |
| Churn standalone | `customer-churn-prediction/app.py` | forms/CSV → predictions and plots | implemented |
| Housing standalone | `regression-project/app.py` | features/CSV → estimates and plots | implemented |
| NLP standalone | `nlp-project/app.py` | text/CSV → sentiment results | implemented |

The unified app uses session state for language/navigation, cached data/model
loaders, Matplotlib charts, safe tables, and downloads. No external user
analytics are evidenced.

