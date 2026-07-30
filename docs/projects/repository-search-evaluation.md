# Repository Search and Evaluation

- Status: implemented repository-resource search and offline quality framework.
- Origin: search workspace `a5101023`; evaluation framework `78942d7b`.
- Entry points: `portfolio/search_index.py`, `portfolio/search_service.py`,
  `evaluation/search/cli.py`, and evaluation modules.
- Algorithms: BM25-style repository index plus metric functions for precision,
  recall, NDCG, MRR, coverage, and ranking differences.
- Data: project registries, repository resources, golden queries, quality gates.
- UI: Search Workspace and Search Intelligence pages.
- Tests: search evaluation, quality-gate mutation, suggested-query tests.
- Limitations: repository-specific corpus and protected benchmark semantics.
- Evidence: code, golden queries, reports, commits `a5101023`/`78942d7b`.

