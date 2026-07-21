"""Restrained enterprise design system for the portfolio UI."""

import streamlit as st

CSS = """
<style>
:root { --bg:#f7f8fc; --surface:#fff; --alt:#f8fafc; --text:#0f172a;
--muted:#64748b; --border:#e2e8f0; --accent:#4f46e5; --accent-hover:#4338ca; --accent-soft:#eef2ff;
--success:#15803d; --success-soft:#f0fdf4; --warning:#b45309;
--warning-soft:#fffbeb; --danger:#b91c1c; --danger-soft:#fef2f2; }
.stApp { background:var(--bg); color:var(--text); }
.block-container { max-width:1360px; padding-top:1.6rem; padding-bottom:3rem; }
section[data-testid="stSidebar"] > div { background:#fff; border-right:1px solid var(--border); }
.portfolio-hero { background:#fff; border:1px solid var(--border); border-radius:16px;
padding:1.4rem 1.65rem; box-shadow:0 6px 22px rgba(15,23,42,.05); margin-bottom:1.1rem; }
.portfolio-kicker { color:var(--accent); font-size:.76rem; font-weight:800;
letter-spacing:.12em; text-transform:uppercase; }
.portfolio-hero h1 { color:var(--text); font-size:2.25rem; line-height:1.15;
letter-spacing:-.035em; margin:.55rem 0 .7rem; }
.portfolio-hero p { color:var(--muted); max-width:900px; line-height:1.7; margin:0; }
.section-heading { margin:1.6rem 0 .8rem; }
.section-heading h2 { font-size:1.35rem; color:var(--text); margin:0 0 .3rem; }
.section-heading p { color:var(--muted); margin:0; }
.project-card,.info-panel,.metric-panel,.empty-panel,.prediction-card { background:#fff;
border:1px solid var(--border); border-radius:14px; padding:1.15rem; margin:.35rem 0;
box-shadow:0 3px 14px rgba(15,23,42,.035); }
.project-card { min-height:290px; display:flex; flex-direction:column; }
.project-card h3 { font-size:1.05rem; margin:.5rem 0 .4rem; color:var(--text); }
.project-card p,.info-panel p { color:var(--muted); line-height:1.55; font-size:.9rem; }
.status { display:inline-block; border-radius:999px; padding:.25rem .6rem;
font-size:.72rem; font-weight:750; }
.status-complete { color:var(--success); background:var(--success-soft); }
.status-progress,.status-planned { color:var(--warning); background:var(--warning-soft); }
.status-empty { color:var(--muted); background:var(--alt); }
.card-meta { display:grid; grid-template-columns:1fr 1fr; gap:.55rem; margin-top:.8rem; }
.card-meta div { background:var(--alt); border-radius:9px; padding:.6rem; }
.card-meta small { color:var(--muted); display:block; }.card-meta strong { font-size:.86rem; }
.sidebar-brand { padding:.45rem 0 1rem; }.sidebar-brand strong { color:var(--text); font-size:1.05rem; }
.sidebar-brand span { display:block; color:var(--muted); font-size:.78rem; margin-top:.2rem; }
.capability-tags { display:flex; flex-wrap:wrap; gap:.45rem; margin:.65rem 0 1rem; }
.capability-tags span { background:var(--accent-soft); color:var(--accent); border:1px solid #dfe3ff;
border-radius:999px; padding:.34rem .68rem; font-size:.76rem; font-weight:700; }
.safe-table-wrap { width:100%; overflow-x:auto; margin:.45rem 0 1rem; border:1px solid var(--border); border-radius:12px; background:var(--surface); }
.safe-table { width:100%; border-collapse:collapse; font-size:.82rem; line-height:1.35; }
.safe-table th { text-align:left; color:var(--muted); background:var(--alt); font-weight:750; white-space:nowrap; }
.safe-table th,.safe-table td { padding:.56rem .68rem; border-bottom:1px solid var(--border); vertical-align:top; }
.safe-table tbody tr:last-child td { border-bottom:0; }
.safe-table td { color:var(--text); max-width:28rem; overflow-wrap:anywhere; }
.safe-table tbody tr:hover { background:var(--alt); }
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(155px,1fr)); gap:.7rem; margin:.45rem 0 1.15rem; }
.kpi-card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:.85rem .9rem; min-width:0; }
.kpi-card small,.kpi-card span { color:var(--muted); display:block; overflow-wrap:anywhere; }
.kpi-card strong { color:var(--text); display:block; font-size:1.15rem; margin:.28rem 0; overflow-wrap:anywhere; }
.kpi-card span { font-size:.72rem; line-height:1.35; }
section[data-testid="stSidebar"] div[role="radiogroup"] { gap:.05rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] label { padding:.2rem .15rem; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] { margin-bottom:.35rem; }
section[data-testid="stSidebar"] [data-testid="stRadio"] > label { color:var(--muted); font-size:.72rem; font-weight:750; text-transform:uppercase; letter-spacing:.08em; }
div.stButton > button { border-radius:9px; border-color:var(--accent); color:var(--accent); font-weight:650; width:100%; }
div.stButton > button:hover { border-color:var(--accent-hover); color:var(--accent-hover); background:var(--accent-soft); }
@media(max-width:700px){.portfolio-hero{padding:1.15rem}.portfolio-hero h1{font-size:1.75rem}.card-meta{grid-template-columns:1fr}.project-card{min-height:auto}}
@media(prefers-color-scheme:dark){:root{--bg:#0b1120;--surface:#111827;--alt:#172033;--text:#f1f5f9;--muted:#a8b3c5;--border:#2b3548;--accent:#a5b4fc;--accent-hover:#c7d2fe;--accent-soft:#20294a;--success:#4ade80;--success-soft:#123323;--warning:#fbbf24;--warning-soft:#392b12;--danger:#f87171;--danger-soft:#3b171b}section[data-testid="stSidebar"] > div{background:var(--surface)}}
</style>
"""


def apply_styles() -> None:
    """Inject the portfolio design tokens once per rerun."""
    st.markdown(CSS, unsafe_allow_html=True)
