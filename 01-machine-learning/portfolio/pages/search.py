"""AI Search Workspace page — product-resource unified search."""

from __future__ import annotations

from html import escape

import streamlit as st

from portfolio.config import GITHUB_BRANCH, GITHUB_OWNER, GITHUB_REPO, REPOSITORY_ROOT
from portfolio.i18n import t
from portfolio.search_index import SearchDocument, get_search_index
from portfolio.experiment_store import repository_relative_path
from portfolio.search_service import SearchService, get_search_service
from portfolio.ui_components import hero_panel, section_heading


RESOURCE_TYPES = [
    "experiment",
    "notebook",
    "model",
    "document",
    "dataset",
    "source_code",
    "configuration",
]


def _ensure_session() -> None:
    st.session_state.setdefault("search_query", "")
    st.session_state.setdefault("recent_searches", [])
    st.session_state.setdefault("search_resource_type", "All")
    st.session_state.setdefault("search_run_token", 0)


def _navigate_to(doc: SearchDocument) -> None:
    """Route Open actions to real application pages with a stable resource id."""
    meta = doc.metadata or {}
    nav_target = meta.get("nav_target")
    nav_section = meta.get("nav_section")
    if not nav_target:
        defaults = {
            "experiment": ("section_portfolio", "nav_notebook_status"),
            "notebook": ("section_portfolio", "nav_notebook_status"),
            "model": ("section_model_ops", "nav_registry"),
            "document": ("section_portfolio", "nav_docs"),
            "dataset": ("section_data_science", "nav_data_workspace"),
        }
        nav_section, nav_target = defaults.get(doc.resource_type, (None, None))
    if nav_section and nav_target:
        st.session_state["nav_section"] = nav_section
        st.session_state[f"nav_page_{nav_section}"] = nav_target
        st.session_state["selected_resource_id"] = doc.resource_id
        st.session_state["selected_resource_type"] = doc.resource_type
        if meta.get("open_tab"):
            st.session_state["notebook_status_tab"] = meta["open_tab"]
        if meta.get("experiment_id"):
            st.session_state["selected_experiment_id"] = meta["experiment_id"]
        if meta.get("project_id"):
            st.session_state["selected_project_id"] = meta["project_id"]
        st.rerun()


def _github_link(doc: SearchDocument) -> str | None:
    meta = doc.metadata or {}
    if meta.get("github_url"):
        return str(meta["github_url"])
    rel = doc.repository_relative_path
    if not rel:
        return None
    return (
        f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{rel}"
    )


def _colab_link(doc: SearchDocument) -> str | None:
    if doc.resource_type != "notebook":
        return None
    meta = doc.metadata or {}
    if meta.get("colab_url"):
        return str(meta["colab_url"])
    rel = doc.repository_relative_path
    if not rel.endswith(".ipynb"):
        return None
    return (
        f"https://colab.research.google.com/github/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/blob/{GITHUB_BRANCH}/{rel}"
    )


def _download_bytes(doc: SearchDocument) -> tuple[bytes, str] | None:
    if doc.resource_type != "notebook":
        return None
    if not (doc.metadata or {}).get("downloadable"):
        return None
    rel = doc.repository_relative_path
    path = REPOSITORY_ROOT / rel
    if not path.is_file():
        return None
    try:
        return path.read_bytes(), path.name
    except OSError:
        return None


def _type_label(resource_type: str) -> str:
    key = f"rtype_{resource_type}"
    label = t(key)
    if label == key or not label:
        return resource_type.replace("_", " ").title()
    return label


def _render_index_status(service) -> None:
    stats = service.get_stats()
    type_counts = stats.get("resource_types") or {}
    bits = ", ".join(f"{_type_label(k)}: {v}" for k, v in type_counts.items() if v)
    last = stats.get("last_indexed") or "—"
    status = stats.get("index_status") or "—"
    st.caption(
        f"{t('index_resources_label')}: **{stats.get('total_documents', 0)}** · "
        f"{t('index_last_label')}: `{last}` · "
        f"{t('index_status_label')}: `{status}`"
    )
    if bits:
        st.caption(bits)


def _render_search_bar() -> tuple[str, bool, bool]:
    """Return (query, search_clicked, clear_clicked)."""
    if st.session_state.get("_search_pending_query") is not None:
        st.session_state["search_input"] = st.session_state.pop("_search_pending_query")
        st.session_state["search_query"] = st.session_state["search_input"]
        st.session_state["search_run_token"] = st.session_state.get("search_run_token", 0) + 1

    query = st.text_input(
        t("search_placeholder"),
        key="search_input",
        label_visibility="collapsed",
        placeholder=t("search_placeholder"),
    )
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        search_btn = st.button(t("search_btn"), type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button(t("clear_btn"), use_container_width=True)
    return (query or "").strip(), bool(search_btn), bool(clear_btn)


def _render_type_filter() -> str | None:
    options = ["All", "experiment", "notebook", "model", "document", "dataset", "source_code", "configuration"]
    current = st.session_state.get("search_resource_type", "All")
    if current not in options:
        current = "All"
    idx = options.index(current)
    selected = st.selectbox(
        t("filter_category"),
        options,
        index=idx,
        format_func=lambda x: t("all_categories") if x == "All" else _type_label(x),
        key="search_type_filter_widget",
    )
    st.session_state["search_resource_type"] = selected
    if st.button(t("reset_filters"), use_container_width=True, key="search_reset_filters"):
        st.session_state["search_resource_type"] = "All"
        st.session_state["search_type_filter_widget"] = "All"
        st.rerun()
    return None if selected == "All" else selected


def _render_recent_searches() -> None:
    recent = st.session_state.get("recent_searches", [])
    if not recent:
        st.caption(t("recent_searches_empty"))
        return
    with st.expander(t("recent_searches"), expanded=True):
        for i, query in enumerate(recent[:8]):
            if st.button(query, key=f"recent_btn_{i}_{hash(query) & 0xffff}", use_container_width=True):
                st.session_state["_search_pending_query"] = query
                st.rerun()


def _render_suggested_queries() -> None:
    st.caption(t("suggested_queries"))
    cols = st.columns(2)
    for i, query in enumerate([
        "sentiment", "duygu analizi", "churn", "müşteri kaybı",
        "housing", "konut tahmini", "random forest", "grid search",
        "notebook", "architecture",
    ]):
        with cols[i % 2]:
            if st.button(query, key=f"suggest_{i}", use_container_width=True):
                st.session_state["_search_pending_query"] = query
                st.rerun()


def _render_results(results: list, query: str) -> None:
    if not results:
        st.markdown(
            f'<div class="empty-state"><strong>{escape(t("no_results"))}</strong>'
            f'<p>{escape(t("no_results_desc", query=query))}</p></div>',
            unsafe_allow_html=True,
        )
        return

    st.caption(t("results_found", count=len(results)))
    from collections import Counter

    counts = Counter(r.document.resource_type for r in results)
    st.caption(" · ".join(f"{_type_label(k)}: {v}" for k, v in counts.items()))

    for rank, result in enumerate(results, start=1):
        doc = result.document
        rel = repository_relative_path(doc.repository_relative_path)
        score = f"{result.score:.3f}"
        reason = escape(result.match_reason or "")
        snippet = escape(result.snippet or doc.summary or "")
        title = escape(doc.title)
        type_label = escape(_type_label(doc.resource_type))

        st.markdown(
            f'<div class="card search-result-card" style="padding:1rem;margin-bottom:0.85rem;overflow-wrap:anywhere;">'
            f'<div style="display:flex;gap:0.75rem;align-items:flex-start;">'
            f'<div style="font-size:1.4rem;">{_type_icon(doc.resource_type)}</div>'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;flex-wrap:wrap;gap:0.5rem;align-items:baseline;">'
            f"<strong>{rank}. {title}</strong>"
            f'<span class="badge badge-available">{type_label}</span>'
            f'<span style="color:var(--muted);font-size:0.8rem;">score {escape(score)}</span>'
            f"</div>"
            f'<div style="color:var(--muted);font-size:0.8rem;margin:0.25rem 0;word-break:break-all;">'
            f"{escape(rel)}</div>"
            f'<div style="font-size:0.9rem;margin:0.35rem 0;">{snippet}</div>'
            f'<div style="font-size:0.75rem;color:var(--muted);">{t("match_reason")}: {reason}</div>'
            f"</div></div></div>",
            unsafe_allow_html=True,
        )
        _action_buttons(doc, rank)


def _type_icon(resource_type: str) -> str:
    return {
        "experiment": "🧪",
        "notebook": "📓",
        "model": "🧠",
        "document": "📄",
        "dataset": "🗂️",
        "source_code": "💻",
        "configuration": "⚙️",
    }.get(resource_type, "📄")


def _action_buttons(doc: SearchDocument, rank: int) -> None:
    actions = list(doc.actions or [])
    if not actions:
        return

    controls: list[tuple[str, str, str]] = []
    for action in actions:
        if action in {"open", "open_details", "open_registry", "open_metadata"}:
            label = {
                "open": t("action_open"),
                "open_details": t("action_open_details"),
                "open_registry": t("action_open_registry"),
                "open_metadata": t("action_open_metadata"),
            }.get(action, t("action_open"))
            controls.append((label, "navigate", action))
        elif action == "view_source":
            controls.append((t("action_view_source"), "navigate", action))
        elif action == "github":
            url = _github_link(doc)
            if url:
                controls.append((t("action_github"), "link", url))
        elif action == "colab":
            url = _colab_link(doc)
            if url:
                controls.append((t("action_colab"), "link", url))
        elif action == "download":
            payload = _download_bytes(doc)
            if payload:
                controls.append((t("action_download"), "download", ""))
        elif action == "copy_path":
            controls.append((t("action_copy_path"), "copy", doc.repository_relative_path))

    if not controls:
        return

    cols = st.columns(min(len(controls), 5))
    for i, (label, kind, payload) in enumerate(controls):
        with cols[i % len(cols)]:
            key = f"act_{rank}_{i}_{doc.resource_id}"
            if kind == "link":
                st.link_button(label, payload, use_container_width=True)
            elif kind == "download":
                data = _download_bytes(doc)
                if data:
                    raw, name = data
                    st.download_button(
                        label,
                        data=raw,
                        file_name=name,
                        mime="application/x-ipynb+json",
                        key=key,
                        use_container_width=True,
                    )
            elif kind == "copy":
                rel = repository_relative_path(payload)
                st.code(rel, language=None)
                st.caption(t("action_copy_path_hint"))
            elif kind == "navigate":
                if st.button(label, key=key, use_container_width=True):
                    _navigate_to(doc)


def render() -> None:
    """Render the AI Search Workspace page."""
    _ensure_session()
    service = get_search_service()
    get_search_index().ensure_ready()

    hero_panel(
        title=t("search_title"),
        subtitle=t("search_subtitle"),
        kicker=t("section_search"),
    )
    section_heading(t("search_workspace"))
    _render_index_status(service)

    st.markdown('<div class="search-page">', unsafe_allow_html=True)

    col_sidebar, col_main = st.columns([1, 4], gap="large")

    with col_sidebar:
        section_heading(t("filters"))
        type_filter = _render_type_filter()
        st.markdown("---")
        _render_recent_searches()
        st.markdown("---")
        _render_suggested_queries()

    with col_main:
        query, search_clicked, clear_clicked = _render_search_bar()

        if clear_clicked:
            st.session_state["search_query"] = ""
            st.session_state["search_input"] = ""
            st.session_state["search_run_token"] = st.session_state.get("search_run_token", 0) + 1
            query = ""
            st.rerun()

        active_query = query
        if search_clicked and query:
            active_query = query
            st.session_state["search_query"] = query
        elif query:
            st.session_state["search_query"] = query
        else:
            active_query = st.session_state.get("search_query", "")

        if active_query:
            st.session_state["recent_searches"] = SearchService.dedupe_recent(
                st.session_state.get("recent_searches", []),
                active_query,
                max_items=10,
            )
            results = service.search(
                active_query,
                top_k=20,
                resource_type=type_filter,
                fuzzy=True,
            )
            _render_results(results, active_query)
        else:
            st.info(t("search_empty_hint"))

    st.markdown("</div>", unsafe_allow_html=True)

    stats = get_search_index().get_stats()
    st.caption(t("index_stats", docs=stats['total_documents'], cats=len(stats['resource_types'])))


if __name__ == "__main__":
    render()