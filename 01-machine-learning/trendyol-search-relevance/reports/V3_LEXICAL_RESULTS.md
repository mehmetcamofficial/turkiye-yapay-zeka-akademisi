# V3 Lexical Results

The Offline Evaluation used 1,000 complete queries and 63,841 indexed products. Validation selected `tfidf_combined_enriched` and `bm25_enriched_k1.2_b0.75`. Mean five-seed TF-IDF Recall@50 was 0.817239, Recall@100 0.886018, NDCG@10 0.603232, MRR 0.686716. BM25 values were 0.802656, 0.856537, 0.632878, 0.716717. Full per-seed metrics, validation grid, build time, index bytes and latency are stored in `outputs/v3/`.

BM25 uses `idf(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))` and the standard length-normalized term contribution `idf(t) * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))`. The selected enriched index used `k1=1.2`, `b=0.75`. The combined TF-IDF score weights enriched word similarity at 0.60 and enriched character similarity at 0.40; the title-only and enriched variants make metadata contribution directly testable.

The persisted 5,000-product live-demo asset is 8,914,086 bytes. A fresh-process load took 1,228.51 ms; after warm-up, 100 measured queries gave TF-IDF p50/p95 0.621/0.647 ms and BM25 p50/p95 0.122/0.257 ms. The Streamlit service uses `st.cache_resource`, so it neither reloads nor rebuilds the index per query. These demo timings are separate from the 63,841-product evaluation timings.

This is a Bounded Candidate Sample with incomplete judgments, not catalogue-wide production search.
