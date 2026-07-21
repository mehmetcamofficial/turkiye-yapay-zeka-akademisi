"""Unified health view for expected local artifacts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import hashlib
import json
import numpy as np

import pandas as pd
import streamlit as st

from portfolio.config import DATA_SCIENCE_MIDTERM_DIR, TRENDYOL_PROFILE_DIR
from portfolio.project_registry import get_project_registry
from portfolio.ui_components import evidence_strip,page_header,information_panel,metric_table,section_heading


@st.cache_data(show_spinner=False)
def _file_health(path_text: str, modified: float, size: int) -> tuple[bool, str, str]:
    """Check readability and hash practical artifacts; cache by immutable metadata."""
    try:
        with open(path_text, "rb") as handle:
            handle.read(1)
        if size > 50 * 1024**2:
            return True, "Atlandı (>50 MB)", datetime.now().astimezone().isoformat(timespec="minutes")
        digest = hashlib.sha256()
        with open(path_text, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return True, digest.hexdigest()[:12], datetime.now().astimezone().isoformat(timespec="minutes")
    except OSError:
        return False, "Kullanılamıyor", datetime.now().astimezone().isoformat(timespec="minutes")

@st.cache_data(show_spinner=False)
def _retrieval_type(path_text:str,modified:float,size:int)->str:
    try:
        path=Path(path_text); metadata=json.loads(path.with_name(path.stem+"_metadata.json").read_text(encoding="utf-8"))
        if not metadata.get("fingerprint") or not metadata.get("rows"):return "Rebuild Required"
        return f"RetrievalAsset · {metadata['rows']:,} rows · fingerprint {metadata['fingerprint'][:12]}"
    except Exception:return "Incompatible"

@st.cache_resource(show_spinner=False)
def _dense_index_type(path_text:str,modified:float,size:int,metadata_modified:float)->str:
    try:
        path=Path(path_text); metadata=json.loads(path.with_name(path.stem+"_metadata.json").read_text(encoding="utf-8")); matrix=np.load(path,mmap_mode="r")
        expected=(int(metadata["product_count"]),int(metadata["embedding_dimension"]))
        if matrix.shape!=expected or str(matrix.dtype)!=metadata["dtype"]:return "Rebuild Required"
        if not np.isfinite(matrix).all():return "Rebuild Required"
        return f"DenseIndex · {matrix.shape[0]:,}×{matrix.shape[1]} · {matrix.dtype} · {metadata['model_revision'][:12]}"
    except Exception:return "Incompatible"


def _record(group: str, root, relative: str) -> dict:
    path = root / relative.rstrip("/")
    exists = path.exists()
    readable, digest, verified = (True, "Dizin", "—") if path.is_dir() else (_file_health(str(path), path.stat().st_mtime, path.stat().st_size) if path.is_file() else (False, "—", "—"))
    # Health is deliberately metadata/readability-only. Deep native reloads run
    # through explicit isolated checks, never during a page render.
    model_result=None; retrieval_type=None
    if path.suffix==".joblib" and path.is_file():
        retrieval_type=_retrieval_type(str(path),path.stat().st_mtime,path.stat().st_size)
    if path.suffix==".npy" and path.is_file():
        metadata=path.with_name(path.stem+"_metadata.json"); retrieval_type=_dense_index_type(str(path),path.stat().st_mtime,path.stat().st_size,metadata.stat().st_mtime if metadata.is_file() else 0)
    loadable = model_result.ok if model_result else (readable if path.is_file() else exists)
    return {"Dependent module": group, "Artifact": relative, "Status": "Healthy" if exists and readable else "Missing",
            "Algorithm / object": retrieval_type or ("Persisted artifact · deep reload isolated" if path.suffix in {".pkl",".joblib"} and exists else ("Not persisted" if path.suffix in {".pkl",".joblib",".npy"} and not exists else "—")),
            "Readable": readable,
            "Loadable": loadable,
            "Type": "Directory" if path.is_dir() else "File",
            "Size (KB)": round(path.stat().st_size / 1024, 1) if path.is_file() else None,
            "SHA-256": digest,
            "Cached verification": verified,
            "Modified": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="minutes") if exists else "—"}


def render() -> None:
    page_header("Artifact Health", "Availability, checksum, metadata, reload contract and dependency health for local portfolio artifacts.", "MODEL RELIABILITY")
    rows = []
    for project in get_project_registry():
        for relative in project["expected_output_files"]:
            rows.append(_record(project["short_name"], project["directory"], relative))
    rows.extend([
        _record("Data Science", DATA_SCIENCE_MIDTERM_DIR, "outputs/dataset_inventory.json"),
        _record("Data Science", DATA_SCIENCE_MIDTERM_DIR, "notebook/data_science_midterm.ipynb"),
        _record("Trendyol Profile", TRENDYOL_PROFILE_DIR, "outputs/profile_summary.md"),
        _record("Trendyol Profile", TRENDYOL_PROFILE_DIR, "outputs/schema_report.json"),
        _record("Trendyol Profile", TRENDYOL_PROFILE_DIR, "outputs/data_quality_report.json"),
    ])
    frame = pd.DataFrame(rows)
    healthy = int((frame["Status"] == "Healthy").sum())
    model_rows=frame[frame["Artifact"].astype(str).str.endswith(".pkl")]; reload_ok=int(model_rows["Loadable"].sum()) if not model_rows.empty else 0
    evidence_strip([("Required artifacts",str(len(frame)),"Registry contract"),("Healthy",str(healthy),"Readable"),("Missing",str(len(frame)-healthy),"Needs review"),("Model files",f"{reload_ok}/{len(model_rows)}","Readable; deep reload isolated"),("Checksum","Cached","Not recomputed per render")])
    information_panel("Health definition", "Mevcudiyet ve okunabilirlik kontrol edilir; 50 MB altındaki dosyalar için SHA-256 kısa özeti cache'lenir. Native modeller sayfa render'ında yüklenmez; deep reload açık inference veya izole sağlık kontrolüyle yapılır.")
    section_heading("Technical artifact details","Experimental artifacts remain visually and operationally separate in the Registry.")
    metric_table(frame)
