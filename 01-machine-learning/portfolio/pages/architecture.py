from __future__ import annotations

import streamlit as st

from portfolio.i18n import t
from portfolio.ui_components import hero_panel, section_heading


def render() -> None:
    hero_panel(
        title=t("nav_architecture"),
        subtitle=t("subtitle_architecture"),
        kicker=t("section_search"),
    )

    st.markdown(
        """
```mermaid
flowchart LR
    A[User Query] --> B[Validation & Normalization]
    B --> C[Lexical Retrieval]
    B --> D[Semantic Retrieval]
    C --> E[Hybrid RRF Fusion]
    D --> E
    E --> F[Top-K Candidates]
    F --> G[Cross-Encoder Reranker]
    G --> H[Deterministic Ranking]
    H --> I[Streamlit Results]
    G -. failure .-> J[Retrieval-Only Fallback]
    J --> H
    K[Artifact Registry] --> C
    K --> D
    K --> G
    L[Artifact Health] --> K
```
""",
        unsafe_allow_html=True,
    )

    section_heading("Design Properties")
    st.markdown(
        """
- **Bounded candidate generation** — retrieval produces a fixed-size pool
- **Retrieval/reranking separation** — reranking reorders only, cannot improve recall
- **Lazy model loading** — models loaded per-page, not at startup
- **Explicit fallback** — every component degrades visibly rather than fabricating scores
- **Metadata-first Registry** — reads actual paths and metrics from persisted outputs
- **Worker isolation** — PyTorch and XGBoost runtimes in separate processes
- **Immutable model revisions** — HuggingFace revisions, not mutable `latest` tags
"""
    )

    section_heading("Platform Layers")
    st.markdown(
        """
1. **Portfolio App** — Streamlit entry point with navigation, localization, error handling
2. **Page Modules** — Individual pages for each project and feature
3. **Registry** — Data-driven project and artifact status from real files
4. **Loaders** — Cached, failure-tolerant artifact loading
5. **UI Components** — Reusable design system components
6. **Data Science** — Trendyol profile, inventory, quality, and schema analysis
"""
    )
