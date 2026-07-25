# V4 Statistical Comparison

Hybrid + V1 versus fixed-k Hybrid retrieval-only: Recall@50 delta `-0.037334`, 95% repeated-seed interval `[-0.059732, -0.014936]`, 107 improved / 466 unchanged / 177 worsened query-seed observations. NDCG@10 delta `-0.087652`, interval `[-0.118122, -0.057181]`, counts 220/117/413. MRR delta `-0.093885`, interval `[-0.154724, -0.033046]`, counts 142/331/277.

All three intervals indicate material degradation. Experimental-ranker and blended requests produced the same values only because their incompatible feature contract invoked the documented V1 fallback.
