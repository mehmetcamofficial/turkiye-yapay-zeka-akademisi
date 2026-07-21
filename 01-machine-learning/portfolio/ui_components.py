"""Reusable presentation components shared by portfolio pages."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import date, datetime
from html import escape
import json
import math

import pandas as pd
import streamlit as st


def normalize_display_value(value: Any) -> str:
    """Return an escaped, deterministic display string without raising."""
    try:
        if hasattr(value, "item") and not isinstance(value, (str, bytes, dict, list, tuple)):
            value = value.item()
        if value is None:
            return "—"
        try:
            missing = pd.isna(value)
            if isinstance(missing, bool) and missing:
                return "—"
        except (TypeError, ValueError):
            pass
        if isinstance(value, (pd.Timestamp, datetime, date)):
            text = value.isoformat(sep=" ", timespec="seconds") if isinstance(value, datetime) else value.isoformat()
        elif isinstance(value, bool):
            text = "Evet" if value else "Hayır"
        elif isinstance(value, float):
            text = f"{value:.4f}" if math.isfinite(value) else "—"
        elif isinstance(value, (dict, list, tuple, set)):
            serializable = list(value) if isinstance(value, (tuple, set)) else value
            text = json.dumps(serializable, ensure_ascii=False, default=str, sort_keys=isinstance(value, dict))
        else:
            text = str(value)
        return escape(text, quote=True)
    except Exception:
        try:
            return escape(str(value), quote=True)
        except Exception:
            return "—"


def prepare_dataframe_for_display(data: Any, max_rows: int | None = None) -> tuple[list[str], list[list[str]], int]:
    """Copy and normalize tabular data; never mutate the caller's object."""
    if isinstance(data, pd.DataFrame):
        frame = data.copy(deep=True).reset_index(drop=True)
    elif isinstance(data, dict):
        frame = pd.DataFrame([data])
    else:
        frame = pd.DataFrame(data).copy(deep=True).reset_index(drop=True)
    total = len(frame)
    if max_rows is not None:
        frame = frame.head(max(0, max_rows)).copy()
    headers = [normalize_display_value(column) for column in frame.columns]
    rows = [[normalize_display_value(value) for value in row] for row in frame.itertuples(index=False, name=None)]
    return headers, rows, total


def safe_html_table(headers: list[str], rows: list[list[str]]) -> str:
    header_html = "".join(f'<th scope="col">{header}</th>' for header in headers)
    body_html = "".join("<tr>" + "".join(f"<td>{value}</td>" for value in row) + "</tr>" for row in rows)
    return f'<div class="safe-table-wrap"><table class="safe-table"><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>'


def classification_report_frame(report: str) -> pd.DataFrame:
    """Parse sklearn's text report into a compact display frame."""
    rows: list[dict[str, Any]] = []
    for line in report.splitlines():
        parts = line.split()
        if not parts or parts[0] == "precision":
            continue
        try:
            if parts[0] == "accuracy" and len(parts) >= 3:
                rows.append({"Sınıf/Özet": "accuracy", "Precision": None, "Recall": None,
                             "F1": float(parts[-2]), "Support": int(parts[-1])})
            elif len(parts) >= 5:
                rows.append({"Sınıf/Özet": " ".join(parts[:-4]), "Precision": float(parts[-4]),
                             "Recall": float(parts[-3]), "F1": float(parts[-2]), "Support": int(parts[-1])})
        except (TypeError, ValueError):
            continue
    return pd.DataFrame(rows)


def render_safe_table(data: Any, *, title: str | None = None, max_rows: int = 100,
                      allow_arrow: bool = False, download_name: str | None = None,
                      empty_message: str = "Rapor henüz mevcut değil.") -> None:
    """Render tabular data without Arrow by default; ``allow_arrow`` is reserved."""
    try:
        headers, rows, total = prepare_dataframe_for_display(data, max_rows=max_rows)
        if not headers or not rows:
            empty_state_panel("Artifact bulunamadı", empty_message)
            return
        if title:
            section_heading(title)
        # Semantic HTML deliberately avoids the Arrow serialization layer.
        st.markdown(safe_html_table(headers, rows), unsafe_allow_html=True)
        if total > len(rows):
            st.caption(f"{total} kaydın ilk {len(rows)} satırı gösteriliyor.")
        if download_name:
            source = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
            st.download_button("CSV olarak indir", source.to_csv(index=False).encode("utf-8"), download_name, "text/csv")
    except Exception as exc:
        st.error("Tablo güvenli biçimde görüntülenemedi. Kaydedilmiş çıktıyı kontrol edin.")
        with st.expander("Teknik ayrıntı", expanded=False):
            st.code(type(exc).__name__)


def hero_panel(title: str, subtitle: str, kicker: str = "PLATFORM MODULE") -> None:
    st.markdown(f'<section class="portfolio-hero"><div class="portfolio-kicker">{kicker}</div><h1>{title}</h1><p>{subtitle}</p></section>', unsafe_allow_html=True)


def section_heading(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="section-heading"><h2>{title}</h2><p>{subtitle}</p></div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    css = {"Tamamlandı":"complete", "Hazır":"complete", "Geliştiriliyor":"progress",
           "Doğrulandı":"complete", "Açık":"complete", "Planlandı":"planned", "Veri Bekleniyor":"planned", "Şema Uyumsuz":"progress"}.get(status, "empty")
    return f'<span class="status status-{css}">{status}</span>'


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def project_card(project: dict[str, Any], action_label: str = "Projeyi aç") -> bool:
    primary = project["primary_metric_value"]
    primary_text = "—" if primary is None else f"{primary:.4f}"
    st.markdown(
        f'''<div class="project-card">{status_badge(project['status'])}<h3>{project['name']}</h3>
        <p>{project['description']}</p><div class="card-meta">
        <div><small>Kategori</small><strong>{project['category']}</strong></div>
        <div><small>Veri seti</small><strong>{project['dataset']} · {project['dataset_size']}</strong></div>
        <div><small>Final model</small><strong>{project['final_model']}</strong></div>
        <div><small>{project['primary_metric_name']}</small><strong>{primary_text}</strong></div>
        <div><small>Validation</small><strong>{'Mevcut' if project['validation_available'] else 'Eksik'}</strong></div>
        <div><small>Model artifact</small><strong>{'Mevcut' if project['model_artifact_available'] else 'Eksik'}</strong></div>
        </div></div>''', unsafe_allow_html=True)
    return st.button(action_label, key=f"open_{project['id']}", disabled=project["id"] not in {"churn", "regression", "nlp"})


def information_panel(title: str, text: str) -> None:
    st.markdown(f'<div class="info-panel"><strong>{title}</strong><p>{text}</p></div>', unsafe_allow_html=True)


def empty_state_panel(title: str, text: str) -> None:
    st.markdown(f'<div class="empty-panel"><strong>{title}</strong><p>{text}</p></div>', unsafe_allow_html=True)


def warning_panel(text: str) -> None:
    st.warning(text)


def prediction_result_card(label: str, value: str, detail: str) -> None:
    st.markdown(f'<div class="prediction-card"><small>{label}</small><h2>{value}</h2><p>{detail}</p></div>', unsafe_allow_html=True)


def metric_table(frame: pd.DataFrame, empty_message: str = "Rapor henüz mevcut değil.") -> None:
    """Backward-compatible small report renderer with no Arrow serialization."""
    render_safe_table(frame, max_rows=100, allow_arrow=False, empty_message=empty_message)


def artifact_checklist(project: dict[str, Any]) -> None:
    rows = []
    directory: Path = project["directory"]
    for relative in project["expected_output_files"]:
        path = directory / relative.rstrip("/")
        rows.append({"Artifact": relative, "Durum": "Mevcut" if path.exists() else "Eksik"})
    metric_table(pd.DataFrame(rows))
