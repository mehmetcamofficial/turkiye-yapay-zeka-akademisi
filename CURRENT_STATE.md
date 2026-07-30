# Current State

Last documentation update: 2026-07-30, Documentation Sprint D1.

## Snapshot

- Current phase: Engineering Knowledge System V1.1 in review.
- Stable tagged release: `ai-project-copilot-v1.0.0` at `1064814e`.
- Latest integrated Copilot work: V2 Sprint 3, merged by `ae7d9404`.
- Active work: living-book, dashboard, graph, metrics, and publication upgrade.
- Current working branch: `docs/engineering-knowledge-system-v1`.

## Completed systems

- Customer churn classification with training, artifacts, and Streamlit UI.
- California housing regression with persisted model and evaluation outputs.
- UCI sentiment classification with TF-IDF and persisted pipeline.
- Trendyol search-relevance research from V1 classification through V5
  cross-encoder reranking.
- Bilingual multi-page Streamlit portfolio and repository search workspace.
- Search evaluation framework and repository-grounded AI Project Copilot.
- Data-science midterm workflow and Trendyol data profiling.

## Confirmed current metrics

- Copilot Retrieval@5: 24/28.
- Copilot intent accuracy: 29/30.
- Copilot citation validity and precision: 30/30 each.
- Copilot required concept recall: 39/48.
- Copilot unsupported claims: 0/30.
- Public tracked tests at Sprint 3 validation: 302 passed.

The canonical source for metric history is `metrics/history.json`.

## Open problems and risks

- Copilot misses GQ03, GQ11, GQ19, and GQ25.
- Some semantic tests require ignored local model assets.
- Repository-root pytest collects a browser script lacking its `page` fixture.
- Group C research files remain untracked and outside public scope.
- Clustering, deployment, and the data-science final project are planned or
  scaffolded, not evidenced as completed systems.
- Historical rationale before 2026-07-21 requires author confirmation.

## Protected files

Golden data, canonical matcher, official evaluator, release gates, model
artifacts, safety boundaries, and tracked evidence outputs require explicit
scope. See `AGENTS.md` and `docs/evaluation/benchmark-integrity.md`.

## Next approved action

Review and reconcile Knowledge System V1.1. No product or model implementation
is approved by this document. Human status: [STATUS.md](STATUS.md); generated
views: [graph summary](docs/architecture/diagrams/generated/knowledge-graph-summary.md)
and [metrics dashboard](metrics/dashboard.md).

## Unresolved author questions

See `docs/publication/unresolved-author-questions.md`.
