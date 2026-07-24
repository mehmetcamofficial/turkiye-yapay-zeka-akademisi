# V4 Policy Comparison

| Retrieval | Policy | Recall@50 | Recall@100 | NDCG@10 | MRR | Decision |
|---|---|---:|---:|---:|---:|---|
| TF-IDF | retrieval-only | 0.817239 | 0.886018 | 0.603232 | 0.686716 | Baseline |
| TF-IDF | V1 | 0.779595 | 0.886018 | 0.524135 | 0.617308 | Reject |
| Hybrid RRF k=20 | retrieval-only | 0.834640 | 0.900276 | 0.619136 | 0.713543 | Select |
| Hybrid RRF k=20 | V1 | 0.797306 | 0.900276 | 0.531485 | 0.619658 | Reject |
| Hybrid RRF k=20 | experimental ranker | 0.797306 | 0.900276 | 0.531485 | 0.619658 | Incompatible; V1 fallback |
| Hybrid RRF k=20 | blended | 0.797306 | 0.900276 | 0.531485 | 0.619658 | Incompatible; V1 fallback |

Ranker and blended rows are fallback measurements, not claims that XGBoost produced those scores.
