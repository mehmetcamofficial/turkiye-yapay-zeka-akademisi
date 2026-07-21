# Portfolio Screenshot Checklist

Automated browser capture was unavailable because the browser-control runtime did not receive its required sandbox context. No screenshots were fabricated.

After starting the app on port 8503, capture optimized WebP or PNG images. Use a 1440 × 1000 browser viewport unless stated otherwise. Before every capture, confirm that no local filesystem path, uploaded personal data, browser account detail or raw dataset content is visible.

| Suggested filename | Page | Width/state or input | Expected visible evidence | Avoid |
|---|---|---|---|---|
| `overview-executive.png` | Platform Overview | 1440 px; initial state | Professional hero, platform status, Verified Champion and experimental challenger decisions | Browser profile, local URL bar if it exposes environment details |
| `trendyol-executive-summary.png` | Trendyol Search Intelligence | 1440 px; `01 · Executive & Live` | V1/V2/V2.1 comparison, Not Promoted wording, exact bounded/offline context | Raw term IDs and local paths |
| `trendyol-live-classification.png` | Trendyol Search Intelligence | 1280 px; query `kablosuz kulaklık`, title `Bluetooth kablosuz kulaklık`; submit | Alakalı/Alakasız, probability, threshold, version and descriptive input signals | Uploaded CSV, personal product data |
| `trendyol-ranking-playground.png` | Trendyol Search Intelligence | 1440 px; Product Ranking → Experimental V2 holdout ranker; select first available group | Baseline/final rank, rank movement, experimental warning and Bounded Candidate Sample | Local artifact paths, full raw dataset |
| `model-registry-governance.png` | Model Registry | 1440 px; default | Champion/challenger roles, algorithm, artifact status, primary metric and why-not-promoted banner | Expanded technical paths if home directory could appear |
| `artifact-health.png` | Artifact Health | 1440 px; default | Healthy/missing summary, algorithm/object class, cached checksum, reload status; HGB visibly Not persisted | Full absolute path or uncached diagnostic trace |
| `about-mehmet.png` | About Mehmet | 1280 px; default | Professional focus, working approach, selected projects and verified links | Unsupported titles, browser account information |
| `overview-v3-retrieval.png` | Platform Overview | 1440 px; V3.1 card visible | RRF Recall@50, indexed scope and Not Promoted governance | Production wording |
| `v3-semantic-search-default.png` | Trendyol → Semantic & Hybrid Search | 1440 px; query `kablosuz kulaklık`, Semantic | Real semantic scores, pinned model, bounded warning and latency | Full raw catalogue rows |
| `v3-method-comparison.png` | Trendyol → Semantic & Hybrid Search | 1440 px; run four comparison actions | Responsive TF-IDF/BM25/Semantic/Hybrid cards and shared-product flags | Four wide tables or local paths |
| `v3-hybrid-results.png` | Trendyol → Semantic & Hybrid Search | 1280 px; select Hybrid and submit | Real RRF scores, model/index scope and experimental status | Production promotion claims |
| `v3-query-segments.png` | Trendyol Evidence | 1440 px; V3 segment evidence visible | Query segment, Recall@50 and method counts | Raw identifiers beyond bounded evidence |
| `v3-registry-assets.png` | Model Registry | 1440 px; V3.1 rows visible | Model revision, dimension, Recall@50, RRF role and artifact availability | Expanded model cache paths |
| `v3-artifact-health.png` | Artifact Health | 1440 px; retrieval rows visible | Dense shapes, dtype, fingerprint-compatible metadata and cached checks | Recomputed checksum trace |
| `v3-search-architecture.png` | Trendyol → Semantic & Hybrid Search | 1440 px; architecture section | Implemented lexical, semantic and fusion paths versus planned reranking | Production labels |

Also repeat Overview and Trendyol at 390 px width to check wrapping, focus order, button labels and absence of horizontal page overflow. Store only optimized final captures under this directory.
