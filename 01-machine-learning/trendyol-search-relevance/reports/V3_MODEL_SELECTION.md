# V3 Model Selection

`tfidf_combined_enriched` remains the **Experimental Retrieval Baseline** (Recall@50 `0.817239`). V3.1 measured standalone semantic retrieval at `0.725147` and validation-selected RRF hybrid at `0.831392`. RRF is now the **Best Research Candidate**, but is Not Promoted because one seed regressed and its Recall@50 delta interval `[-0.006188, 0.034494]` includes small degradation. Optional reranking remains unattempted so candidate generation and ranking stay separate. V1 remains the Verified Champion relevance classifier; Catalogue-Wide Not Established applies.
