# V3 Query Segment Analysis

`outputs/v3/v31_query_segment_metrics.csv` contains measured TF-IDF, BM25, semantic and hybrid results. Standalone semantic improved Recall@50 only for the attribute-heavy segment (`+0.048701`) and regressed most on short (`-0.140327`), low-overlap (`-0.113636`) and brand queries (`-0.110136`). The low-overlap segment is small and must not be generalized.

RRF recovered complementary candidates: strongest measured deltas were low lexical overlap `+0.102273`, medium lexical overlap `+0.063978`, attribute-heavy `+0.047827`, model-code/number-heavy `+0.023050` and medium queries `+0.022104`. Small regressions remained for gender-specific `-0.004623` and long queries `-0.003856`. No reliable unit-query segment row was available.
