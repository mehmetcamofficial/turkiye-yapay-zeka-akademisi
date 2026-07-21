# V2 Limitations

- The resource-safe run uses 7,724 rows and 119 complete groups, not the full million-row training matrix.
- Validation has only 18 queries and holdout has 18; confidence intervals are therefore wide.
- The dense OOF base scorer approximates the V1 signal but is not the persisted sparse V1 pipeline.
- Candidate generation is not evaluated; ranking metrics condition on supplied candidates.
- Duplicate query-item pairs are collapsed by keeping the first occurrence.
- Category codes are ordinal conveniences, not semantic embeddings.
- No neural semantic model or CatBoost candidate was run due missing optional runtimes and CPU/storage discipline.
- Competition-snapshot metrics are not production-search evidence.
- V2.1 candidate recall outside the supplied candidate set cannot be computed because no independent catalogue-wide relevance universe is available; Recall@K is conditional on supplied candidates.
- The persisted V1 same-group row may overlap V1's historical training snapshot and is reported only as a reference, not an independent test.
