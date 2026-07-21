"""Artifact-driven registry for Data Science assignments."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from portfolio.config import DATA_SCIENCE_FINAL_DIR, DATA_SCIENCE_MIDTERM_DIR, TRENDYOL_PROFILE_DIR
from portfolio.loaders import load_json_safe

REQUIRED_COLUMNS = ["indirim_orani", "musteri_puani", "odeme_turu", "musteri_tipi",
                    "siparis_tarihi", "sehir", "kategori", "birim_fiyat", "toplam_tutar", "teslimat_gunu"]
EXPECTED_OUTPUTS = ["data_profile.csv", "missing_values.csv", "duplicate_summary.json",
                    "cleaning_summary.json", "outlier_analysis.csv", "category_summary.csv",
                    "customer_type_summary.csv", "payment_type_countplot.png",
                    "total_amount_histogram.png", "total_amount_boxplot.png",
                    "final_clean_dataset.csv", "final_summary.md"]
TOTAL_QUESTIONS = 15


def _discover_dataset(project_dir: Path, configured: Path | None = None) -> Path | None:
    candidates = []
    if configured is not None:
        candidates.append(configured)
    env_path = os.environ.get("ACADEMY_ECOMMERCE_DATA")
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.extend(sorted((project_dir / "data").glob("*.csv")))
    return next((path.resolve() for path in candidates if path.is_file()), None)


def _columns(path: Path | None) -> list[str]:
    if path is None:
        return []
    try:
        frame = pd.read_csv(path, nrows=0)
        if len(frame.columns) == 1:
            alternate = pd.read_csv(path, nrows=0, sep=";")
            if len(alternate.columns) > 1:
                frame = alternate
        return [str(column) for column in frame.columns]
    except (OSError, UnicodeError, pd.errors.ParserError):
        return []


def evaluate_midterm(project_dir: Path = DATA_SCIENCE_MIDTERM_DIR,
                     dataset_path: Path | None = None,
                     colab_url: str | None = None) -> dict[str, Any]:
    """Evaluate status from local data, schema, notebook, outputs and Colab URL."""
    dataset = _discover_dataset(project_dir, dataset_path)
    available = _columns(dataset)
    missing = [column for column in REQUIRED_COLUMNS if column not in available]
    compatible = bool(dataset and available and not missing)
    notebook = project_dir / "notebook" / "data_science_midterm.ipynb"
    outputs = project_dir / "outputs"
    existing_outputs = [name for name in EXPECTED_OUTPUTS if (outputs / name).is_file()]
    configured_colab = colab_url if colab_url is not None else os.environ.get("DATA_SCIENCE_MIDTERM_COLAB_URL", "")
    inventory = load_json_safe(str(project_dir / "outputs" / "dataset_inventory.json"))
    use_saved_schema = project_dir.resolve() == DATA_SCIENCE_MIDTERM_DIR.resolve()
    schema_report = load_json_safe(str(TRENDYOL_PROFILE_DIR / "outputs" / "schema_report.json")) if use_saved_schema else {}
    supported_questions = schema_report.get("supported_questions", list(range(1, TOTAL_QUESTIONS + 1)) if compatible else [])
    blocked_questions = schema_report.get("blocked_questions", [] if compatible else list(range(1, TOTAL_QUESTIONS + 1)))
    profile_outputs = sorted(path.name for path in (TRENDYOL_PROFILE_DIR / "outputs").glob("*") if path.is_file() and path.name != ".gitkeep")
    adapted_outputs = {"table_summary.csv", "missing_values.csv", "duplicate_summary.csv", "categorical_summary.csv",
                       "text_length_summary.csv", "schema_report.json", "data_quality_report.json", "profile_summary.md"}
    adapted_complete = adapted_outputs.issubset(profile_outputs)
    all_complete = bool(dataset) and adapted_complete and notebook.is_file() and bool(configured_colab)
    if dataset is None:
        status = "Veri Bekleniyor"
    elif all_complete:
        status = "Tamamlandı"
    else:
        status = "Geliştiriliyor"
    timestamp_candidates = [path.stat().st_mtime for path in [dataset, notebook] if path and path.is_file()]
    return {
        "id":"data_science_midterm", "name":"Trendyol Veri Kalitesi ve Keşifsel Veri Analizi", "category":"Veri Bilimi",
        "status":status, "dataset":"TEKNOFEST Trendyol 2026 Datathon / akademi e-ticaret verisi",
        "source":"https://www.kaggle.com/datasets/thetrumpet/teknofest-trendyol-2026-datathonn",
        "dataset_path":dataset, "notebook_path":notebook, "colab_url":configured_colab,
        "required_columns":REQUIRED_COLUMNS, "available_columns":available,
        "missing_columns":missing, "completed_questions":12 if adapted_complete else 0,
        "supported_questions":supported_questions, "blocked_questions":blocked_questions,
        "total_questions":TOTAL_QUESTIONS, "expected_outputs":EXPECTED_OUTPUTS,
        "existing_outputs":existing_outputs,
        "data_source_documented":(project_dir/"DATA_SOURCE.md").is_file(),
        "schema_compatible":compatible, "notebook_ready":notebook.is_file(),
        "outputs_ready":adapted_complete,
        "colab_configured":bool(configured_colab),
        "inventory":inventory, "inventory_ready":bool(inventory),
        "downloaded_file_count":len(inventory),
        "downloaded_size_bytes":sum(int(record.get("size_bytes", 0)) for record in inventory),
        "profile_ready":(TRENDYOL_PROFILE_DIR/"outputs/profile_summary.md").is_file(),
        "profile_outputs":profile_outputs,
        "last_verified":datetime.fromtimestamp(max(timestamp_candidates)).astimezone().isoformat(timespec="minutes") if timestamp_candidates else None,
        "project_dir":project_dir,
    }


def evaluate_final_project(project_dir: Path = DATA_SCIENCE_FINAL_DIR) -> dict[str, Any]:
    """Connect final-project planning to the independently validated ML artifact."""
    model_ready=(TRENDYOL_PROFILE_DIR.parents[1]/"01-machine-learning/trendyol-search-relevance/models/trendyol_relevance_pipeline.pkl").is_file()
    return {"id":"data_science_final", "name":"Trendyol Search Relevance Intelligence",
            "category":"Veri Bilimi Final Projesi", "status":"Geliştiriliyor" if model_ready else "Planlandı",
            "dataset":"TEKNOFEST Trendyol 2026 Datathon (planlanan)",
            "notebook_ready":any((project_dir/"notebook").glob("*.ipynb")),
            "outputs_ready":model_ready,
            "data_source_documented":(project_dir/"DATA_SOURCE.md").is_file(),
            "schema_compatible":False, "project_dir":project_dir}


def data_science_counts() -> dict[str, int]:
    midterm, final = evaluate_midterm(), evaluate_final_project()
    return {"assignments":2, "completed":sum(item["status"]=="Tamamlandı" for item in [midterm, final]),
            "datasets_ready":int(midterm["dataset_path"] is not None),
            "notebooks_ready":int(midterm["notebook_ready"]),
            "colab_published":int(midterm["colab_configured"])}
