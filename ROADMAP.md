# Project Roadmap — Türkiye Yapay Zeka Akademisi

This roadmap separates product, engineering, research, documentation, and
publication work. Existing milestone tables below remain historical evidence.

## Product roadmap

- Maintain the integrated portfolio and current model/search capabilities.
- Define future Copilot V3–V5 scope only after author approval.

## Engineering roadmap

- Make asset-dependent tests explicitly selectable and reproducible.
- Resolve repository-root browser-script collection behavior.
- Preserve protected evaluation semantics and zero-regression review.

## Research roadmap

- Investigate bounded Turkish morphology and oversized-chunk handling.
- Continue Trendyol retrieval/reranking only with unchanged evaluation cohorts.

## Documentation roadmap

- Obtain author confirmation for pre-Git history and architectural rationale.
- Add reviewed diagrams and reconcile historical test/release counts.
- Review Knowledge System V1.1 and decide whether graph/metric validation should
  become a CI documentation gate.
- Capture only verified assets listed in `docs/assets/manifest.yaml`.

## Publication roadmap

- Convert only evidenced claims into the planned technical article series.
- Create figures with source/commit/metric metadata.
- Use generated graph and metrics views as publication sources after review.

> Engineering-focused portfolio demonstrating ML & IR systems. Prioritizes reproducibility, evaluation rigor, and production-readiness signals.

---

## ✅ Completed

| Milestone | Deliverable |
|-----------|-----------|
| Sprint 1 | Command Center, Notebook Workflows, NLP Classification |
| Sprint 2 | Model Registry, Artifact Health, Churn Dashboard |
| Search Relevance | V1–V5 pipeline (TF-IDF → Cross-Encoder) |

---

## 🛠 In Progress

- Streamlit polish (micro-interactions, dark mode)
- Documentation audit (this sprint)

---

## 🎯 Future

- SVG icon system (replace emoji)
- Pill-chip filters (replace selectbox)
- GitHub Actions CI/CD
- Usage analytics telemetry
- FastAPI backend for inference

---

## 📈 Priorities

1. Evaluation rigor — All models have metrics & baselines
2. Reproducibility — Fixed seeds, pinned revisions
3. UX polish — Product-grade UI, not ML demo
4. Governance — Artifacts, health, decisions documented
5. Open source — License, contributing, issues, roadmap
