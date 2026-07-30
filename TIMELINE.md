# Canonical Repository Timeline

The table is authoritative; the Mermaid view is a convenience. Dates are Git
commit dates.

| Date | Commit | Branch/phase evidence | Milestone | System | Significance | Task | Release | Confidence |
|---|---|---|---|---|---|---|---|---|
| 2026-07-21 | `c09fd946` | initial history | Repository initialized | Repository | Earliest tracked state | TASK-0001 | — | confirmed |
| 2026-07-21 | `bdbd1b2c` | churn phase | Churn completed | Churn | End-to-end training/artifacts/app | TASK-0002 | — | confirmed |
| 2026-07-21 | `5ed3f3a1` | ML portfolio | Regression and NLP added | Housing/NLP | Two task families added | TASK-0003 | — | confirmed |
| 2026-07-22 | `377fbe8a` | Trendyol V1 | Relevance pipeline | Trendyol | Classification/search foundation | TASK-0005 | — | confirmed |
| 2026-07-22 | `35357283` | V2 | Ranking challengers | Trendyol | Tree/XGBoost research | TASK-0005 | — | confirmed |
| 2026-07-22 | `4f168992` | V3 | Semantic/hybrid retrieval | Trendyol | E5 and fusion | TASK-0005 | — | confirmed |
| 2026-07-25 | `f70e398a` | V4 | End-to-end pipeline | Trendyol | Contracts/governance | TASK-0005 | — | confirmed |
| 2026-07-25 | `4db73a6b` | V5 | Cross-encoder reranking | Trendyol | Bounded reranking research | TASK-0005 | — | confirmed |
| 2026-07-26 | `7c2c8fd9` | portfolio | Bilingual integration | Streamlit | Unified experience | TASK-0004 | — | confirmed |
| 2026-07-27 | `a5101023` | search workspace | Repository search | Portfolio | Resource discovery | TASK-0006 | — | confirmed |
| 2026-07-27 | `78942d7b` | evaluation | Quality framework | Search | Golden queries/gates | TASK-0007 | — | confirmed |
| 2026-07-29 | `3e9be63d` | Copilot V1 | Grounded assistant | Copilot | Read-only repository Q&A | TASK-0008 | — | confirmed |
| 2026-07-29 | `7de65f19` | Copilot V1 | Canonical evaluation | Copilot | Release gates | TASK-0008 | — | confirmed |
| 2026-07-29 | `1064814e` | V1 hotfix | Page integration repair | Copilot | Release blocker fixed | TASK-0009 | `ai-project-copilot-v1.0.0` | confirmed |
| 2026-07-29 | `75929c01` | V2 Sprint 1A | Retrieval coverage | Copilot | 19/28 | TASK-0010 | — | confirmed |
| 2026-07-30 | `df3171ed` | V2 Sprint 1B | Filename stem | Copilot | 22/28 | TASK-0010 | — | confirmed |
| 2026-07-30 | `17b512fb` | V2 Sprint 2 | Phrase aliases | Copilot | 23/28 | TASK-0011 | — | confirmed |
| 2026-07-30 | `e3bbaf43` | V2 Sprint 3 | File intent | Copilot | 24/28 | TASK-0012 | — | confirmed |
| 2026-07-30 | `ae7d9404` | docs branch base | Knowledge System V1 | Documentation | 103-file initial system | TASK-0013 | — | confirmed |
| 2026-07-30 | working tree | Documentation Sprint D1 | Knowledge System V1.1 | Documentation | Book/dashboard/tooling expansion | TASK-0013 | — | confirmed |

```mermaid
flowchart LR
  A[Repository] --> B[Churn]
  B --> C[Regression and NLP]
  C --> D[Trendyol V1-V5]
  D --> E[Bilingual Portfolio]
  E --> F[Repository Search]
  F --> G[Evaluation]
  G --> H[Copilot V1]
  H --> I[V2 Sprints 1A-3]
  I --> J[Knowledge System V1/V1.1]
```

