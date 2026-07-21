# Algorithm Review

V1 remains the production champion. V2 separately benchmarked linear models, SGD variants, shallow trees, bagged trees and histogram boosting for binary relevance; ranking used XGBoost LambdaMART objectives (`rank:ndcg` mean/top-k, `rank:map`, `rank:pairwise`). CatBoost was skipped because it was absent and adding a second optional boosting runtime was not justified. Semantic models were skipped: `torch`, `transformers` and `sentence-transformers` were absent, execution was CPU-only, and the bounded experiment did not justify a large model download.

Features are explicit lexical similarities, word/character TF-IDF cosine, missing indicators, encoded catalogue fields, training-only frequencies and group-safe out-of-fold base scores. IDs and labels are never features.
