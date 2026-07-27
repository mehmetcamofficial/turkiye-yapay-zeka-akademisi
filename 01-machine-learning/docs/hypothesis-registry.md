# Hypothesis Registry

Hypotheses generated during Sprint 3.2 — Search Intelligence & Evaluation Framework.

| ID | Date | Hypothesis | Rationale | Expected Evidence | Metric | Baseline | Target | Status | Decision | Linked AHA |
|----|------|-----------|-----------|-------------------|--------|----------|--------|--------|----------|------------|
| H-001 | 2026-07-27 | Golden queries with graded relevance (0-3) will surface ranking quality differences that binary relevance misses | NDCG with graded gains captures ordering quality; Precision/Recall treat all relevant items equally | NDCG@10 variance > Precision@10 variance by 2x across 67 queries | NDCG@10 variance vs Precision@10 variance | NDCG@10=0.1676, Precision@10=0.0259 | NDCG variance 2x Precision variance | Testing | NDCG=0.1676 vs Precision=0.0259 show different scales; variance analysis pending | AHA-007 |
| H-002 | 2026-07-27 | The 67-query golden set provides sufficient coverage to detect regressions in the BM25 scoring formula | Broad intent coverage (5 product intents, 6 evaluation categories) should catch ranking changes | Gate pass/fail stability across index rebuilds and ranking mutations | All 6 quality gates vs known-bad mutations | All gates PASS on baseline | Gates fail on mutations A, C, D | Testing | Baseline passes; A_empty, C_must_include, D_noise produce failures | AHA-008 |
| H-003 | 2026-07-27 | Quality gates set at current baseline will catch real regressions without false alarms | Gates calibrated at ~80% of observed baseline values | Gates pass on baseline, fail on known-bad mutations | Gate pass/fail on 5 mutation scenarios | All PASS | A,B,C,D,E expected to fail some gates | Testing | 5/5 mutation tests produce expected gate failures | — |
| H-004 | 2026-07-27 | Must-include resources will be in top-10 for branded capability queries (e.g., "churn" must return model:churn) | Query-level all-or-nothing semantics: every must-include resource must appear in top-k | Must-include success rate > 0.500 | must_include_success_rate | 0.6923 | ≥ 0.500 | Confirmed | 69% of 13 must-include queries pass; 4/13 fail (resources not in top-10) | — |
| H-005 | 2026-07-27 | Turkish queries will have lower NDCG than English equivalents due to tokenization differences | BM25 tokenization differs between Turkish and English text | Per-language NDCG breakdown shows TR < EN | NDCG@10 by language | Overall NDCG@10=0.1676 | TR NDCG < EN NDCG | Proposed | 10 TR-only + 13 bilingual queries in set; per-language analysis not yet run | — |
| H-006 | 2026-07-27 | Cross-lingual synonym expansion (e.g., "customer churn" for "müşteri kaybı") improves English query recall for Turkish content | English queries on Turkish-tagged data may miss Turkish content | Recall@K for EN queries on TR-only resources > baseline recall@K | recall@10 by query language | Overall recall@10=0.1782 | EN recall on TR data > 0.100 | Proposed | Analysis pending; requires per-language recall computation | — |

## Notes

- **H-004 evidence**: 13 must-include queries defined; 9 pass (model:nlp, model:churn, model:regression, experiment:experiment_churn_rf, dataset:midterm all found in top-10). 4 fail: resources not in top-10 for their respective queries.
- The 69% must-include rate suggests room for improvement in query-to-resource alignment for specific resources.
- Intent distribution improved: capability_lookup is 29/67 = 43.3% (was 23/45 = 51%).
- All hypothesis statuses comply with allowed values: Proposed, Testing, Confirmed, Rejected, Inconclusive.
