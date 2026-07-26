from __future__ import annotations
from html import escape

from portfolio.config import PORTFOLIO_VERSION, TEST_COUNT
from portfolio.data_science_registry import data_science_counts
from portfolio.i18n import t
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import (
    capability_card,
    command_hero,
    health_cards,
    navigate_to,
    pipeline_flow,
    quick_action_grid,
    section_heading,
    status_badge,
    status_strip,
    transparency_panel,
)


def _activity_entries() -> list[dict]:
    import streamlit as st
    return st.session_state.get("cc_activity_log", [])


def render() -> None:
    import streamlit as st


    counts = data_science_counts()
    profile_compat = counts.get("midterm", {}).get("schema_compatible", False)
    profile_fields = counts.get("midterm", {}).get("matched_fields", 0)
    total_fields = 10

    projects = get_project_registry()
    model_artifacts = sum(1 for p in projects if p.get("model_artifact_available"))
    report_count = sum(1 for p in projects if any(
        f.endswith(".md") or f.endswith(".csv") for f in p.get("expected_output_files", [])
    ))

    # ── Section 1: Premium Hero ──
    command_hero(
        title=t("command_center_title"),
        subtitle=t("command_center_subtitle"),
        badges=[
            (t("command_center_badge_local"), "local"),
            (t("command_center_badge_validated"), "validated"),
            (t("command_center_badge_architect"), "architect"),
        ],
        primary_cta_text=t("command_center_cta_search"),
        primary_cta_key=("section_search", "nav_search_intelligence"),
        secondary_cta_text=t("command_center_cta_models"),
        secondary_cta_key=("section_model_ops", "nav_registry"),
        test_count=TEST_COUNT,
        test_label=t("command_center_tests"),
    )

    # ── Section 2: Status Strip ──
    status_strip([
        (t("strip_models_label"), t("strip_models_value"), ""),
        (t("strip_tests_label"), t("strip_tests_value"), ""),
        (t("strip_sources_label"), t("strip_sources_value"), ""),
        (t("strip_runtime_label"), t("strip_runtime_value"), ""),
        (t("strip_validation_label"), t("strip_validation_value"), ""),
    ])

    # ── Section 3: System Health ──
    section_heading(t("health_title"))
    health_cards([
        (t("health_model_runtime"), "ready", t("health_model_runtime_primary"),
         t("health_model_runtime_detail")),
        (t("health_search_pipeline"), "ready", t("health_search_pipeline_primary"),
         t("health_search_pipeline_detail")),
        (t("health_data_readiness"), "ready", t("health_data_readiness_primary"),
         t("health_data_readiness_detail")),
        (t("health_validation_suite"), "ready", t("health_validation_suite_primary"),
         t("health_validation_suite_detail")),
        (t("health_artifact_registry"), "ready", t("health_artifact_registry_primary"),
         t("health_artifact_registry_detail")),
        (t("health_notebook_schema"), "partial" if not profile_compat else "ready",
         t("health_notebook_schema_primary"),
         t("health_notebook_schema_detail")),
    ])

    # ── Section 4: Capabilities ──
    section_heading(t("capabilities_title"))
    cap_cols = st.columns(3)
    capabilities = [
        ("nav_housing", "section_ml", "cap_housing_name", "cap_housing_category",
         "cap_housing_desc", "status_verified", "capability_cta_open"),
        ("nav_churn", "section_ml", "cap_churn_name", "cap_churn_category",
         "cap_churn_desc", "status_verified", "capability_cta_run"),
        ("nav_sentiment", "section_ml", "cap_sentiment_name", "cap_sentiment_category",
         "cap_sentiment_desc", "status_verified", "capability_cta_run"),
        ("nav_hybrid_retrieval", "section_search", "cap_hybrid_name", "cap_hybrid_category",
         "cap_hybrid_desc", "status_available", "capability_cta_explore"),
        ("nav_cross_encoder", "section_search", "cap_cross_encoder_name",
         "cap_cross_encoder_category", "cap_cross_encoder_desc", "status_experimental",
         "capability_cta_explore"),
        ("nav_runtime_diagnostics", "section_search", "cap_runtime_name",
         "cap_runtime_category", "cap_runtime_desc", "status_available",
         "capability_cta_view"),
        ("nav_data_workspace", "section_data_science", "cap_data_name",
         "cap_data_category", "cap_data_desc", "status_available",
         "capability_cta_inspect"),
    ]
    for i, (page_key, section, name_key, cat_key, desc_key, badge_key, cta_key) in enumerate(capabilities):
        with cap_cols[i % 3]:
            capability_card(
                name=t(name_key),
                category=t(cat_key),
                status_badge_html=status_badge(t(badge_key)),
                description=t(desc_key),
                cta_text=t(cta_key),
                cta_section=section,
                cta_key=page_key,
            )

    # ── Section 5: Latest Activity ──
    section_heading(t("activity_title"))
    entries = _activity_entries()
    if entries:
        from datetime import datetime as _dt
        html = '<div class="activity-feed">'
        for entry in reversed(entries[-10:]):
            cap = escape(entry.get("capability", ""))
            summary = escape(entry.get("summary", ""))
            ts = entry.get("timestamp")
            if ts:
                secs = int((_dt.now() - ts).total_seconds())
                ago = t("activity_seconds_ago", s=max(secs, 0))
            else:
                ago = ""
            html += (
                f'<div class="activity-entry">'
                f'<span class="activity-cap">{cap}</span>'
                f'<span class="activity-summary">{summary}</span>'
                f'<span class="activity-ago">{ago}</span>'
                f"</div>"
            )
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="empty-state"><strong>{t("activity_empty_title")}</strong>'
            f"<p>{t('activity_empty_cta')}</p></div>",
            unsafe_allow_html=True,
        )
        st.button(t("activity_empty_cta"), type="secondary", key="cc_activity_cta",
                  on_click=navigate_to, args=("section_search", "nav_search_intelligence"))

    # ── Section 6: Pipeline ──
    section_heading(t("pipeline_title"))
    pipeline_flow([
        (t("pipeline_data_sources"), t("pipeline_data_sources_detail")),
        (t("pipeline_validation"), t("pipeline_validation_detail")),
        (t("pipeline_features"), t("pipeline_features_detail")),
        (t("pipeline_training"), t("pipeline_training_detail")),
        (t("pipeline_registry"), t("pipeline_registry_detail")),
        (t("pipeline_inference"), t("pipeline_inference_detail")),
        (t("pipeline_monitoring"), t("pipeline_monitoring_detail")),
    ])

    # ── Section 7: Search Snapshot ──
    section_heading(t("search_snapshot_title"), t("search_snapshot_desc"))
    st.markdown(
        f'<div class="search-snapshot">'
        f'<div class="search-snapshot-vis">'
        f'<div class="search-snapshot-step"><span class="search-snapshot-step-label">{t("ss_step_query")}</span></div>'
        f'<span class="pipeline-arrow">→</span>'
        f'<div class="search-snapshot-step"><span class="search-snapshot-step-label">{t("ss_step_retrieval")}</span><span class="search-snapshot-step-value">{t("ss_value_candidates")}</span></div>'
        f'<span class="pipeline-arrow">→</span>'
        f'<div class="search-snapshot-step"><span class="search-snapshot-step-label">{t("ss_step_fusion")}</span><span class="search-snapshot-step-value">RRF</span></div>'
        f'<span class="pipeline-arrow">→</span>'
        f'<div class="search-snapshot-step"><span class="search-snapshot-step-label">{t("ss_step_rerank")}</span><span class="search-snapshot-step-value">Cross-Encoder</span></div>'
        f'<span class="pipeline-arrow">→</span>'
        f'<div class="search-snapshot-step"><span class="search-snapshot-step-label">{t("ss_step_results")}</span><span class="search-snapshot-step-value">{t("ss_value_displayed")}</span></div>'
        f"</div>"
        f'<div class="search-snapshot-info">'
        f'<span class="search-snapshot-stat"><strong>20</strong> {t("ss_stat_pool")}</span>'
        f'<span class="search-snapshot-stat"><strong>10</strong> {t("ss_stat_results_shown")}</span>'
        f'<span class="search-snapshot-stat">{status_badge("available")} {t("ss_stat_hybrid_ce")}</span>'
        f'<span class="search-snapshot-stat">{t("ss_stat_runtime")}</span>'
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.button(t("search_snapshot_cta"), type="secondary", key="cc_search_snapshot",
              on_click=navigate_to, args=("section_search", "nav_search_intelligence"))

    # ── Section 8: Data & Artifact Readiness ──
    st.markdown(
        f'<div class="data-artifact-panels">'
        f'<div class="data-panel">'
        f"<h3>{t('data_readiness_title')}</h3>"
        f'<ul class="data-panel-list">'
        f"<li>{t('dr_source_files')}<strong>7</strong></li>"
        f"<li>{t('dr_total_size')}<strong>0.91 GiB</strong></li>"
        f"<li>{t('dr_total_products')}<strong>962,873</strong></li>"
        f"<li>{t('dr_profile_outputs')}<strong>12/12</strong></li>"
        f"<li>{t('dr_schema_fields')}<strong>10</strong></li>"
        f"</ul>"
        f'<div class="data-panel-cta">',
        unsafe_allow_html=True,
    )
    st.button(t("data_cta_intel"), key="cc_data_intel", use_container_width=True,
              on_click=navigate_to, args=("section_data_science", "nav_data_workspace"))
    st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="data-panel">'
        f"<h3>{t('artifacts_title')}</h3>"
        f'<ul class="data-panel-list">'
        f"<li>{t('art_models')}<strong>{model_artifacts}</strong></li>"
        f"<li>{t('art_tokenizer')}<strong>1</strong></li>"
        f"<li>{t('art_candidate_index')}<strong>1</strong></li>"
        f"<li>{t('art_notebooks')}<strong>1</strong></li>"
        f"<li>{t('art_test_suite')}<strong>{TEST_COUNT}</strong></li>"
        f"</ul>"
        f'<div class="data-panel-cta">',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        st.button(t("data_cta_notebook"), key="cc_notebook", use_container_width=True,
                  on_click=navigate_to, args=("section_portfolio", "nav_notebook_status"))
    with c2:
        st.button(t("data_cta_docs"), key="cc_docs", use_container_width=True,
                  on_click=navigate_to, args=("section_portfolio", "nav_docs"))
    st.markdown("</div></div></div>", unsafe_allow_html=True)

    # ── Section 9: Quick Actions ──
    section_heading(t("quick_actions_title"))
    st.markdown('<div class="quick-action-grid">', unsafe_allow_html=True)
    quick_action_grid([
        (t("qa_sentiment"), "secondary", ("section_ml", "nav_sentiment")),
        (t("qa_housing"), "secondary", ("section_ml", "nav_housing")),
        (t("qa_hybrid"), "secondary", ("section_search", "nav_hybrid_retrieval")),
        (t("qa_cross_encoder"), "secondary", ("section_search", "nav_cross_encoder")),
        (t("qa_runtime"), "secondary", ("section_search", "nav_runtime_diagnostics")),
        (t("qa_data"), "secondary", ("section_data_science", "nav_data_workspace")),
    ])
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Section 10: Technical Transparency ──
    transparency_panel([
        ("Runtime", t("transparency_runtime")),
        ("Validation", t("transparency_validation")),
        ("Models", t("transparency_models")),
        ("Deployment", t("transparency_deployment")),
        ("Data", t("transparency_data")),
    ])

    st.caption(f"Platform v{PORTFOLIO_VERSION}")
