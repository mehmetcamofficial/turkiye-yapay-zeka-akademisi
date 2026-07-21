"""Data-driven project registry built exclusively from real artifacts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from portfolio.config import (CHURN_DIR, CHURN_MODEL_PATH, CLUSTERING_DIR,
                              DEPLOYMENT_DIR, NLP_DIR, NLP_MODEL_PATH,
                              REGRESSION_DIR, REGRESSION_MODEL_PATH,
                              TRENDYOL_RELEVANCE_DIR, TRENDYOL_RELEVANCE_MODEL_PATH)
from portfolio.loaders import load_csv_safe, load_json_safe


def _exists_all(directory: Path, relative_paths: list[str]) -> bool:
    return all((directory / relative).is_file() for relative in relative_paths)


def _metric(frame, name: str) -> float | None:
    if not frame.empty and name in frame.columns:
        try:
            return float(frame.iloc[0][name])
        except (TypeError, ValueError):
            return None
    return None


def _last_verified(directory: Path, relative_paths: list[str]) -> str | None:
    timestamps = [(directory / item).stat().st_mtime for item in relative_paths if (directory / item).is_file()]
    return datetime.fromtimestamp(max(timestamps)).astimezone().isoformat(timespec="minutes") if timestamps else None


def _supervised_project(*, project_id: str, name: str, short_name: str,
                        category: str, description: str, directory: Path,
                        dataset: str, dataset_size: str, model_path: Path,
                        expected: list[str], primary_name: str,
                        secondary_names: list[str], limitations: list[str]) -> dict[str, Any]:
    metrics = load_csv_safe(str(directory / "outputs" / "test_metrics.csv"))
    validation = load_csv_safe(str(directory / "outputs" / "validation_results.csv"))
    completed = directory.is_dir() and _exists_all(directory, expected)
    status = "Tamamlandı" if completed else ("Geliştiriliyor" if directory.is_dir() else "Henüz Başlanmadı")
    final_model = str(metrics.iloc[0]["Model"]) if not metrics.empty and "Model" in metrics else "Doğrulanmadı"
    secondary = {metric: _metric(metrics, metric) for metric in secondary_names}
    return {
        "id": project_id, "name": name, "short_name": short_name,
        "category": category, "description": description, "directory": directory,
        "status": status, "dataset": dataset, "dataset_size": dataset_size,
        "final_model": final_model, "primary_metric_name": primary_name,
        "primary_metric_value": _metric(metrics, primary_name),
        "secondary_metrics": secondary, "model_path": model_path,
        "expected_output_files": expected, "app_available": (directory / "app.py").is_file(),
        "training_available": (directory / "train_model.py").is_file(),
        "data_source_available": (directory / "DATA_SOURCE.md").is_file(),
        "readme_available": (directory / "README.md").is_file(),
        "validation_available": not validation.empty,
        "model_artifact_available": model_path.is_file(),
        "last_verified": _last_verified(directory, expected), "limitations": limitations,
    }


def get_project_registry() -> list[dict[str, Any]]:
    """Return current statuses and metrics; no completion value is hard-coded."""
    churn_expected = ["models/churn_model.pkl", "outputs/test_metrics.csv", "outputs/final_summary.txt"]
    regression_expected = ["models/regression_model.pkl", "outputs/test_metrics.csv", "outputs/final_summary.txt",
                           "outputs/residual_plot.png", "outputs/prediction_vs_actual.png"]
    nlp_expected = ["models/nlp_pipeline.pkl", "outputs/test_metrics.csv", "outputs/final_summary.txt",
                    "outputs/confusion_matrix.png", "outputs/top_terms.csv"]
    projects = [
        _supervised_project(project_id="churn", name="Customer Churn Prediction", short_name="Customer Churn",
            category="Sınıflandırma", description="Telekom müşterilerinin ayrılma riskini tahmin eden uçtan uca pipeline.",
            directory=CHURN_DIR, dataset="Telco Customer Churn", dataset_size="7.043 × 33",
            model_path=CHURN_MODEL_PATH, expected=churn_expected, primary_name="ROC AUC",
            secondary_names=["Accuracy", "Recall", "F1 Score"],
            limitations=["Tek telekom bağlamı", "Sınıf dengesizliği", "Concept drift"]),
        _supervised_project(project_id="regression", name="California Housing Regression", short_name="Regresyon",
            category="Regresyon", description="Bölgesel medyan ev değerini tahmin eden offline-first regresyon çalışması.",
            directory=REGRESSION_DIR, dataset="California Housing", dataset_size="20.640 × 9",
            model_path=REGRESSION_MODEL_PATH, expected=regression_expected, primary_name="RMSE",
            secondary_names=["MAE", "MSE", "R2"],
            limitations=["1990 California bağlamı", "Mekânsal bağımlılık", "Hedef tavanı"]),
        _supervised_project(project_id="nlp", name="UCI Sentiment Analysis", short_name="NLP Analizi",
            category="Doğal Dil İşleme", description="Amazon, IMDb ve Yelp cümlelerinde İngilizce ikili duygu analizi.",
            directory=NLP_DIR, dataset="UCI Sentiment Labelled Sentences", dataset_size="3.000 × 3",
            model_path=NLP_MODEL_PATH, expected=nlp_expected, primary_name="F1",
            secondary_names=["Accuracy", "Precision", "Recall"],
            limitations=["Nötr sınıf yok", "Kısa İngilizce cümleler", "Domain yanlılığı"]),
    ]

    trendyol_metrics = load_json_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "metrics.json"))
    trendyol_metadata = load_json_safe(str(TRENDYOL_RELEVANCE_DIR / "models" / "model_metadata.json"))
    trendyol_expected = ["models/trendyol_relevance_pipeline.pkl", "models/model_metadata.json",
                         "outputs/metrics.json", "outputs/model_comparison.csv", "reports/split_report.json",
                         "reports/error_analysis.md", "reports/model_selection.md"]
    trendyol_ready = _exists_all(TRENDYOL_RELEVANCE_DIR, trendyol_expected)
    projects.append({"id":"trendyol_relevance", "name":"Trendyol Search Relevance Intelligence", "short_name":"Trendyol Relevance",
        "category":"Query-Product Relevance Classification", "description":"Sorgu ve ürün ilişkisini leakage-aware term-group validation ile sınıflandıran sparse lexical baseline.",
        "directory":TRENDYOL_RELEVANCE_DIR, "status":"Doğrulandı" if trendyol_ready else "Geliştiriliyor",
        "dataset":"Public Datathon train_with_negatives", "dataset_size":f"{trendyol_metadata.get('training_rows', 0) + trendyol_metadata.get('validation_rows', 0):,} sample rows",
        "final_model":trendyol_metadata.get("model_type", "Üretilmedi"), "primary_metric_name":"F1",
        "primary_metric_value":trendyol_metrics.get("f1"), "secondary_metrics":{name:trendyol_metrics.get(name) for name in ["precision","recall","pr_auc","roc_auc"]},
        "model_path":TRENDYOL_RELEVANCE_MODEL_PATH, "expected_output_files":trendyol_expected,
        "app_available":trendyol_ready, "training_available":(TRENDYOL_RELEVANCE_DIR/"train.py").is_file(),
        "data_source_available":True, "readme_available":(TRENDYOL_RELEVANCE_DIR/"README.md").is_file(),
        "validation_available":(TRENDYOL_RELEVANCE_DIR/"reports/split_report.json").is_file(),
        "model_artifact_available":TRENDYOL_RELEVANCE_MODEL_PATH.is_file(), "last_verified":_last_verified(TRENDYOL_RELEVANCE_DIR,trendyol_expected),
        "limitations":trendyol_metadata.get("known_limitations",["Bounded lexical baseline"]),
        "data_mode":trendyol_metadata.get("data_mode","—"), "validation_strategy":trendyol_metadata.get("validation_strategy","—")})

    v2=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2/v2_results.json"))
    for project_id,name,category,artifact,metric,value in [
        ("trendyol_v2_classifier","Trendyol V2 Classification Challenger","Classification challenger","classification_challenger.pkl","F1",v2.get("classification_holdout",{}).get("f1")),
        ("trendyol_v2_ranker","Trendyol V2 Search Ranker","Learning to rank challenger","search_ranker.pkl","NDCG@10",v2.get("ranking_holdout",{}).get("ndcg@10"))]:
        path=TRENDYOL_RELEVANCE_DIR/"models/v2"/artifact; expected=[f"models/v2/{artifact}","outputs/v2/v2_results.json"]
        projects.append({"id":project_id,"name":name,"short_name":name,"category":category,"description":"Grup-güvenli V2 deneysel challenger; üretim şampiyonu değildir.","directory":TRENDYOL_RELEVANCE_DIR,"status":"Deneysel","dataset":"Public Datathon group-complete sample","dataset_size":f"{v2.get('sample',{}).get('rows',0):,} rows","final_model":v2.get("classification_validation_champion" if "classifier" in project_id else "ranking_champion","—"),"primary_metric_name":metric,"primary_metric_value":value,"secondary_metrics":{},"model_path":path,"expected_output_files":expected,"app_available":False,"training_available":True,"data_source_available":True,"readme_available":True,"validation_available":bool(v2),"model_artifact_available":path.is_file(),"last_verified":_last_verified(TRENDYOL_RELEVANCE_DIR,expected),"limitations":["Deneysel challenger","V1 değiştirilmedi","Bounded group-complete sample"],"data_mode":"ranking-sample","validation_strategy":"70/15/15 complete term_id groups; zero overlap"})

    cluster_expected = ["models/clustering_pipeline.pkl", "outputs/model_comparison.csv", "outputs/pca_clusters.png"]
    cluster_status = "Henüz Başlanmadı" if not CLUSTERING_DIR.is_dir() else ("Tamamlandı" if _exists_all(CLUSTERING_DIR, cluster_expected) else "Geliştiriliyor")
    projects.append({"id":"clustering", "name":"Customer Segmentation", "short_name":"Kümeleme", "category":"Denetimsiz Öğrenme",
        "description":"Müşteri segmentasyonu için planlanan kümeleme çalışması.", "directory":CLUSTERING_DIR,
        "status":cluster_status, "dataset":"Henüz seçilmedi", "dataset_size":"—", "final_model":"—",
        "primary_metric_name":"Silhouette", "primary_metric_value":None, "secondary_metrics":{},
        "model_path":CLUSTERING_DIR/"models/clustering_pipeline.pkl", "expected_output_files":cluster_expected,
        "app_available":False, "training_available":(CLUSTERING_DIR/"train_model.py").is_file(),
        "data_source_available":(CLUSTERING_DIR/"DATA_SOURCE.md").is_file(), "readme_available":(CLUSTERING_DIR/"README.md").is_file(),
        "validation_available":False, "model_artifact_available":False, "last_verified":_last_verified(CLUSTERING_DIR, cluster_expected),
        "limitations":["Henüz uygulanmadı"]})

    deployment_ready = DEPLOYMENT_DIR.is_dir() and (DEPLOYMENT_DIR/"api.py").is_file() and (DEPLOYMENT_DIR/"tests").is_dir() and (DEPLOYMENT_DIR/"outputs/test_metadata.json").is_file()
    projects.append({"id":"deployment", "name":"Model Deployment", "short_name":"Deployment", "category":"MLOps",
        "description":"Model servisleme, sağlık kontrolleri ve API testleri için planlanan katman.", "directory":DEPLOYMENT_DIR,
        "status":"Hazır" if deployment_ready else "Planlandı", "dataset":"Uygulanamaz", "dataset_size":"—", "final_model":"—",
        "primary_metric_name":"Test durumu", "primary_metric_value":None, "secondary_metrics":{}, "model_path":None,
        "expected_output_files":["api.py", "tests/", "outputs/test_metadata.json"], "app_available":False,
        "training_available":False, "data_source_available":False, "readme_available":(DEPLOYMENT_DIR/"README.md").is_file(),
        "validation_available":deployment_ready, "model_artifact_available":False, "last_verified":None,
        "limitations":["Henüz harici servise alınmadı"]})
    return projects


def project_by_id(project_id: str) -> dict[str, Any]:
    return next(project for project in get_project_registry() if project["id"] == project_id)


def portfolio_counts() -> dict[str, int]:
    projects = get_project_registry()
    completed = [p for p in projects if p["status"] in {"Tamamlandı", "Hazır", "Doğrulandı"}]
    model_counts = 0
    for project in projects[:3]:
        comparison = load_csv_safe(str(project["directory"] / "outputs" / "validation_results.csv"))
        model_counts += int(comparison["Model"].nunique()) if not comparison.empty and "Model" in comparison else 0
    trendyol_experiments = load_csv_safe(str(TRENDYOL_RELEVANCE_DIR / "outputs" / "experiments.csv"))
    if not trendyol_experiments.empty:
        model_counts += int((trendyol_experiments.get("status") == "evaluated").sum())
    return {"completed_projects": len(completed), "models_compared": model_counts,
            "completed_pipelines": sum(bool(p["model_artifact_available"]) for p in projects),
            "live_prediction_modules": sum(bool(p["app_available"] and p["model_artifact_available"]) for p in projects)}
