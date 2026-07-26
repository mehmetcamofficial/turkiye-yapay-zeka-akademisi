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

LEGACY_STATUS_MAP = {
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
    "Eksik": "limited",
    "Şema Uyumsuz": "limited",
}


def normalize_status(legacy: str) -> str:
    return LEGACY_STATUS_MAP.get(legacy, "experimental")


def _fmt(val: Any, default: str = "—") -> str:
    if val is None:
        return default
    if isinstance(val, float):
        if abs(val) >= 1000:
            return f"{val:.1f}"
        if abs(val) >= 1:
            return f"{val:.4f}"
        return f"{val:.4f}"
    if isinstance(val, int):
        return str(val)
    return str(val)


def _display_value(value: Any) -> str:
    return _fmt(value)


def format_metric(value: float | None, digits: int = 4) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}"


def format_ranking_metric(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.4f}"


def format_delta(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.4f}"


def format_latency_ms(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.0f} ms"


def status_badge(status: str) -> str:
    """Accept either normalized status (verified, available, etc.) or legacy Turkish status."""
    normalized = LEGACY_STATUS_MAP.get(status, status)
    if normalized not in STATUS_CSS:
        normalized = "experimental"
    css_class = STATUS_CSS.get(normalized, "badge-experimental")
    label = _t(STATUS_I18N_KEYS.get(normalized, "status_experimental"))
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
            cells = "".join(f"<td>{escape(_fmt(v))}</td>" for v in row)
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
    except Exception:
        import logging
        LOGGER = logging.getLogger(__name__)
        LOGGER.exception("render_safe_table failed")
        st.error(_t("table_error_unavailable"))
        with st.expander(_t("error_detail"), expanded=False):
            st.markdown(_t("table_error_detail"))


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


def kpi_grid(items: list[tuple[str, str, str | None]]) -> None:
    html = "".join(
        f'<div class="metric-card"><small>{escape(a)}</small>'
        f"<strong>{escape(str(b))}</strong>"
        f"{'<span>' + escape(c) + '</span>' if c else ''}</div>"
        for a, b, c in items
    )
    st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)


def kpi_grid_mixed(items: list[tuple[str, str, str | None]]) -> None:
    """Like kpi_grid but second value is raw HTML (for status badges)."""
    html = "".join(
        f'<div class="metric-card"><small>{escape(a)}</small>'
        f"<strong>{b}</strong>"
        f"{'<span>' + escape(c) + '</span>' if c else ''}</div>"
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


def evidence_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f'<div class="metric-card"><small>{escape(label)}</small>'
        f"<strong>{escape(value)}</strong><span>{escape(note)}</span></div>",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    st.metric(label, value, help=help_text)


def decision_banner(title: str, text: str) -> None:
    st.markdown(
        f'<div class="callout" style="border-left:4px solid var(--warning);background:var(--warning-soft)">'
        f"<strong>{escape(title)}</strong><p>{escape(text)}</p></div>",
        unsafe_allow_html=True,
    )


def comparison_cards(items: list[dict[str, str]]) -> None:
    cards = ""
    for x in items:
        kind = x.get("kind", "experimental")
        css = "champion" if kind == "champion" else "experimental"
        cards += (
            f'<div class="card" style="border-top:3px solid '
            f'{("var(--success)" if kind == "champion" else "var(--warning)")}">'
            f"{status_badge(x.get('status', 'experimental'))}"
            f"<h3>{escape(x.get('title', ''))}</h3>"
            f"<p>{escape(x.get('algorithm', ''))}</p>"
            f"<strong>{escape(x.get('metric', ''))}</strong>"
            f"<p>{escape(x.get('note', ''))}</p></div>"
        )
    st.markdown(f'<div class="card-grid">{cards}</div>', unsafe_allow_html=True)


def evidence_strip(items: list[tuple[str, str, str]]) -> None:
    kpi_grid(items)


def page_header(title: str, subtitle: str, kicker: str | None = None) -> None:
    hero_panel(title, subtitle, kicker)


def external_action(label: str, url: str) -> None:
    st.markdown(
        f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" '
        f'class="external-action">{escape(label)}</a>',
        unsafe_allow_html=True,
    )


def information_panel(title: str, text: str) -> None:
    st.markdown(
        f'<div class="information-panel"><strong>{escape(title)}</strong>'
        f"<p>{escape(text)}</p></div>",
        unsafe_allow_html=True,
    )


def empty_state_panel(status: str, message: str) -> None:
    empty_state(status, message)


def metric_table(data: Any, empty_message: str | None = None) -> None:
    render_safe_table(data, empty_message=empty_message)


def artifact_checklist(project: dict[str, Any]) -> None:
    required = project.get("required_artifacts", [])
    existing = project.get("existing_artifacts", [])
    html = '<div class="checklist">'
    for art in required:
        ok = art in existing
        icon = "✓" if ok else "—"
        cls = "checklist-item check-ok" if ok else "checklist-item check-miss"
        html += f'<div class="{cls}"><span class="check-icon">{icon}</span>'
        html += f"<span>{escape(art)}</span></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def architecture_flow(stages: list[tuple[str, str]]) -> None:
    dot_map = {"current": "#22c55e", "experimental": "#f59e0b", "planned": "#94a3b8"}
    status_map = {"current": "Operational", "experimental": "Experimental", "planned": "Planned"}
    html = '<div class="arch-cards">'
    for i, (name, stage_status) in enumerate(stages):
        dot_color = dot_map.get(stage_status, "#94a3b8")
        status_label = status_map.get(stage_status, stage_status)
        arrow = ""
        if i > 0:
            arrow = '<div class="arch-connector"><span class="arch-connector-arrow">→</span></div>'
        html += (
            f'{arrow}'
            f'<div class="arch-card">'
            f'<div class="arch-card-dot" style="background:{dot_color};"></div>'
            f'<div class="arch-card-body">'
            f'<span class="arch-card-title">{escape(name)}</span>'
            f'<span class="arch-card-status">{escape(status_label)}</span>'
            f"</div></div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def classification_report_frame(
    data: pd.DataFrame | dict[str, Any] | None,
    *,
    title: str | None = None,
) -> None:
    if data is None or (isinstance(data, pd.DataFrame) and data.empty):
        empty_state("Classification Report", "Not available")
        return
    try:
        if isinstance(data, dict):
            data = pd.DataFrame(data)
        render_safe_table(data, title=title)
    except Exception:
        empty_state("Classification Report", "Could not render")


def prediction_result_card(
    label: str,
    probability: float | None,
    true_label: str | None = None,
) -> None:
    pct = f"{probability * 100:.1f}%" if probability is not None else "—"
    html = (
        f'<div class="prediction-card">'
        f"<strong>{escape(label)}</strong>"
        f"<span>{escape(pct)}</span>"
        f"{'<small>True: ' + escape(true_label) + '</small>' if true_label else ''}"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def navigate_to(section: str, page_key: str) -> None:
    st.session_state["nav_section"] = section
    st.session_state[f"nav_page_{section}"] = page_key


def log_activity(capability: str, summary: str) -> None:
    from datetime import datetime
    if "cc_activity_log" not in st.session_state:
        st.session_state["cc_activity_log"] = []
    st.session_state["cc_activity_log"].append({
        "capability": capability,
        "timestamp": datetime.now(),
        "summary": summary,
    })


def command_hero(
    title: str,
    subtitle: str,
    badges: list[tuple[str, str]],
    primary_cta_text: str,
    primary_cta_key: tuple[str, str],
    secondary_cta_text: str,
    secondary_cta_key: tuple[str, str],
    test_count: int | str,
    test_label: str,
) -> None:
    badges_html = "".join(
        f'<span class="command-hero-badge command-hero-badge-{css}">{escape(label)}</span>'
        for label, css in badges
    )
    st.markdown(
        f'<div class="command-hero">'
        f'<div class="command-hero-main">'
        f'<div class="command-hero-eyebrow">{escape(_t("command_center_eyebrow"))}</div>'
        f"<h1>{escape(title)}</h1>"
        f"<p>{escape(subtitle)}</p>"
        f'<div class="command-hero-badges">{badges_html}</div>'
        f'<div class="command-hero-actions">',
        unsafe_allow_html=True,
    )
    p_col1, p_col2 = st.columns([1, 1])
    with p_col1:
        st.button(primary_cta_text, type="primary", use_container_width=True,
                  on_click=navigate_to, args=primary_cta_key)
    with p_col2:
        st.button(secondary_cta_text, type="secondary", use_container_width=True,
                  on_click=navigate_to, args=secondary_cta_key)
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="command-hero-side"><div class="command-hero-testcount">'
        f"<strong>{escape(str(test_count))}</strong>"
        f"<small>{escape(test_label)}</small></div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def status_strip(items: list[tuple[str, str, str]]) -> None:
    html = "".join(
        f'<div class="status-strip-item">'
        f'<span class="status-strip-label">{escape(label)}</span>'
        f'<span class="status-strip-value">{escape(value)}</span>'
        f'<span class="status-strip-sub">{escape(sub)}</span></div>'
        for label, value, sub in items
    )
    st.markdown(f'<div class="status-strip">{html}</div>', unsafe_allow_html=True)


def health_cards(cards: list[tuple[str, str, str, str]]) -> None:
    html = ""
    for title, dot_class, primary, detail in cards:
        html += (
            f'<div class="health-card">'
            f'<div class="health-card-header">'
            f'<span class="health-dot health-dot-{dot_class}"></span>'
            f'<span class="health-card-title">{escape(title)}</span>'
            f'</div>'
            f'<div class="health-card-status">{escape(primary)}</div>'
            f'<div class="health-card-detail">{escape(detail)}</div>'
            f"</div>"
        )
    st.markdown(f'<div class="health-grid">{html}</div>', unsafe_allow_html=True)


def capability_card(
    name: str,
    category: str,
    status_badge_html: str,
    description: str,
    cta_text: str,
    cta_section: str,
    cta_key: str,
) -> None:
    st.markdown(
        f'<div class="cap-card">'
        f'<div class="cap-card-top">'
        f'<span class="cap-card-name">{escape(name)}</span>'
        f'<span class="cap-card-cat">{escape(category)}</span>'
        f"</div>"
        f'<div class="cap-card-desc">{escape(description)}</div>'
        f'<div class="cap-card-cta">{status_badge_html}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.button(cta_text, key=f"cc_{cta_key}", use_container_width=True,
              on_click=navigate_to, args=(cta_section, cta_key))


def pipeline_flow(stages: list[tuple[str, str]]) -> None:
    html = '<div class="pipeline-flow">'
    for i, (label, detail) in enumerate(stages):
        if i > 0:
            html += '<span class="pipeline-arrow">→</span>'
        html += f'<div class="pipeline-stage"><span class="pipeline-stage-label">{escape(label)}</span><span class="pipeline-stage-detail">{escape(detail)}</span></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def quick_action_grid(actions: list[tuple[str, str, tuple[str, str]]]) -> None:
    for label, kind, (section, key) in actions:
        btn_type = "primary" if kind == "primary" else "secondary"
        st.button(label, type=btn_type, key=f"qa_{key}", use_container_width=False,
                  on_click=navigate_to, args=(section, key))


def transparency_panel(items: list[tuple[str, str]]) -> None:
    html = '<div class="transparency-panel"><h3>' + escape(_t("transparency_title")) + '</h3><div class="transparency-grid">'
    for title, value in items:
        html += f'<div class="transparency-item"><strong>{escape(title)}:</strong> {escape(value)}</div>'
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)


def model_stage_timeline(stages: list[tuple[str, str, str, str]]) -> None:
    html = '<div class="timeline">'
    for name, subtitle, desc, stage_status in stages:
        cls = STATUS_CSS.get(stage_status, "badge-experimental")
        html += (
            f'<div class="timeline-item">'
            f'<div class="timeline-marker {cls}"></div>'
            f'<div class="timeline-content">'
            f"<h4>{escape(name)}</h4>"
            f"<p>{escape(subtitle)}</p>"
            f"<small>{escape(desc)}</small>"
            f"</div></div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
