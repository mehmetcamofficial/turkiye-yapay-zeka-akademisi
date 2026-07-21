# V3.1 Statistical Comparison

The primary comparison is Recall@50 against `tfidf_combined_enriched` (`0.817239`).

| Method | Recall@50 | 95% interval | Delta vs TF-IDF | Delta interval | Improved / unchanged / worsened |
|---|---:|---:|---:|---:|---:|
| Semantic E5 Small | 0.725147 | [0.710879, 0.739416] | -0.092091 | [-0.108379, -0.075803] | 104 / 369 / 277 |
| Weighted hybrid | 0.829845 | [0.820284, 0.839407] | +0.012607 | [-0.003517, 0.028730] | 102 / 582 / 66 |
| RRF hybrid | 0.831392 | [0.810725, 0.852059] | +0.014153 | [-0.006188, 0.034494] | 128 / 521 / 101 |
| Candidate union | 0.791763 | [0.770777, 0.812749] | -0.025476 | [-0.049522, -0.001429] | 118 / 460 / 172 |

RRF also improved Recall@100 by `0.014258` (CI `[0.007515, 0.021001]`), NDCG@10 by `0.014783` (`[0.001876, 0.027690]`) and MRR by `0.026666` (`[0.003756, 0.049576]`). Query-level bootstrap intervals by seed and metric are preserved in `outputs/v3/v31_bootstrap_by_seed.csv`.
