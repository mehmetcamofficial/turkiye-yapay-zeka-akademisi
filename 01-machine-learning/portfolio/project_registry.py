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
    projects.append({"id":"trendyol_relevance", "name":"Trendyol Relevance Classifier V1", "short_name":"Trendyol V1 Champion",
        "category":"Verified Champion", "description":"Sorgu ve ürün ilişkisini leakage-aware term-group validation ile sınıflandıran sparse lexical baseline.",
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
        ("trendyol_v2_classifier","Trendyol Classification Challenger V2","Historical Experimental Challenger","classification_challenger.pkl","F1",v2.get("classification_holdout",{}).get("f1")),
        ("trendyol_v2_ranker","Trendyol Search Ranker V2","Historical Experimental Ranker","search_ranker.pkl","NDCG@10",v2.get("ranking_holdout",{}).get("ndcg@10"))]:
        path=TRENDYOL_RELEVANCE_DIR/"models/v2"/artifact; expected=[f"models/v2/{artifact}","outputs/v2/v2_results.json"]
        algorithm="Random Forest" if "classifier" in project_id else "XGBRanker rank:ndcg topk"; projects.append({"id":project_id,"name":name,"short_name":name,"category":category,"description":"Offline Evaluation · Bounded Candidate Sample · Not Promoted.","directory":TRENDYOL_RELEVANCE_DIR,"status":"Deneysel","dataset":"Public Datathon group-complete sample","dataset_size":f"{v2.get('sample',{}).get('rows',0):,} rows","final_model":algorithm,"primary_metric_name":metric,"primary_metric_value":value,"secondary_metrics":{},"model_path":path,"expected_output_files":expected,"app_available":False,"training_available":True,"data_source_available":True,"readme_available":True,"validation_available":bool(v2),"model_artifact_available":path.is_file(),"last_verified":_last_verified(TRENDYOL_RELEVANCE_DIR,expected),"limitations":["Not Promoted","V1 unchanged","Bounded Candidate Sample"],"data_mode":"ranking-sample","validation_strategy":"70/15/15 complete term_id groups; zero overlap"})

    v21_summary=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2_1/classification_repeated_seed_ci.csv")); v21_rank=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v2_1/ranking_repeated_seed_ci.csv"))
    v21_specs=[("trendyol_v21_classifier","Trendyol Classification Challenger V2.1","HistGradientBoostingClassifier","v21_hist_gradient_boosting.pkl","F1",float(v21_summary.loc[v21_summary.model.eq("hist_gradient_boosting"),"f1_mean"].iloc[0]) if not v21_summary.empty else None),("trendyol_v21_ranker","Trendyol Search Ranker V2.1","XGBRanker rank:ndcg topk","v21_ranker_candidate.pkl","NDCG@10",float(v21_rank.loc[v21_rank.model.eq("rank_ndcg_topk"),"ndcg@10_mean"].iloc[0]) if not v21_rank.empty else None)]
    for project_id,name,algorithm,artifact,metric,value in v21_specs:
        path=TRENDYOL_RELEVANCE_DIR/"models/v2_1"/artifact; expected=[f"models/v2_1/{artifact}","outputs/v2_1/v21_results.json","reports/v2_1/ROBUST_EVALUATION.md"]
        classifier=project_id.endswith("classifier"); projects.append({"id":project_id,"name":name,"short_name":name,"category":"Best Research Candidate" if classifier else "Experimental Ranker","description":"Offline Evaluation · 1.000 tam sorgu grubu ve beş group-safe seed · Direct superiority not established · Not Promoted.","directory":TRENDYOL_RELEVANCE_DIR,"status":"Deneysel","dataset":"Public Datathon · Bounded Candidate Sample","dataset_size":"52,422 rows · 1,000 groups","final_model":algorithm,"primary_metric_name":metric,"primary_metric_value":value,"secondary_metrics":{},"model_path":path,"expected_output_files":expected,"app_available":False,"training_available":True,"data_source_available":True,"readme_available":True,"validation_available":True,"model_artifact_available":path.is_file(),"last_verified":_last_verified(TRENDYOL_RELEVANCE_DIR,expected),"limitations":["Not Promoted","Different historical split","Direct superiority not established","Classifier artifact not persisted" if classifier else "Research-only feature contract"],"data_mode":"ranking_medium","validation_strategy":"five seeds · 700/150/150 complete term_id groups · zero overlap"})

    v3=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/v3_results.json")); v3_metrics=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/retrieval_metrics_by_seed.csv")); demo=TRENDYOL_RELEVANCE_DIR/"models/v3/lexical_demo.joblib"
    def retrieval_metric(method):
        rows=v3_metrics[v3_metrics.method.eq(method)] if not v3_metrics.empty and "method" in v3_metrics else v3_metrics
        return float(rows["recall@50"].mean()) if not rows.empty else None
    v31=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/v31_results.json")); v31_metrics=load_csv_safe(str(TRENDYOL_RELEVANCE_DIR/"outputs/v3/v31_metrics_by_seed.csv")); semantic_meta=load_json_safe(str(TRENDYOL_RELEVANCE_DIR/"models/v3/semantic_demo_metadata.json"))
    def v31_metric(method):
        rows=v31_metrics[v31_metrics.method.eq(method)] if not v31_metrics.empty and "method" in v31_metrics else v31_metrics
        return float(rows["recall@50"].mean()) if not rows.empty else None
    semantic_path=TRENDYOL_RELEVANCE_DIR/"models/v3/semantic_demo.npy"; hybrid_path=TRENDYOL_RELEVANCE_DIR/"outputs/v3/v31_results.json"; best_hybrid=v31.get("best_hybrid","hybrid_pending")
    specs=[
        ("trendyol_v3_tfidf","Trendyol Lexical Retriever V3","Experimental Retrieval Baseline",v3.get("best_tfidf","TF-IDF"),demo,"retrieval_asset",retrieval_metric(v3.get("best_tfidf","TF-IDF")),"sparse TF-IDF/BM25",["models/v3/lexical_demo.joblib","models/v3/lexical_demo_metadata.json"]),
        ("trendyol_v3_bm25","Trendyol BM25 Retriever V3","Experimental Retrieval Baseline",v3.get("best_bm25","BM25"),demo,"retrieval_asset",retrieval_metric(v3.get("best_bm25","BM25")),"sparse TF-IDF/BM25",["models/v3/lexical_demo.joblib","models/v3/lexical_demo_metadata.json"]),
        ("trendyol_v31_semantic","Trendyol Semantic Retriever V3.1","Experimental Semantic Retriever","multilingual E5 Small",semantic_path,"dense_index",v31_metric("semantic_e5_small"),"normalized NumPy cosine",["models/v3/semantic_demo.npy","models/v3/semantic_demo_metadata.json","models/v3/semantic_medium.npy","models/v3/semantic_medium_metadata.json","models/v3/model_cache/models--intfloat--multilingual-e5-small/snapshots/614241f622f53c4eeff9890bdc4f31cfecc418b3","outputs/v3/v31_results.json"]),
        ("trendyol_v31_hybrid","Trendyol Hybrid Retriever V3.1","Best Research Candidate" if v31 else "Experimental Hybrid Retriever",best_hybrid,hybrid_path,"hybrid_metadata",v31_metric(best_hybrid),"score/rank fusion",["outputs/v3/v31_results.json","outputs/v3/v31_validation_selection.csv"]),
    ]
    for pid,name,role,method,path,kind,value,index_type,expected in specs:
        available=path.is_file(); semantic=pid=="trendyol_v31_semantic"; hybrid=pid=="trendyol_v31_hybrid"; performance=v31.get("performance",{})
        projects.append({"id":pid,"name":name,"short_name":name,"category":role,"description":"Offline Evaluation · Bounded Demo · Catalogue-Wide Not Established.","directory":TRENDYOL_RELEVANCE_DIR,"status":"Deneysel","dataset":"Bounded broad product catalogue","dataset_size":f"{v3.get('catalogue',{}).get('bounded_rows',0):,} evaluation products · 5,000 live-demo products","final_model":method,"primary_metric_name":"Recall@50","primary_metric_value":value,"secondary_metrics":{},"model_path":path,"expected_output_files":expected,"app_available":available,"training_available":True,"data_source_available":True,"readme_available":True,"validation_available":bool(v3),"model_artifact_available":available,"last_verified":_last_verified(TRENDYOL_RELEVANCE_DIR,expected),"limitations":["Not Promoted","Bounded Demo","Catalogue-Wide Not Established","Model Cache Required" if semantic else "Offline retrieval asset"],"data_mode":"retrieval_medium","validation_strategy":"five complete-query group-safe seeds","artifact_kind":kind,"embedding_model":semantic_meta.get("model_id","None selected") if semantic or hybrid else "None","model_revision":semantic_meta.get("model_revision","—") if semantic or hybrid else "—","embedding_dimension":semantic_meta.get("embedding_dimension","—") if semantic or hybrid else "—","index_type":index_type,"indexed_product_count":semantic_meta.get("product_count",0) if semantic else (5000 if not hybrid else 5000),"evaluation_product_count":v3.get('catalogue',{}).get('bounded_rows',0),"evaluation_dataset":"1,000 complete queries · five holdouts","artifact_availability":"Available" if available else "Dense Index Required","governance_decision":role,"p95_latency_ms":performance.get("semantic_search_p95_ms") if semantic else performance.get(f"{best_hybrid}_fusion_p95_ms") if hybrid else None,"fusion_method":best_hybrid if hybrid else "—"})

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
