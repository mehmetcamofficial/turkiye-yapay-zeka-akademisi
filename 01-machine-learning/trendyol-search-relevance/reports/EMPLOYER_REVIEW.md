# Employer Review

## Recruiter review

Strengths: the Overview now identifies Mehmet Cam, names four working projects, exposes professional links and routes directly to the Trendyol demo and Registry. Evidence is concrete—live inference, artifact reload, group-safe validation and exact metrics. Remaining weakness: this is a local Streamlit experience; public hosting availability is not claimed.

Recruiter path: Overview → Featured Trendyol comparison → Live demo → About Mehmet.

## Technical hiring-manager review

Strengths: exact split strategy, zero overlap, feature families, classification/ranking separation, artifacts, bootstrap uncertainty, hard-negative experiments and non-promotion decisions are visible. Registry and Artifact Health distinguish runtime compatibility from model quality. Remaining weakness: CatBoost and semantic retrieval are not evaluated; V1's historical training snapshot prevents treating its same-group score as a fully independent causal comparison.

Technical path: Overview → Trendyol Evidence → Engineering → Registry → Artifact Health → Repository Guide.

Artifact clarification: HistGradientBoosting is the V2.1 Best Research Candidate (mean F1 0.753935, standard deviation 0.006349, 95% CI 0.746053–0.761817), but it is Not Promoted and not persisted because the selected trained object was unavailable after repeated-seed aggregation without retraining. Registry and Artifact Health expose this missing research artifact honestly.

## Product-stakeholder review

Strengths: the search problem, bounded live capability, governance boundary and roadmap are stated without fabricated conversion impact. The demo separates a deployable V1 classifier from experimental holdout reranking. Remaining weakness: candidate retrieval, online latency/service-level objectives and A/B testing are outside scope.

Product path: Overview → Trendyol Executive & Live → Business Problem → Governance & Roadmap.

## V3 retrieval extension

V3/V3.1 demonstrates that candidate retrieval, relevance classification and ranking are distinct search-system stages. Recruiters see a bounded live lexical, semantic and hybrid demo. Technical reviewers see pinned multilingual E5 embeddings, catalogue fingerprints, NumPy cosine indexing, validation-only fusion tuning, Recall@K, latency/index cost and group-safe statistical evaluation. Product and search reviewers see explicit catalogue scope and incomplete-judgment risks. Standalone semantic retrieval underperformed; RRF became the Best Research Candidate at Recall@50 `0.831392` but remains Not Promoted because uncertainty and bounded scope remain.

## Confusing areas found and changed

- Replaced eighteen equal-priority Trendyol tabs with five guided groups.
- Replaced generic platform totals with repository-derived status and evidence.
- Separated champion, classifier challenger and ranker decisions.
- Added explicit “why not promoted” explanations.
- Reframed About as a verified professional profile without unsupported employment claims.

## Evidence visible in the UI

Term-group validation, deterministic samples, persisted artifacts, reload compatibility, single/batch inference, checksums, classification/ranking metrics, confidence intervals, error analysis, raw-data exclusion and champion/challenger governance.
