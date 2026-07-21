"""Runtime-backed registry for trained model artifacts."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from portfolio.loaders import load_model_safe
from portfolio.project_registry import get_project_registry, portfolio_counts
from portfolio.ui_components import decision_banner,evidence_strip,page_header,information_panel,metric_table,section_heading,status_badge


def render() -> None:
    page_header("Model Registry", "Hangi modelin canlı, hangisinin deneysel ve neden terfi edilmediğini artifact düzeyinde gösteren yönetişim kaydı.", "MODEL GOVERNANCE")
    rows = []
    technical = []
    for project in get_project_registry():
        path = project.get("model_path")
        if path is None:
            continue
        result = load_model_safe(path) if path.is_file() else None
        experimental=project["status"]=="Deneysel"; decision="Terfi edilmedi" if experimental else ("Doğrulandı" if result and result.ok else "İnceleme gerekli")
        rows.append({
            "Project": project["name"], "Role": "Challenger" if experimental else "Champion / project model", "Task": project["category"],
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
            "Governance decision":decision,
        })
        technical.append({"Project": project["name"], "Relative path": f"{path.parent.parent.name}/models/{path.name}"})
    live = sum(row["Runtime"] == "Compatible" for row in rows)
    counts = portfolio_counts()
    experimental=sum(row["Role"]=="Challenger" for row in rows); production=len(rows)-experimental
    evidence_strip([("Production-style",str(production),"Champion/project artifact"),("Experimental",str(experimental),"Challenger artifact"),("Healthy reload",str(live),"Fresh runtime compatible"),("Live inference",str(sum(row["Live module"]=="Ready" for row in rows)),"UI contract"),("Evaluated candidates",str(counts["models_compared"]),"Saved experiment rows")])
    information_panel("Registry ayrımı", f"Persist edilmiş doğrulanmış artifact sayısı {live}; {counts['models_compared']} değeri kayıtlı değerlendirme deneylerini ifade eder. Modeller yalnızca Registry veya tahmin sayfası açıldığında yüklenir.")
    decision_banner("Challengers neden terfi edilmedi?","V2 Random Forest historical experimental challenger’dır. V2.1 HistGradientBoosting Best Research Candidate olsa da Different historical split nedeniyle direct superiority established değildir ve seçilmiş nesnesi retraining olmadan persist edilememiştir. XGBoost ranker ortak holdout baseline’ını tekrarlanabilir biçimde geçmedi. Live path Verified Champion V1’de kaldı.")
    section_heading("Model governance inventory","Validation, runtime ve karar aynı görünümde.")
    metric_table(pd.DataFrame(rows))
    with st.expander("Technical artifact locations", expanded=False):
        metric_table(pd.DataFrame(technical))
