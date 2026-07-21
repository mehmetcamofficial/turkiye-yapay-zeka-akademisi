"""Runtime-backed registry for trained model artifacts."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st
import json
import numpy as np

from portfolio.project_registry import get_project_registry, portfolio_counts
from portfolio.ui_components import decision_banner,evidence_strip,page_header,information_panel,metric_table,section_heading,status_badge

def _metadata_asset_ok(path:Path,kind:str|None)->bool:
    """Registry display must not import native model runtimes."""
    if not path.is_file():return False
    if kind=="retrieval_asset":
        metadata=path.with_name(path.stem+"_metadata.json")
        try:return bool(json.loads(metadata.read_text(encoding="utf-8")).get("fingerprint"))
        except (OSError,json.JSONDecodeError):return False
    return path.stat().st_size>0

@st.cache_resource(show_spinner=False)
def _special_asset_ok(path_text:str,modified:float,size:int,kind:str)->bool:
    try:
        if kind=="dense_index":
            path=Path(path_text); metadata=json.loads(path.with_name(path.stem+"_metadata.json").read_text(encoding="utf-8")); matrix=np.load(path,mmap_mode="r")
            return matrix.shape==(metadata["product_count"],metadata["embedding_dimension"]) and str(matrix.dtype)==metadata["dtype"] and bool(metadata["finite_values"])
        if kind=="hybrid_metadata":return bool(json.loads(Path(path_text).read_text(encoding="utf-8")).get("best_hybrid"))
        return False
    except Exception:return False


def render() -> None:
    page_header("Model Registry", "Hangi modelin canlı, hangisinin deneysel ve neden terfi edilmediğini artifact düzeyinde gösteren yönetişim kaydı.", "MODEL GOVERNANCE")
    rows = []
    technical = []
    for project in get_project_registry():
        path = project.get("model_path")
        if path is None:
            continue
        try:relative_artifact=path.relative_to(project["directory"])
        except ValueError:relative_artifact=Path("models")/path.name
        kind=project.get("artifact_kind"); retrieval=kind in {"retrieval_asset","dense_index","hybrid_metadata"}; retrieval_ok=False
        if kind=="retrieval_asset" and path.is_file():
            retrieval_ok=_metadata_asset_ok(path,kind)
        elif retrieval and path.is_file():retrieval_ok=_special_asset_ok(str(path),path.stat().st_mtime,path.stat().st_size,kind)
        metadata_ok=_metadata_asset_ok(path,kind) if not retrieval else retrieval_ok
        experimental=project["status"]=="Deneysel"; decision="Terfi edilmedi" if experimental else ("Doğrulandı" if metadata_ok else "İnceleme gerekli")
        rows.append({
            "Project": project["name"], "Role": project["category"] if retrieval else ("Challenger" if experimental else "Champion / project model"), "Task": project["category"],
            "Final estimator": project["final_model"], "Pipeline type": kind or project["final_model"], "Artifact": path.name,
            "Relative path": f"01-machine-learning/{project['directory'].name}/{relative_artifact}",
            "Path status": "Present" if path.is_file() else "Missing",
            "Size (MB)": round(path.stat().st_size / 1024**2, 2) if path.is_file() else None,
            "predict": bool(metadata_ok),
            "predict_proba": bool(metadata_ok and "ranker" not in project["final_model"].lower()),
            "decision_function": False,
            "Final metric": project["primary_metric_name"],
            "Value": project["primary_metric_value"],
            "Validation method": project.get("validation_strategy", "5-fold CV + tuning") if project["validation_available"] else "Eksik",
            "Modified": project["last_verified"] or "—",
            "Runtime": "Metadata verified" if metadata_ok else "Unavailable",
            "Live module": "Ready" if project["app_available"] and metadata_ok else "Unavailable",
            "Data mode": project.get("data_mode", "full/local"),
            "Governance decision":decision,
            "Embedding model":project.get("embedding_model","—"),"Index type":project.get("index_type","—"),
            "Indexed products":project.get("indexed_product_count","—"),"Evaluation products":project.get("evaluation_product_count","—"),
            "Evaluation dataset":project.get("evaluation_dataset",project.get("dataset","—")),"Asset availability":project.get("artifact_availability","Available" if path.is_file() else "Missing"),
            "Revision":project.get("model_revision","—"),"Dimension":project.get("embedding_dimension","—"),"p95 latency (ms)":project.get("p95_latency_ms","—"),"Fusion":project.get("fusion_method","—"),
        })
        technical.append({"Project": project["name"], "Relative path": str(relative_artifact)})
    live = sum(row["Runtime"] == "Metadata verified" for row in rows)
    counts = portfolio_counts()
    experimental=sum(row["Role"]=="Challenger" or "Experimental" in row["Role"] for row in rows); production=len(rows)-experimental
    evidence_strip([("Production-style",str(production),"Champion/project artifact"),("Experimental",str(experimental),"Challenger artifact"),("Metadata verified",str(live),"No eager native reload"),("Live inference",str(sum(row["Live module"]=="Ready" for row in rows)),"UI contract"),("Evaluated candidates",str(counts["models_compared"]),"Saved experiment rows")])
    information_panel("Registry ayrımı", f"Persist edilmiş ve metadata/okunabilirlik sözleşmesi doğrulanmış artifact sayısı {live}; {counts['models_compared']} değeri kayıtlı değerlendirme deneylerini ifade eder. Native deep reload yalnız açık inference veya izole sağlık kontrolü sırasında yapılır.")
    decision_banner("Challengers neden terfi edilmedi?","V2 Random Forest historical experimental challenger’dır. V2.1 HistGradientBoosting Best Research Candidate olsa da Different historical split nedeniyle direct superiority established değildir ve seçilmiş nesnesi retraining olmadan persist edilememiştir. XGBoost ranker ortak holdout baseline’ını tekrarlanabilir biçimde geçmedi. Live path Verified Champion V1’de kaldı.")
    section_heading("Model governance inventory","Validation, runtime ve karar aynı görünümde.")
    metric_table(pd.DataFrame(rows))
    with st.expander("Technical artifact locations", expanded=False):
        metric_table(pd.DataFrame(technical))
