# Portfolio Platform

- Status: implemented bilingual multi-page Streamlit application.
- Problem/user: expose projects, evidence, inference, search, governance, and
  diagnostics to learners and technical reviewers.
- Origin: direct evidence for the current `portfolio_app.py` path begins at
  `377fbe8a`; modular churn milestone `12a2115e` predates that path and may be
  a predecessor; bilingual integration is `7c2c8fd9`.
- Entry point: `01-machine-learning/portfolio_app.py`.
- Architecture: page modules, service/loaders, i18n, registries, shared UI,
  cached artifacts, and session-state navigation.
- Inputs/outputs: forms, uploads, search queries, predictions, charts, tables,
  citations, and CSV/notebook downloads.
- Tests: `tests/test_portfolio_integrity.py` and related UI/search tests.
- Limitations: runtime depends on persisted assets; no usage telemetry exists.
- Evidence: source, root/ML READMEs, Git history, tests.
