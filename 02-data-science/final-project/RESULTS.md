# V1 Results

## Data and validation

Sample mode uses 100,000 deterministic rows. Training uses 80,715 rows and validation 19,285 rows. The validation positive rate is 0.2501; `term_id` overlap is exactly zero. Item overlap is 4,983 because the primary split isolates queries, not products.

## Selected baseline

Combined word/character TF-IDF + explicit similarity features with Logistic Regression was selected using group-term F1, PR AUC, inference cost and live-demo suitability.

| Metric | Value |
|---|---:|
| Accuracy | 0.8380 |
| Precision | 0.7406 |
| Recall | 0.5422 |
| F1 | 0.6260 |
| PR AUC | 0.7165 |
| ROC AUC | 0.9100 |

These are bounded validation results, not production performance. Full mode was not run.
