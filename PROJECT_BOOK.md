# Engineering the Türkiye Yapay Zekâ Akademisi Repository

## Purpose and method

This is the canonical living technical book for the repository. It summarizes
rather than replaces project, task, ADR, experiment, failure, metric, and
source records. Historical claims require tracked evidence; inference and
unknowns are labeled. See [the evidence method](docs/project/scope.md),
[timeline](TIMELINE.md), and [claims ledger](docs/publication/article-claims-and-evidence.md).

## Table of contents

- [Part I — Foundation](#part-i--foundation)
- [Part II — Early machine learning](#part-ii--early-machine-learning)
- [Part III — Search and ranking research](#part-iii--search-and-ranking-research)
- [Part IV — Streamlit and product integration](#part-iv--streamlit-and-product-integration)
- [Part V — Repository search](#part-v--repository-search)
- [Part VI — AI Project Copilot](#part-vi--ai-project-copilot)
- [Part VII — Engineering methodology](#part-vii--engineering-methodology)
- [Part VIII — Knowledge infrastructure](#part-viii--knowledge-infrastructure)
- [Part IX — Future work](#part-ix--future-work)

## Part I — Foundation

### 1. Why the repository exists — Requires author confirmation

Git proves an academy-oriented AI/search portfolio, not the owner's pre-Git
motivation. Evidence: [vision](docs/project/vision.md). Open question: what
personal, educational, or hiring goals preceded `c09fd946`?

### 2. Repository scope and engineering method — Confirmed

The tracked system spans ML, data science, search, Streamlit, evaluation, and
Copilot. Evidence: [repository map](docs/project/repository-map.md). Lesson:
planned scaffolds must remain distinct from delivered capability.

### 3. Evidence and historical reconstruction — Partial reconstruction

The confirmed Git window is 2026-07-21 through 2026-07-30. Evidence:
[historical reconstruction](docs/project/historical-reconstruction.md) and
[TIMELINE.md](TIMELINE.md). Pre-Git history remains unknown.

### 4. Initial constraints and design principles — Partial reconstruction

Current code demonstrates persisted artifacts, bounded local runtime, explicit
evaluation, and limitations. Original rationale is only partly recorded. See
[ADR-0001](docs/engineering/decisions/ADR-0001-persisted-artifact-runtime.md).

## Part II — Early machine learning

### 5. Customer churn prediction — Confirmed

An end-to-end classification pipeline compares four model families and selects
Logistic Regression. Evidence: [project](docs/projects/customer-churn.md) and
[TASK-0002](docs/engineering/tasks/TASK-0002-churn-project.md). Lesson: persist
preprocessing with the model. Open question: complete upstream licensing.

### 6. California housing regression — Confirmed

Random Forest is selected over Gradient Boosting, with RMSE 0.5121 and R²
0.8087. Evidence: [project](docs/projects/housing-regression.md).

### 7. Sentiment analysis — Confirmed

TF-IDF with MultinomialNB reaches F1 0.8212 on the tracked UCI dataset.
Evidence: [project](docs/projects/sentiment-nlp.md).

### 8. Data preparation and persisted artifacts — Confirmed

Training scripts own cleaning, splitting, comparison, final evaluation, and
persistence; runtime services load bounded artifacts. Evidence:
[model lifecycle](docs/architecture/model-lifecycle.md) and ADR-0001.

### 9. Lessons from early model development — Partial reconstruction

Confirmed lessons concern split discipline, reproducible preprocessing, and
honest limitations. See [LESSONS.md](LESSONS.md). Author reflection is still
required for choices not recorded in source or reports.

## Part III — Search and ranking research

### 10. Trendyol relevance V1 — Confirmed

V1 establishes TF-IDF relevance classification and tracked model artifacts.
Evidence: [Trendyol project](docs/projects/trendyol-search-relevance.md).

### 11. Ranking challengers — Confirmed

V2/V2.1 evaluate linear, tree, HistGradientBoosting, and XGBoost candidates
without equating research leadership with runtime promotion. Evidence:
[model inventory](docs/models/model-inventory.yaml).

### 12. Semantic retrieval — Confirmed

Multilingual E5 is implemented behind a local asset boundary and underperforms
TF-IDF standalone on the measured cohort. Evidence: EXP-0001 and FAIL-0001.

### 13. Hybrid retrieval — Confirmed

RRF combines complementary lexical/semantic lists and becomes the V4
retrieval-only research policy. Evidence:
[EXP-0001](docs/engineering/experiments/EXP-0001-trendyol-retrieval.md).

### 14. Cross-encoder reranking — Confirmed

V5 reranks a bounded Hybrid RRF pool and reports NDCG@10 0.6785; it remains not
production promoted. Evidence: [project record](docs/projects/trendyol-search-relevance.md).

### 15. Evaluation and benchmark discipline — Confirmed

Group-safe splits, multi-seed comparisons, bootstrap intervals, Recall@K,
NDCG, MRR, latency, and non-promotion decisions are preserved. Evidence:
[evaluation methodology](docs/evaluation/methodology.md).

### 16. Rejected search approaches — Confirmed

Standalone semantic promotion and unsafe broad retrieval changes were rejected
on measured evidence. See [rejected approaches](docs/research/rejected-approaches.md).

## Part IV — Streamlit and product integration

### 17. From scripts and notebooks to applications — Partial reconstruction

Git shows standalone apps followed by unified integration; exact design
motivation requires confirmation. Evidence: TASK-0002–TASK-0004.

### 18. Standalone Streamlit applications — Confirmed

Churn, housing, and sentiment each have standalone application entry points.
Evidence: [interface inventory](docs/interfaces/streamlit-applications.md).

### 19. Unified bilingual portfolio — Confirmed

The current application provides shared navigation, i18n, pages, services, and
evidence views. Evidence: [portfolio project](docs/projects/portfolio-platform.md).

### 20. Navigation, state, caching, and runtime loading — Confirmed

Session state coordinates navigation and user flows; cached loaders isolate
data/model resources. Evidence: [Streamlit architecture](docs/architecture/streamlit-architecture.md).

### 21. UX and runtime stabilization — Confirmed

Multiple 2026-07-26 commits repair runtime integrity, page separation, i18n,
and visual analytics. Evidence: [timeline](TIMELINE.md). Open question: which
changes were driven by deployed-user feedback versus local review?

## Part V — Repository search

### 22. Repository indexing — Confirmed

The portfolio builds a local resource index for projects, models, notebooks,
experiments, and documents. Evidence: [repository search project](docs/projects/repository-search-evaluation.md).

### 23. Query intent and file discovery — Confirmed

Intent and structural evidence route repository questions; Sprint 3 proves an
intent error can masquerade as ranking failure. Evidence: FAIL-0003.

### 24. Retrieval evaluation — Confirmed

Offline evaluation measures precision, recall, ranking quality, coverage, and
changes. Evidence: TASK-0007 and [metric definitions](docs/evaluation/metric-definitions.md).

### 25. Golden queries and quality gates — Confirmed

Protected golden inputs and mutation-tested gates define reproducible review.
Evidence: [benchmark integrity](docs/evaluation/benchmark-integrity.md).

## Part VI — AI Project Copilot

### 26. Copilot vision — Confirmed

Copilot answers repository questions using local evidence and citations.
Evidence: [Copilot project](docs/projects/ai-project-copilot.md).

### 27. Copilot V1 architecture — Confirmed

V1 combines safe indexing, intent classification, deterministic retrieval,
extractive answers, citation validation, and memory. Evidence: TASK-0008.

### 28. Read-only and repository-grounded design — Confirmed

Allowed repository paths, secret exclusion, and absence of shell execution
bound the assistant. Evidence: [ADR-0002](docs/engineering/decisions/ADR-0002-read-only-copilot.md).

### 29. Citation and unsupported-claim controls — Confirmed

Canonical evaluation separates citation validity, citation precision, concept
recall, and unsupported claims. Evidence: evaluation architecture.

### 30. V1 release and hotfix — Confirmed

The V1 release tag points to the scoped Streamlit integration hotfix
`1064814e`. Evidence: TASK-0009 and `metrics/releases.json`.

### 31. V2 Sprint 1A — Confirmed

Low-risk vocabulary coverage raises Retrieval@5 to 19/28. Evidence: TASK-0010.

### 32. V2 Sprint 1B — Confirmed

An exact filename-stem signal applied once per file raises the result to 22/28.
Evidence: EXP-0002 and the Sprint 1B report.

### 33. V2 Sprint 2 — Confirmed

Strict contiguous configured phrases recover GQ29 without substring matching.
Evidence: TASK-0011.

### 34. V2 Sprint 3 — Confirmed

Explicit file-location intent precedence recovers GQ12. Evidence: TASK-0012
and FAIL-0003.

### 35. Current 24/28 baseline — Confirmed

Current metrics are Retrieval@5 24/28, intent 29/30, citation validity and
precision 30/30, concept recall 39/48, and unsupported claims 0/30. Evidence:
[STATUS.md](STATUS.md) and `metrics/history.json`.

### 36. Remaining problems — Confirmed

OPEN-GQ03, OPEN-GQ11, OPEN-GQ19, and OPEN-GQ25 remain unresolved. They cover
compound evidence, Turkish morphology, dropped oversized chunks, and weak
documentation ranking. Planned solutions are not accepted decisions.

## Part VII — Engineering methodology

### 37. Zero-regression engineering — Confirmed

Every narrow gain is compared with prior hits; silent regressions are rejected.
Evidence: [ADR-0003](docs/engineering/decisions/ADR-0003-protected-zero-regression-evaluation.md).

### 38. Counterfactual analysis — Confirmed

Candidate rules are modeled before production edits when practical. Evidence:
Sprint 1B–3 reports. Lesson: measure scope, not only target rank.

### 39. Failure-driven development — Confirmed

Hidden dependencies, missing assets, and intent collision became durable
failure records. Evidence: `docs/engineering/failures/`.

### 40. Protected evaluation assets — Confirmed

Golden, matcher, evaluator, and gates require explicit governance. Evidence:
benchmark integrity and ADR-0003.

### 41. Human–AI collaboration — Partial reconstruction

The current governed workflow is documented; historical attribution remains
incomplete. Evidence: [AI_COLLABORATION.md](AI_COLLABORATION.md).

### 42. Branch, review, and commit discipline — Confirmed current policy

Agents inspect state, preserve user work, validate scope, and do not commit
without human approval. Evidence: [AGENTS.md](AGENTS.md).

## Part VIII — Knowledge infrastructure

### 43. Engineering Knowledge System — Confirmed

V1 establishes a handbook, evidence archive, journal, registries, and agent
context; V1.1 adds dashboards and generation tooling. Evidence: TASK-0013.

### 44. Tasks, ADRs, experiments, and failures — Confirmed

Stable IDs create traceable links between problem, evidence, decision, result,
and lesson. Evidence: `docs/engineering/`.

### 45. Machine-readable metrics — Confirmed

Confirmed values live in `metrics/history.json`; unrelated metrics are never
presented as directly comparable. See [dashboard](metrics/dashboard.md).

### 46. Knowledge graph — Confirmed

YAML nodes and relationships connect projects, models, tasks, failures,
lessons, metrics, and open problems. See [generated summary](docs/architecture/diagrams/generated/knowledge-graph-summary.md).

### 47. Publication and reproducibility — Planned

Claims, figures, and article sections are mapped to evidence, but the final
article is not written. Evidence: `docs/publication/`.

## Part IX — Future work

### 48. Copilot V2 remaining sprints — Planned

Research may address remaining misses only through approved, general,
zero-regression hypotheses. See [open questions](docs/research/open-questions.md).

### 49. Copilot V3–V5 — Requires author confirmation

No tracked product definition exists. Names are roadmap placeholders, not
implemented systems.

### 50. Documentation automation — Confirmed initial tooling

V1.1 generates and validates the knowledge graph and metrics dashboard locally.
Open question: whether CI should enforce these checks.

### 51. Research questions — Planned

Open areas include Turkish morphology, oversized chunk splitting, portable
semantic assets, and data provenance. See the research registry.

### 52. Publication plan — Planned

The article series will use only verified claims, figures, metrics, and explicit
limitations. See [publication outline](docs/publication/medium-article-outline.md).

