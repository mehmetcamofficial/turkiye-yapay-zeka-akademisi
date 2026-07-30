# AI Project Copilot

- Status: V1 released; V2 Sprints 1A–3 merged. V3–V5 are not yet defined by
  tracked implementation plans.
- Problem/user: answer repository questions using local evidence and citations.
- Origin: `3e9be63d`; canonical evaluation `7de65f19`; V1 tag `1064814e`.
- Entry point: `portfolio/pages/project_copilot.py`.
- Architecture: safe indexer, intent classifier, lexical/structural retriever,
  extractive answer generation, citation validation, and conversation memory.
- Data: allowed tracked repository content and `copilot_golden.json`.
- Safety: read-only, repository-bound paths, secret exclusion, no shell surface.
- Evolution: Sprint 1A alias coverage; 1B filename-stem boost; Sprint 2 strict
  phrase activation; Sprint 3 file-location intent precedence.
- Current metrics: Retrieval@5 24/28, intent 29/30, citation validity/precision
  30/30, concept recall 39/48, unsupported claims 0/30.
- Limitations: four remaining canonical misses; lexical/morphology/chunk gaps.
- Evidence: source/tests, official results, V2 engineering reports, Git history.

