# V3.1 Semantic Results

Pinned `intfloat/multilingual-e5-small` revision `614241f622f53c4eeff9890bdc4f31cfecc418b3` was evaluated with real 384-dimensional L2-normalized embeddings on the identical 1,000-query, 63,841-product V3 medium catalogue and five frozen holdouts.

Mean semantic metrics were Recall@50 `0.725147` (95% repeated-seed interval `[0.710879, 0.739416]`), Recall@100 `0.795702`, NDCG@10 `0.527419` and MRR `0.633439`. Recall@50 by seed was `0.708623`, `0.730553`, `0.731563`, `0.718176`, `0.736823`. Against TF-IDF, mean Recall@50 delta was `-0.092091`, CI `[-0.108379, -0.075803]`; 104 queries improved, 369 were unchanged and 277 worsened.

The semantic retriever is therefore retained as an **Experimental Semantic Retriever**, not a standalone Best Research Candidate. It contributes complementary candidates to hybrid retrieval but materially underperforms exact lexical retrieval alone.
