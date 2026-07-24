# V4 Query Segment Analysis

V1 ordering degraded Hybrid NDCG@10 in every measured segment. The smallest reduction was age-specific (`-0.035532`); brand queries were `-0.064807`, short queries `-0.085702`, model/number-heavy queries `-0.093532`, attribute-heavy `-0.116161`, gender-specific `-0.140782`, low lexical overlap `-0.142535`, and medium lexical overlap `-0.214287`.

V1 sometimes moved additional positives into the top 50 for age-specific (`+0.043400`) and model/number-heavy (`+0.030674`) queries, but worsened top ordering. This is insufficient for policy selection. Unit and typo-like cohorts are small or absent under the deterministic rules and must not be generalized.
