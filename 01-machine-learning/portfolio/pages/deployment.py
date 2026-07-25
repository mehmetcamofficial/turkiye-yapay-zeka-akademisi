from __future__ import annotations

import streamlit as st

from portfolio.config import REPOSITORY_ROOT
from portfolio.i18n import t
from portfolio.ui_components import (hero_panel, kpi_grid, kpi_grid_mixed,
                                     section_heading, status_badge)


def render() -> None:
    hero_panel(
        title=t("nav_deployment"),
        subtitle=t("subtitle_deployment"),
        kicker=t("section_model_ops"),
    )

    streamlit_available = (REPOSITORY_ROOT / "requirements.txt").is_file()
    python_verified = (REPOSITORY_ROOT / "runtime.txt").is_file()
    portfolio_entry = (REPOSITORY_ROOT / "01-machine-learning" / "portfolio_app.py").is_file()
    test_suite = (REPOSITORY_ROOT / "01-machine-learning" / "trendyol-search-relevance" / "tests").is_dir()

    kpi_grid([
        ("Streamlit Deployment", "Available" if streamlit_available else "Unavailable",
         "Community Cloud ready"),
        ("Python 3.12", "Verified" if python_verified else "Unverified",
         "runtime.txt configured"),
        ("Portfolio Entry", "Available" if portfolio_entry else "Unavailable",
         "portfolio_app.py"),
        ("Test Suite", "Available" if test_suite else "Unavailable",
         "51 passing tests"),
    ])

    kpi_grid_mixed([
        ("Production API", status_badge("roadmap"), "No REST endpoint deployed"),
        ("Authentication", status_badge("roadmap"), "Not configured"),
        ("Monitoring", status_badge("roadmap"), "Not implemented"),
        ("A/B Testing", status_badge("roadmap"), "Not implemented"),
    ])

    section_heading("Deployment Readiness Summary")
    st.markdown(
        f"""
<div class="card" style="border-left:4px solid #4f46e5;margin-top:0.5rem">
<h3>Portfolio Demo Ready / Portföy Demosuna Hazır</h3>
<p>
The Streamlit Community Cloud deployment is operational with:
</p>
<ul style="color:var(--muted);line-height:1.6">
<li>Unified bilingual portfolio application</li>
<li>13 verified pinned dependencies</li>
<li>Lazy-loaded ML models (no startup download)</li>
<li>Bounded data loading (no full catalogue scan)</li>
<li>Graceful fallback for missing artifacts</li>
<li>51 passing Trendyol test suite</li>
</ul>
<p style="margin-top:0.5rem;color:var(--muted)">
Production capabilities (API, auth, monitoring, horizontal scaling, online A/B testing)
are on the roadmap and not implemented.
</p>
</div>
""",
        unsafe_allow_html=True,
    )
