"""Runtime-backed registry for trained model artifacts."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from portfolio.loaders import load_model_safe
from portfolio.project_registry import get_project_registry, portfolio_counts
from portfolio.ui_components import hero_panel, information_panel, metric_table


def render() -> None:
    hero_panel("Model Registry", "Yerel model artifact'larının doğrulanmış yetenekleri, metrikleri ve çalışma zamanı durumu.", "MODEL OPERATIONS")
    rows = []
    technical = []
    for project in get_project_registry():
        path = project.get("model_path")
        if path is None:
            continue
        result = load_model_safe(path) if path.is_file() else None
        rows.append({
            "Project": project["name"], "Task": project["category"],
            "Final estimator": project["final_model"], "Pipeline type": type(result.model).__name__ if result and result.ok else "—", "Artifact": path.name,
            "Relative path": f"01-machine-learning/{path.parent.parent.name}/models/{path.name}",
            "Path status": "Present" if path.is_file() else "Missing",
            "Size (MB)": round(path.stat().st_size / 1024**2, 2) if path.is_file() else None,
            "predict": bool(result and result.supports_predict),
            "predict_proba": bool(result and result.supports_predict_proba),
            "decision_function": bool(result and result.ok and hasattr(result.model, "decision_function")),
            "Final metric": project["primary_metric_name"],
            "Value": project["primary_metric_value"],
            "Validation method": project.get("validation_strategy", "5-fold CV + tuning") if project["validation_available"] else "Eksik",
            "Modified": project["last_verified"] or "—",
            "Runtime": "Compatible" if result and result.ok else "Unavailable",
            "Live module": "Ready" if project["app_available"] and result and result.ok else "Unavailable",
            "Data mode": project.get("data_mode", "full/local"),
        })
        technical.append({"Project": project["name"], "Relative path": f"{path.parent.parent.name}/models/{path.name}"})
    live = sum(row["Runtime"] == "Compatible" for row in rows)
    counts = portfolio_counts()
    cols = st.columns(3)
    cols[0].metric("Persist edilmiş artifact", len(rows))
    cols[1].metric("Runtime hazır", live)
    cols[2].metric("Değerlendirilen aday", counts["models_compared"])
    information_panel("Registry ayrımı", f"Persist edilmiş doğrulanmış artifact sayısı {live}; {counts['models_compared']} değeri kayıtlı değerlendirme deneylerini ifade eder. Modeller yalnızca Registry veya tahmin sayfası açıldığında yüklenir.")
    metric_table(pd.DataFrame(rows))
    with st.expander("Technical artifact locations", expanded=False):
        metric_table(pd.DataFrame(technical))
