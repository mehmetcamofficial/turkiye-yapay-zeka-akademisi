# V4 Error Analysis

Deterministic examples in `outputs/v4/v4_error_examples.json` record Hybrid order, V1 order, NDCG movement and labelled positives. Observed categories are V1 top-order correction, V1 misclassification and incomplete judgments. The dominant aggregate finding is over-correction: a classifier trained for pairwise binary relevance is not automatically an effective listwise ranker.

Candidate-missing errors cannot be repaired by reranking. Semantic drift, lexical over-match, brand/model/numeric/unit mismatch, category mismatch and metadata weakness remain retrieval/enrichment concerns. Unlabelled products are not assumed irrelevant.
