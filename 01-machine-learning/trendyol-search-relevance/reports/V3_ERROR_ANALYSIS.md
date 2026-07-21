# V3 Retrieval Error Analysis

Measured medium-holdout examples are stored in `outputs/v3/v31_error_examples.json`. Semantic retrieval corrected lexical formulation/typo cases such as `waflee makinası`, but drifted on exact short brands and identifiers such as `jrl`, `nars`, `fullamoda mont` and `küçük lego`. Hybrid RRF usually preserved the exact lexical path while admitting complementary semantic candidates.

Failure categories include semantic drift, exact-brand loss, category ambiguity, lexical formulation mismatch and incomplete labels. An unlabelled retrieved product is not automatically irrelevant; examples show only labelled-item recall and descriptive top results.
