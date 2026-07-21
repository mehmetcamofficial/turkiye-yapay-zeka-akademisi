"""Unified health view for expected local artifacts."""

from __future__ import annotations

from datetime import datetime
import hashlib

import pandas as pd
import streamlit as st

from portfolio.config import DATA_SCIENCE_MIDTERM_DIR, TRENDYOL_PROFILE_DIR
from portfolio.loaders import load_model_safe
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


def _record(group: str, root, relative: str) -> dict:
    path = root / relative.rstrip("/")
    exists = path.exists()
    readable, digest, verified = (True, "Dizin", "—") if path.is_dir() else (_file_health(str(path), path.stat().st_mtime, path.stat().st_size) if path.is_file() else (False, "—", "—"))
    model_result=load_model_safe(path) if path.suffix == ".pkl" and path.is_file() else None
    loadable = model_result.ok if model_result else (readable if path.is_file() else exists)
    return {"Dependent module": group, "Artifact": relative, "Status": "Healthy" if exists and readable else "Missing",
            "Algorithm / object": type(model_result.model).__name__ if model_result and model_result.ok else ("Not persisted" if path.suffix==".pkl" and not exists else "—"),
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
    evidence_strip([("Required artifacts",str(len(frame)),"Registry contract"),("Healthy",str(healthy),"Readable"),("Missing",str(len(frame)-healthy),"Needs review"),("Model reload",f"{reload_ok}/{len(model_rows)}","Fresh compatible runtime"),("Checksum","Cached","Not recomputed per render")])
    information_panel("Health definition", "Mevcudiyet ve okunabilirlik kontrol edilir; 50 MB altındaki dosyalar için SHA-256 kısa özeti cache'lenir. Model çalışma zamanı uygunluğu Model Registry sayfasında ayrıca doğrulanır.")
    section_heading("Technical artifact details","Experimental artifacts remain visually and operationally separate in the Registry.")
    metric_table(frame)
