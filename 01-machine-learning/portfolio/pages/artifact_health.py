from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from portfolio.config import (CHURN_DIR, CLUSTERING_DIR, DEPLOYMENT_DIR,
                              ML_ROOT, NLP_DIR, REGRESSION_DIR,
                              REPOSITORY_ROOT, TRENDYOL_RELEVANCE_DIR)
from portfolio.i18n import t
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import (hero_panel, kpi_grid, render_safe_table,
                                     section_heading)


def _is_cloud() -> bool:
    return os.environ.get("STREAMLIT_SHARING", "") == "true" or os.environ.get("STREAMLIT_RUNTIME_ENV", "") == "cloud"


def _classify(path: Path, project_id: str) -> str:
    rel = str(path.relative_to(ML_ROOT)) if ML_ROOT in path.parents else str(path)
    ignored_patterns = [
        "trendyol-search-relevance/models/v3/model_cache",
        "trendyol-search-relevance/models/v3/semantic_medium",
    ]
    if any(pattern in rel for pattern in ignored_patterns):
        return "cloud_excluded"
    if "model_cache" in rel or ".pytest_cache" in rel or ".venv" in rel:
        return "cloud_excluded"
    return "core"


def render() -> None:
    is_cloud = _is_cloud()
    hero_panel(
        title=t("nav_artifact_health"),
        subtitle=t("subtitle_artifact_health"),
        kicker=t("section_model_ops"),
    )

    if is_cloud:
        st.info(
            "Running on Streamlit Cloud. Local-only and cache artifacts are "
            "excluded from this health check."
        )

    projects = get_project_registry()
    core_healthy = 0
    core_required = 0
    optional_missing = 0
    cloud_excluded = 0
    historical = 0
    total_expected = 0

    for project in projects:
        if project["id"] in {"deployment", "clustering", "trendyol_v2_classifier",
                              "trendyol_v2_ranker", "trendyol_v21_classifier",
                              "trendyol_v21_ranker", "trendyol_v3_tfidf",
                              "trendyol_v3_bm25", "trendyol_v31_semantic"}:
            historical += 1
            continue
        core_required += 1
        if project.get("model_artifact_available") or project.get("app_available"):
            core_healthy += 1

    kpi_grid([
        ("Core Required", str(core_required), "Projects needed for portfolio"),
        ("Core Healthy", str(core_healthy), "Artifacts verified"),
        ("Optional Missing", str(optional_missing), "Historical/local artifacts"),
        ("Cloud Excluded", str(cloud_excluded), "Local-only/cache assets"),
        ("Historical", str(historical), "Past research candidates"),
    ])

    rows = []
    for project in projects:
        path = project.get("model_path")
        if path:
            classification = _classify(path, project["id"])
            exists = path.exists() if path else False
            if classification == "cloud_excluded":
                exists_str = "Excluded from cloud"
            elif exists:
                exists_str = "Available"
            else:
                exists_str = "Unavailable"
            rows.append({
                "Project": project.get("short_name", project.get("name", "—")),
                "Category": project.get("category", "—"),
                "Status": project.get("status", "experimental").title(),
                "Artifact": exists_str,
                "Type": classification,
            })

    if rows:
        render_safe_table(rows, download_name="artifact_health.csv")
