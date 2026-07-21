# Feature Dictionary

## Normalized text

- `query_text`: lower-case, whitespace-normalized query; Turkish characters and product codes preserved.
- `title_text`, `category_text`, `brand_text`, `attributes_text`: equivalent source-field copies.
- `product_document`: title + category + brand + attributes.
- `pair_document`: transparent query + product document representation.

## Sparse families

- Word TF-IDF for query, product document and query-product pair; word 1–2 grams.
- Character TF-IDF for the pair document; `char_wb` 3–5 grams.
- Sparse matrices are never converted to dense form.

## Explicit similarity

Exact match, mutual containment, word counts, length difference, intersection/union, Jaccard, query/title coverage, brand mention, category overlap, normalized character-length ratio and attributes overlap.

IDs, label and sample weight are never included as model features.
