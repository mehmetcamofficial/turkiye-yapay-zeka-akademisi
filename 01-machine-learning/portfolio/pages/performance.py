"""Cross-project performance review without mixing incompatible metrics."""

import pandas as pd
import streamlit as st

from portfolio.loaders import load_csv_safe, load_json_safe
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import hero_panel, metric_table, section_heading


def _row(project, metric_names):
    metrics = load_csv_safe(str(project["directory"] / "outputs/test_metrics.csv"))
    row = {"Final model": project["final_model"], "Dataset": project["dataset"], "Boyut": project["dataset_size"]}
    for name in metric_names:
        row[name] = metrics.iloc[0][name] if not metrics.empty and name in metrics else None
    tuning = load_json_safe(str(project["directory"] / "outputs/best_hyperparameters.json"))
    row["CV"] = f"{tuning.get('cv_folds', 5)}-fold"
    row["Tuning"] = tuning.get("search_method", "GridSearchCV" if tuning else "—")
    return row


def render() -> None:
    hero_panel("Model Performansı", "Farklı problem tiplerinin metrikleri ayrı bağlamlarda, kaydedilmiş test artifact'larından gösterilir.", "CROSS-PROJECT REVIEW")
    projects = {project["id"]: project for project in get_project_registry()}
    section_heading("Customer Churn · Sınıflandırma", "ROC AUC, Accuracy, Recall ve F1 aynı ikili sınıflandırma bağlamındadır.")
    metric_table(pd.DataFrame([_row(projects["churn"], ["ROC AUC", "Accuracy", "Recall", "F1 Score"])]))
    st.caption("Sınırlamalar: " + "; ".join(projects["churn"]["limitations"]))
    section_heading("California Housing · Regresyon", "RMSE/MAE hata büyüklüğünü, R² açıklanan varyansı ifade eder.")
    metric_table(pd.DataFrame([_row(projects["regression"], ["RMSE", "MAE", "R2"])]))
    st.caption("Sınırlamalar: " + "; ".join(projects["regression"]["limitations"]))
    section_heading("UCI Sentiment · NLP Sınıflandırma", "Accuracy, Precision, Recall ve F1 metin sınıflandırma test setine aittir.")
    metric_table(pd.DataFrame([_row(projects["nlp"], ["Accuracy", "Precision", "Recall", "F1"])]))
    st.caption("Sınırlamalar: " + "; ".join(projects["nlp"]["limitations"]))
