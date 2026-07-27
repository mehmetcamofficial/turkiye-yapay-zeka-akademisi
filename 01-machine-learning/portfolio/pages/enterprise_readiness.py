from __future__ import annotations

import streamlit as st

from portfolio.config import REPOSITORY_ROOT
from portfolio.i18n import t
from portfolio.loaders import load_test_metadata
from portfolio.ui_components import hero_panel, kpi_grid, kpi_grid_mixed, section_heading, status_badge


def render() -> None:
    hero_panel(
        title=t("nav_enterprise_readiness"),
        subtitle=t("subtitle_enterprise_readiness"),
        kicker=t("section_model_ops"),
    )

    section_heading(t("capability_matrix"), t("capability_matrix_desc"))
    kpi_grid_mixed([
        (t("capability_real_data"), status_badge("verified"), t("status_operational")),
        (t("capability_trained_models"), status_badge("verified"), t("status_operational")),
        (t("capability_live_inference"), status_badge("verified"), t("status_validated")),
        (t("capability_hybrid_search"), status_badge("verified"), t("status_validated")),
        (t("capability_cross_encoder"), status_badge("verified"), t("status_validated")),
        (t("capability_model_registry"), status_badge("available"), t("status_operational")),
        (t("capability_artifact_health"), status_badge("available"), t("status_operational")),
        (t("capability_cloud_deployment"), status_badge("available"), t("status_operational")),
        (t("capability_production_api"), status_badge("roadmap"), t("status_roadmap")),
        (t("capability_auth_sso"), status_badge("roadmap"), t("status_roadmap")),
        (t("capability_observability"), status_badge("roadmap"), t("status_roadmap")),
        (t("capability_horizontal_scaling"), status_badge("roadmap"), t("status_roadmap")),
        (t("capability_online_ab"), status_badge("roadmap"), t("status_roadmap")),
    ])

    section_heading(t("enterprise_snapshot"))
    st.markdown("""
    <div class="card" style="border-left:4px solid #4f46e5;margin-top:0.5rem">
    <h3>Enterprise Readiness Assessment</h3>
    <p>
    The platform demonstrates operational capabilities in core ML inference, search ranking,
    and model management. Enterprise-grade production capabilities (API, authentication,
    observability, horizontal scaling, online A/B validation) are on the roadmap.
    </p>
    </div>
    """, unsafe_allow_html=True)

    section_heading(t("deployment_architecture"))
    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"**{t('runtime_boundaries')}**")
        st.caption("Streamlit Community Cloud · CPU inference · Bounded 5,000-product catalogue")
    with cols[1]:
        st.markdown(f"**{t('security_boundaries')}**")
        st.caption("No authentication · No authorization · Public deployment")
    with cols[2]:
        st.markdown(f"**{t('data_governance')}**")
        st.caption("Bundled artifacts · No raw data in cloud · Model files in git LFS")

    section_heading(t("production_readiness_gap"))
    gap_items = [
        (t("production_api_gap"), t("production_api_roadmap")),
        (t("security_gap"), t("auth_roadmap_active")),
        (t("observability_gap"), t("observability_roadmap_active")),
        (t("not_production_system") + " · " + t("no_production_traffic"), ""),
        (t("no_sla") + " · " + t("no_online_ab"), ""),
        (t("scaling_roadmap"), t("scaling_roadmap_active")),
    ]
    for title, desc in gap_items:
        st.markdown(f"- **{title}** {desc}")

    metadata = load_test_metadata()
    if metadata:
        verified_at = metadata.get("verified_at", "—")
        total = metadata["total"]
        st.success(f"Tests: {total['passed']} passing, {total['failed']} failed — Verified: {verified_at}")
    else:
        st.warning(t("test_outdated"))
