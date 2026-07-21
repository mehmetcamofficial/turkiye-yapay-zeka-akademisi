# V3.1 Model Selection

`hybrid_rrf` is selected as the **Best Research Candidate** for bounded candidate retrieval. It raises mean Recall@50 from TF-IDF `0.817239` to `0.831392` and Recall@100 from `0.886018` to `0.900276`, while also improving NDCG@10 and MRR. Four of five seed deltas are positive.

It is **Not Promoted**. Seed 62 Recall@50 delta was `-0.010641`, and the repeated-seed Recall@50 delta interval `[-0.006188, 0.034494]` includes small degradation. The live bounded demo uses the validation-majority RRF setting `k=20`; this is not a production configuration. V1 remains the Verified Champion relevance classifier and TF-IDF remains the Experimental Retrieval Baseline.
