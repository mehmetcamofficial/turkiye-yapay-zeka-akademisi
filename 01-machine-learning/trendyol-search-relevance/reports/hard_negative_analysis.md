# Hard-negative Analysis

High-overlap negative examples were defined as negative rows with Jaccard similarity at least 0.2; 150 appeared in training. Baseline logistic F1 was 0.7227. Doubling those rows' weights improved F1 to 0.7454 while PR AUC slightly decreased from 0.7529 to 0.7494. Explicit duplication was also tested and is recorded in `outputs/v2/hard_negative_experiments.csv`. This analysis is diagnostic; it does not change V1.
