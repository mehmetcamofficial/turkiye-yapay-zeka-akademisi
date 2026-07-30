# Repository Constitution for AI Agents

## Identity and first read

This repository is the Türkiye Yapay Zekâ Akademisi engineering portfolio: a
collection of machine-learning, data-science, search, Streamlit, evaluation,
and repository-assistant systems. It is both executable software and an
evidence archive.

Read in this order before meaningful work:

1. `AGENTS.md`
2. `CURRENT_STATE.md`
3. `README.md`
4. `docs/README.md`
5. the relevant file under `docs/projects/`
6. related task, ADR, experiment, and failure records
7. relevant source and tests

## Working principles

- Source, tests, Git history, tracked reports, and configuration outrank prose.
- Never invent history, rationale, metrics, provenance, licenses, or outcomes.
- Label uncertain claims as **Unknown**, **Not yet reconstructed**,
  **Requires author confirmation**, or **Inferred from repository evidence**.
- Keep facts, inference, plans, and rejected ideas visibly distinct.
- Prefer repository-relative links and one canonical source for each fact.
- Do not expose secrets, personal data, local absolute paths, ignored model
  caches, or private prompt transcripts.

## Repository map

- `01-machine-learning/`: predictive ML, Trendyol relevance, portfolio UI,
  search evaluation, and AI Project Copilot.
- `02-data-science/`: coursework, profiling, data governance, and planned final
  project material.
- `docs/`: canonical engineering knowledge system.
- `metrics/`: machine-readable confirmed metric and release history.
- `.github/`: contribution and pull-request templates.

See `docs/project/repository-map.md` for ownership and entry points.

High-level orientation views are `STATUS.md`, `TIMELINE.md`, `LESSONS.md`,
`AI_COLLABORATION.md`, and `DECISION_TREE.md`. Generated graph/metric views are
derived from canonical YAML/JSON and must be regenerated after source changes.

## Protected assets

Treat the following as protected unless a task explicitly authorizes changes:

- `01-machine-learning/evaluation/search/copilot_golden.json`
- `01-machine-learning/evaluation/search/canonical_match.py`
- `01-machine-learning/evaluation/search/official_evaluation.py`
- `01-machine-learning/evaluation/search/release_gates.yaml`
- model artifacts, tracked benchmark outputs, and evaluation contracts
- secret/path safety logic under `portfolio/copilot/`

Never weaken tests or evaluation semantics to make a gate pass. Benchmark IDs,
accepted target paths, or golden answers must not leak into production logic.

## Task workflow

1. Record branch, HEAD, tracked status, and relevant untracked files.
2. Read the project record and associated source/tests.
3. State the hypothesis, scope, invariants, and rollback condition.
4. Make the smallest authorized change.
5. Run focused tests, then proportional integration/evaluation checks.
6. Audit the diff and protected files.
7. Update the knowledge system.
8. Commit, push, tag, or open a PR only with explicit approval.

Git history is evidence. Do not rewrite it, discard user changes, or stage
unrelated files. Untracked research files belong to their author unless a task
explicitly places them in scope.

## Documentation update protocol

Every meaningful task updates:

- `CURRENT_STATE.md`
- the relevant project document
- one task record
- the current journal entry

When applicable, also update the ADR, experiment, failure, metric, model,
roadmap, release, project-book, or publication records. Every implementation
report must include a “Documentation impact” section listing updated files and
why other record types were not required.

Use templates under `docs/templates/`. Stable IDs are `TASK-`, `ADR-`, `EXP-`,
and `FAIL-`. Reconstructed records declare `record_type: reconstructed` and a
confidence value; future work uses `record_type: live`.

## Test expectations

Use the narrowest deterministic tests first. For repository-wide changes,
verify syntax, Markdown links, YAML/JSON parsing, and `git diff --check`.
Model-dependent or research tests may require ignored local assets; report
that condition rather than fabricating a pass.
