from __future__ import annotations

from pathlib import Path

import streamlit as st

from portfolio.config import ML_ROOT
from portfolio.i18n import t
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import (format_metric, hero_panel, kpi_grid,
                                     section_heading, status_badge)


def _rel_path(p: Path | None) -> str:
    if p is None:
        return "—"
    try:
        return str(p.relative_to(ML_ROOT))
    except ValueError:
        return p.name


def _evidence_status(project: dict) -> str:
    status = project.get("status", "experimental")
    governance = project.get("governance_decision", "")
    if governance:
        return governance
    labels = {
        "verified": t("verified_label"),
        "available": t("available_label"),
        "experimental": t("experimental_label"),
        "local_only": t("local_only_label"),
        "cloud_excluded": t("cloud_excluded_label"),
    }
    return labels.get(status, t("experimental_label"))


def render() -> None:
    hero_panel(
        title=t("nav_registry"),
        subtitle=t("subtitle_model_registry"),
        kicker=t("section_model_ops"),
    )

    projects = get_project_registry()
    verified = [p for p in projects if p.get("status") == "verified"]
    available = [p for p in projects if p.get("status") == "available"]
    experimental = [p for p in projects if p.get("status") == "experimental"]

    kpi_grid([
        (t("verified_label"), str(len(verified)), t("confirmed_champions")),
        (t("available_label"), str(len(available)), t("completed_pipelines")),
        (t("experimental_label"), str(len(experimental)), t("research_candidates")),
        (t("total"), str(len(projects)), t("all_registered")),
    ])

    catalog = {"verified": verified, "available": available, "experimental": experimental}
    filter_all_label = t("filter_all")
    category = st.selectbox(t("filter_status"), [filter_all_label] + list(catalog))
    filtered = projects if category == filter_all_label else catalog.get(category, [])

    for project in filtered:
        governance = _evidence_status(project)
        prim_val = project.get("primary_metric_value")
        prim_str = format_metric(prim_val) if prim_val is not None else "—"
        artifact_path = project.get("model_path")
        with st.expander(f"{project.get('name', '—')} \u2014 {governance}", expanded=False):
            st.markdown(f"**{t('id_label')}:** `{project.get('id', '—')}`")
            st.markdown(f"**{t('status_label')}:** `{project.get('status', '—')}`")
            st.markdown(f"**{t('decision_label')}:** {governance}")
            st.markdown(f"**{t('algorithm_label')}:** {project.get('final_model', '—')}")
            st.markdown(f"**{t('metric_label')}:** {project.get('primary_metric_name', '—')}: {prim_str}")
            limitations = project.get("limitations", [])
            if limitations:
                st.markdown(f"**{t('limitations_label')}:** " + "; ".join(limitations[:3]))
            if artifact_path:
                st.markdown(f"**{t('artifact_label')}:** `{_rel_path(artifact_path)}`")
