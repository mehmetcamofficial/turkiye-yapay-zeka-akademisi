# V3 Retrieval Feasibility

## Sources and contracts

Inspected `02-data-science/midterm-assignment/data/items.csv` using chunked projected reads and `train_with_negatives.parquet` using Parquet column projection. The catalogue fields are `item_id`, `title`, `category`, `brand`, `gender`, `age_group`, and `attributes`; the judgment source adds `term_id`, `query`, and binary `label`.

The catalogue contains 962,873 rows and 962,873 unique item IDs. Missing item IDs and titles are zero; two brands are missing. The judgment table contains 1,000,000 rows, 17,968 complete query groups, 250,000 unique positive query-item pairs and 229,416 positive products. 17,798 products are positive for more than one query; median positive products/query is seven.

## Feasible scope

Catalogue-wide sparse retrieval is technically possible but unnecessarily costly for iterative five-seed evaluation. V3 uses a deterministic bounded broad catalogue: every relevant product for the selected evaluation queries plus roughly 50,000 independently stride-sampled distractors. It is not an artificially query-local candidate set and is explicitly not catalogue-wide.

The mandatory mode selects 1,000 complete eligible query groups. Query-item duplicates are removed consistently, products are ordered deterministically by `item_id`, and every judged positive must exist in the index. Rows with missing IDs or empty searchable text are excluded; current source inspection found none.

## Resource estimates

A float32 dense index for the full catalogue would require about 1.38 GiB at 384 dimensions or 2.75 GiB at 768 dimensions, excluding model and search overhead. The bounded 50k catalogue would require roughly 77 MiB at 384 dimensions. Sparse index sizes, build time, memory and query latency are measured by the evaluator rather than estimated.

No semantic runtime is installed (`torch`, `transformers`, `sentence-transformers`, FAISS are absent). Downloading a large model and cache solely to force semantic metrics would violate dependency and reproducibility constraints. True catalogue-wide semantic evaluation is therefore not feasible in the current verified environment.

## Limitations

Relevance judgments are incomplete: an unlabelled retrieved product is not necessarily irrelevant. Candidate recall is measured only against labelled positives and the bounded broad catalogue. No online traffic, conversion impact, A/B test, catalogue-wide SLA or production business result is claimed.
