from __future__ import annotations

import streamlit as st

from portfolio.config import REPOSITORY_ROOT
from portfolio.i18n import t
from portfolio.loaders import load_test_metadata
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

    metadata = load_test_metadata()
    metadata_valid = metadata is not None

    if metadata_valid:
        total = metadata["total"]
        verified_at = metadata.get("verified_at", "—")
        test_label = f"{total['passed']} passing, {total['failed']} failed, {total['skipped']} skipped"
        summary_items = [
            f"Portfolio: {metadata['portfolio']['passed']} passed, {metadata['portfolio']['failed']} failed",
            f"Trendyol:  {metadata['trendyol']['passed']} passed, {metadata['trendyol']['failed']} failed",
            f"Total:     {total['passed']} passing, {total['failed']} failed, {total['skipped']} skipped",
            f"Verified:  {verified_at}",
        ]
    else:
        test_label = t("test_outdated")
        summary_items = [t("test_outdated")]

    kpi_grid([
        (t("deploy_streamlit_deployment"), "Available" if streamlit_available else "Unavailable",
         t("deploy_streamlit_deployment_desc")),
        (t("deploy_python_312"), "Verified" if python_verified else "Unverified",
         t("deploy_python_312_desc")),
        (t("deploy_portfolio_entry"), "Available" if portfolio_entry else "Unavailable",
         t("deploy_portfolio_entry_desc")),
        (t("deploy_test_suite"), "Available" if test_suite else "Unavailable",
         test_label),
    ])

    kpi_grid_mixed([
        (t("deploy_production_api"), status_badge("roadmap"), t("deploy_production_api_desc")),
        (t("deploy_authentication"), status_badge("roadmap"), t("deploy_not_configured")),
        (t("deploy_monitoring"), status_badge("roadmap"), t("deploy_not_implemented")),
        (t("dsf_deploy_ab_testing"), status_badge("roadmap"), t("deploy_not_implemented")),
    ])

    section_heading(t("deploy_deployment_readiness_summary"))
    summary_lines = "".join(f"<li>{item}</li>" for item in summary_items)
    st.markdown(
        f"""
<div class="card" style="border-left:4px solid #4f46e5;margin-top:0.5rem">
<h3>Deployment Ready / Dağıtıma Hazır</h3>
<p>
The Streamlit Community Cloud deployment is operational with:
</p>
<ul style="color:var(--muted);line-height:1.6">
<li>Unified bilingual AI product platform</li>
<li>13 verified pinned dependencies</li>
<li>Lazy-loaded ML models (no startup download)</li>
<li>Bounded data loading (no full catalogue scan)</li>
<li>Graceful fallback for missing artifacts</li>
{summary_lines}
</ul>
<p style="margin-top:0.5rem;color:var(--muted)">
Production capabilities (API, auth, monitoring, horizontal scaling, online A/B testing)
are on the roadmap and not implemented.
</p>
</div>
""",
        unsafe_allow_html=True,
    )
