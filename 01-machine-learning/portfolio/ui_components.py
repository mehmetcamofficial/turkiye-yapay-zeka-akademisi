from __future__ import annotations

from datetime import date, datetime
from html import escape
from pathlib import Path
from typing import Any
import json
import math

import pandas as pd
import streamlit as st

from portfolio.i18n import t as _t

STATUS_CSS = {
    "verified": "badge-verified",
    "available": "badge-available",
    "experimental": "badge-experimental",
    "limited": "badge-limited",
    "archived": "badge-archived",
    "roadmap": "badge-roadmap",
    "unavailable": "badge-unavailable",
    "error": "badge-error",
}

STATUS_I18N_KEYS = {
    "verified": "status_verified",
    "available": "status_available",
    "experimental": "status_experimental",
    "limited": "status_limited",
    "archived": "status_archived",
    "roadmap": "status_roadmap",
    "unavailable": "status_unavailable",
    "error": "status_error",
}


def _map_status(legacy: str) -> str:
    mapping = {
        "Tamamlandı": "available",
        "Hazır": "available",
        "Sağlıklı": "available",
        "Doğrulandı": "verified",
        "Açık": "available",
        "Deneysel": "experimental",
        "Terfi edilmedi": "experimental",
        "Geliştiriliyor": "experimental",
        "Planlandı": "roadmap",
        "Veri Bekleniyor": "limited",
        "Henüz Başlanmadı": "roadmap",
        "Henüz": "roadmap",
        "Eksik": "limited",
        "Şema Uyumsuz": "limited",
        "Tamamlandı": "available",
        "Current": "available",
        "Implemented": "available",
    }
    return mapping.get(legacy, "experimental")


def normalize_status(legacy: str) -> str:
    return _map_status(legacy)


def status_badge(legacy_status: str, *, lang_override: str | None = None) -> str:
    normalized = _map_status(legacy_status)
    css_class = STATUS_CSS.get(normalized, "badge-experimental")
    i18n_key = STATUS_I18N_KEYS.get(normalized, "status_experimental")
    if lang_override:
        from portfolio.i18n import TRANSLATIONS, DEFAULT_LANG
        label = TRANSLATIONS.get(i18n_key, {}).get(lang_override, TRANSLATIONS.get(i18n_key, {}).get(DEFAULT_LANG, legacy_status))
    else:
        label = _t(i18n_key)
    return f'<span class="badge {css_class}">{escape(label)}</span>'


def render_safe_table(
    data: Any,
    *,
    title: str | None = None,
    max_rows: int = 100,
    column_map: dict[str, str] | None = None,
    download_name: str | None = None,
    empty_message: str | None = None,
) -> None:
    try:
        if isinstance(data, pd.DataFrame):
            frame = data.copy(deep=True).reset_index(drop=True)
        elif isinstance(data, dict):
            frame = pd.DataFrame([data])
        else:
            frame = pd.DataFrame(data).copy(deep=True).reset_index(drop=True)
        total = len(frame)
        if max_rows is not None:
            frame = frame.head(max(0, max_rows))
        if frame.empty:
            st.markdown(
                f'<div class="empty-state"><strong>{_t("table_empty")}</strong>'
                f"<p>{empty_message or ''}</p></div>",
                unsafe_allow_html=True,
            )
            return
        if title:
            section_heading(title)
        display_columns = list(frame.columns)
        if column_map:
            headers = [column_map.get(c, c) for c in display_columns]
        else:
            headers = [_normalize_header(c) for c in display_columns]
        header_html = "".join(f'<th scope="col">{escape(h)}</th>' for h in headers)
        rows_html = ""
        for row in frame.itertuples(index=False, name=None):
            cells = "".join(
                f"<td>{_display_value(v)}</td>" for v in row
            )
            rows_html += f"<tr>{cells}</tr>"
        st.markdown(
            f'<div class="safe-table-wrap"><table class="safe-table">'
            f"<thead><tr>{header_html}</tr></thead><tbody>{rows_html}</tbody></table></div>",
            unsafe_allow_html=True,
        )
        if total > len(frame):
            st.caption(_t("table_showing", count=len(frame), total=total))
        if download_name:
            source = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
            st.download_button(
                _t("table_download"),
                source.to_csv(index=False).encode("utf-8"),
                download_name,
                "text/csv",
            )
    except Exception as exc:
        st.error(f"Table error: {exc}")
        with st.expander(_t("error_detail"), expanded=False):
            st.code(type(exc).__name__)


def _normalize_header(header: str) -> str:
    friendly = {
        "relative_path": _t("table_file"),
        "extension": _t("table_type"),
        "size_mb": _t("table_size"),
        "row_count": _t("table_rows"),
        "column_count": _t("table_columns"),
        "sha256_short": _t("table_sha256"),
        "readable": _t("table_readable"),
        "status": _t("table_status"),
        "artifact": _t("table_artifact"),
        "Durum": _t("table_status"),
        "Artifact": _t("table_artifact"),
    }
    return friendly.get(header, header.replace("_", " ").title())


def _display_value(value: Any) -> str:
    try:
        if value is None:
            return "—"
        if hasattr(value, "item") and not isinstance(value, (str, bytes, dict, list, tuple)):
            value = value.item()
        try:
            missing = pd.isna(value)
            if isinstance(missing, bool) and missing:
                return "—"
        except (TypeError, ValueError):
            pass
        if isinstance(value, (pd.Timestamp, datetime, date)):
            if isinstance(value, datetime):
                text = value.isoformat(sep=" ", timespec="seconds")
            else:
                text = value.isoformat()
        elif isinstance(value, bool):
            text = "✓" if value else "—"
        elif isinstance(value, float):
            text = f"{value:.4f}" if math.isfinite(value) else "—"
        elif isinstance(value, (dict, list, tuple, set)):
            text = json.dumps(
                list(value) if isinstance(value, (tuple, set)) else value,
                ensure_ascii=False,
                default=str,
            )
        else:
            text = str(value)
        return escape(text, quote=True)
    except Exception:
        try:
            return escape(str(value), quote=True)
        except Exception:
            return "—"


def hero_panel(title: str, subtitle: str, kicker: str | None = None) -> None:
    kicker_html = f'<div class="hero-kicker">{escape(kicker)}</div>' if kicker else ""
    st.markdown(
        f'<div class="hero">{kicker_html}<h1>{escape(title)}</h1>'
        f"<p>{escape(subtitle)}</p></div>",
        unsafe_allow_html=True,
    )


def section_heading(title: str, subtitle: str = "") -> None:
    sub = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f'<div class="section-heading"><h2>{escape(title)}</h2>{sub}</div>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def kpi_grid(items: list[tuple[str, str, str]]) -> None:
    html = "".join(
        f'<div class="metric-card"><small>{escape(a)}</small><strong>{escape(b)}</strong>'
        f"<span>{escape(c)}</span></div>"
        for a, b, c in items
    )
    st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)


def card_grid(items: list[dict[str, str]]) -> None:
    html = "".join(
        f'<div class="card"><h3>{escape(item.get("title", ""))}</h3>'
        f"<p>{escape(item.get("text", ""))}</p></div>"
        for item in items
    )
    st.markdown(f'<div class="card-grid">{html}</div>', unsafe_allow_html=True)


def callout(title: str, text: str) -> None:
    st.markdown(
        f'<div class="callout"><strong>{escape(title)}</strong><p>{escape(text)}</p></div>',
        unsafe_allow_html=True,
    )


def empty_state(title: str, text: str = "") -> None:
    st.markdown(
        f'<div class="empty-state"><strong>{escape(title)}</strong>'
        f"<p>{escape(text)}</p></div>",
        unsafe_allow_html=True,
    )


def evidence_strip(items: list[tuple[str, str, str]]) -> None:
    html = "".join(
        f'<div class="metric-card"><small>{escape(a)}</small>'
        f"<strong>{escape(str(b))}</strong><span>{escape(c)}</span></div>"
        for a, b, c in items
    )
    st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)
