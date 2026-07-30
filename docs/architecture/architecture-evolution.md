# Architecture Evolution

## Stage 1 — Standalone model workflows

- Evidence: `bdbd1b2c`, `5ed3f3a1`; TASK-0002/TASK-0003.
- Components/flow: dataset → preprocessing → split/train/evaluate → persisted
  model and reports → standalone Streamlit app.
- Runtime: project-specific artifact loading.
- Limitation: duplicated app structure and separate navigation.
- Transition: broader portfolio integration.
- Confidence: confirmed; original motivation requires author confirmation.

```mermaid
flowchart LR
  D[Dataset] --> T[Training pipeline] --> M[Persisted model and reports] --> A[Standalone app]
```

## Stage 2 — Unified multi-page portfolio

- Evidence: `377fbe8a`, `7c2c8fd9`, TASK-0004, ADR-0001.
- Components/flow: project artifacts → shared loaders/services → navigation,
  i18n, and page renderers.
- Runtime: session-state navigation and cached data/model resources.
- Limitation: artifact availability and broad page surface.
- Transition: repository resources needed searchable navigation.
- Confidence: confirmed.

```mermaid
flowchart LR
  P[Project artifacts] --> S[Shared services] --> N[Navigation and i18n] --> U[Portfolio pages]
```

## Stage 3 — Search and evaluation workspace

- Evidence: `a5101023`, `78942d7b`; TASK-0006/TASK-0007.
- Components/flow: registries/files → index → search/results → offline golden
  evaluation and gates.
- Runtime: bounded local search with session-state navigation.
- Limitation: repository-specific corpus and protected benchmark semantics.
- Transition: grounded Q&A required answer and citation layers.
- Confidence: confirmed.

## Stage 4 — AI Project Copilot V1

- Evidence: `3e9be63d`, `7de65f19`, `1064814e`; TASK-0008/TASK-0009.
- Components/flow: safe chunks → intent/scoring → extractive answer → citation
  validation and conversation memory.
- Runtime: read-only, local, repository-bound, no shell execution.
- Limitation: lexical and chunk-evidence gaps.
- Transition: canonical misses motivated narrow V2 research.
- Confidence: confirmed.

## Stage 5 — Copilot V2 incremental evolution

- Evidence: `75929c01`, `df3171ed`, `17b512fb`, `e3bbaf43`.
- Components: aliases, exact filename stems, strict phrase activation, and
  file-location intent precedence; core architecture unchanged.
- Limitation: GQ03/GQ11/GQ19/GQ25 remain unresolved.
- Transition: durable context/evidence navigation became necessary.
- Confidence: confirmed.

## Stage 6 — Engineering Knowledge System

- Evidence: documentation working tree based at `ae7d9404`; TASK-0013.
- Components/flow: repository evidence → canonical records → deterministic
  graph/metrics views → human and AI review.
- Runtime: documentation-only Python tooling with no product dependency.
- Limitation: pre-Git rationale and future V3–V5 remain unknown.
- Confidence: confirmed for the created structure.

```mermaid
flowchart LR
  E[Source Git tests reports] --> C[Canonical docs YAML JSON] --> G[Generated views] --> H[Human and AI review]
```

