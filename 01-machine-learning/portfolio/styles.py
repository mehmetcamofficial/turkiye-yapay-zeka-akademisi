import streamlit as st

CSS = """
<style>
:root {
  --bg: #f5f6fa;
  --surface: #ffffff;
  --alt: #f0f2f6;
  --text: #0f172a;
  --muted: #64748b;
  --border: #e2e8f0;
  --accent: #4f46e5;
  --accent-hover: #4338ca;
  --accent-soft: #eef2ff;
  --success: #15803d;
  --success-soft: #f0fdf4;
  --warning: #b45309;
  --warning-soft: #fffbeb;
  --danger: #b91c1c;
  --danger-soft: #fef2f2;
  --shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 14px rgba(15, 23, 42, 0.06);
  --radius-sm: 8px;
  --radius: 12px;
  --radius-lg: 16px;
}
.stApp { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }
.block-container { max-width: 1320px; padding-top: 1.5rem; padding-bottom: 3rem; }
section[data-testid="stSidebar"] > div { background: var(--surface); border-right: 1px solid var(--border); }

.hero { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 2rem 2rem; box-shadow: var(--shadow-md); margin-bottom: 1.5rem; }
.hero-kicker { color: var(--accent); font-size: 0.72rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.4rem; }
.hero h1 { color: var(--text); font-size: 2rem; line-height: 1.2; letter-spacing: -0.03em; margin: 0.4rem 0 0.6rem; font-weight: 700; }
.hero p { color: var(--muted); max-width: 840px; line-height: 1.7; font-size: 0.95rem; margin: 0; }

.section-heading { margin: 1.8rem 0 1rem; }
.section-heading h2 { font-size: 1.25rem; color: var(--text); margin: 0 0 0.25rem; font-weight: 600; }
.section-heading p { color: var(--muted); font-size: 0.88rem; margin: 0; }

.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; margin-bottom: 0.5rem; box-shadow: var(--shadow); transition: box-shadow 180ms ease, border-color 180ms ease, transform 180ms ease; }
.card:hover { box-shadow: var(--shadow-md); border-color: var(--accent); transform: translateY(-2px); }
.card h3 { font-size: 1rem; margin: 0 0 0.4rem; color: var(--text); font-weight: 600; }
.card p { color: var(--muted); line-height: 1.55; font-size: 0.88rem; margin: 0; }

.metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.15rem; min-width: 0; transition: box-shadow 150ms ease, border-color 150ms ease; }
.metric-card:hover { box-shadow: var(--shadow-md); border-color: var(--accent); }
.metric-card small { color: var(--muted); display: block; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-card strong { color: var(--text); display: block; font-size: 1.35rem; margin: 0.25rem 0; font-weight: 700; }
.metric-card span { color: var(--muted); font-size: 0.75rem; line-height: 1.4; display: block; }

.badge { display: inline-flex; align-items: center; border-radius: 999px; padding: 0.2rem 0.65rem; font-size: 0.72rem; font-weight: 650; line-height: 1.4; }
.badge-verified { color: #15803d; background: #f0fdf4; }
.badge-available { color: #1e40af; background: #eff6ff; }
.badge-experimental { color: #b45309; background: #fffbeb; }
.badge-limited { color: #6b21a8; background: #faf5ff; }
.badge-archived { color: #64748b; background: #f1f5f9; }
.badge-roadmap { color: #a16207; background: #fefce8; }
.badge-unavailable { color: #b91c1c; background: #fef2f2; }
.badge-error { color: #b91c1c; background: #fef2f2; }

.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.75rem; margin: 0.75rem 0 1.25rem; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.75rem; margin: 0.75rem 0; }

.safe-table-wrap { width: 100%; overflow-x: auto; margin: 0.5rem 0 1rem; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); }
.safe-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; line-height: 1.4; }
.safe-table th { text-align: left; color: var(--muted); background: var(--alt); font-weight: 650; white-space: nowrap; padding: 0.55rem 0.7rem; border-bottom: 1px solid var(--border); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; }
.safe-table td { padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--border); vertical-align: top; color: var(--text); max-width: 22rem; overflow-wrap: break-word; }
.safe-table tbody tr:last-child td { border-bottom: 0; }
.safe-table tbody tr:hover { background: var(--alt); }

.callout { background: var(--accent-soft); border: 1px solid #dde3ff; border-radius: var(--radius); padding: 1rem 1.15rem; margin: 0.75rem 0; }
.callout strong { color: var(--accent); display: block; margin-bottom: 0.25rem; font-size: 0.88rem; }
.callout p { color: var(--muted); margin: 0; font-size: 0.85rem; line-height: 1.5; }

.empty-state { background: var(--alt); border: 1px dashed var(--border); border-radius: var(--radius); padding: 2rem; text-align: center; margin: 0.75rem 0; }
.empty-state strong { color: var(--muted); display: block; margin-bottom: 0.3rem; }
.empty-state p { color: var(--muted); font-size: 0.85rem; margin: 0; }

.activity-feed { display: flex; flex-direction: column; gap: 0.4rem; margin: 0.75rem 0; }
.activity-entry { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0.75rem; background: var(--alt); border-radius: var(--radius); font-size: 0.85rem; }
.activity-cap { font-weight: 600; color: var(--text); min-width: 9rem; }
.activity-summary { color: var(--text); flex: 1; }
.activity-ago { color: var(--muted); font-size: 0.78rem; white-space: nowrap; }

.sidebar-brand { padding: 0.3rem 0 0.8rem; }
.sidebar-brand strong { color: var(--text); font-size: 1rem; font-weight: 700; }
.sidebar-brand span { display: block; color: var(--muted); font-size: 0.75rem; margin-top: 0.15rem; }

section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.05rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] label { padding: 0.15rem 0.1rem; font-size: 0.85rem; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] { margin-bottom: 0.3rem; }
section[data-testid="stSidebar"] [data-testid="stRadio"] > label { color: var(--muted); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; }

/* Primary buttons - filled professional indigo */
div.stButton > button {
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  font-weight: 600;
  width: 100%;
  cursor: pointer;
  transition: background 150ms ease, border-color 150ms ease, box-shadow 150ms ease, opacity 150ms ease;
}
div.stButton > button:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
}
div.stButton > button:active {
  background: #3730a3;
  border-color: #3730a3;
}
div.stButton > button:disabled {
  background: #94a3b8;
  border-color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.6;
}
div.stButton > button[aria-busy="true"] {
  opacity: 0.7;
  cursor: wait;
}

/* Secondary buttons - muted outline */
div.stButton > button[kind="secondary"],
div.stButton > button[kind="tertiary"] {
  background: transparent;
  color: var(--muted);
  border: 1px solid var(--border);
}
div.stButton > button[kind="secondary"]:hover,
div.stButton > button[kind="tertiary"]:hover {
  color: var(--text);
  border-color: var(--muted);
  background: var(--alt);
  box-shadow: none;
}
div.stButton > button[kind="secondary"]:active,
div.stButton > button[kind="tertiary"]:active {
  background: var(--border);
}

/* Destructive buttons - red reserved for errors */
div.stButton > button[kind="destructive"],
div.stButton > button[data-testid="baseButton-destructive"] {
  background: var(--danger);
  color: #ffffff;
  border: 1px solid var(--danger);
}
div.stButton > button[kind="destructive"]:hover,
div.stButton > button[data-testid="baseButton-destructive"]:hover {
  background: #991b1b;
  border-color: #991b1b;
  box-shadow: 0 2px 8px rgba(185, 28, 28, 0.3);
}

/* Download buttons match primary */
div.stDownloadButton > button {
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  font-weight: 600;
  transition: background 150ms ease, border-color 150ms ease;
}
div.stDownloadButton > button:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}

@media (max-width: 700px) {
  .hero { padding: 1.25rem; }
  .hero h1 { font-size: 1.5rem; }
  .card-grid { grid-template-columns: 1fr; }
  .kpi-grid { grid-template-columns: 1fr 1fr; }
}

@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; transition: none !important; } }

/* ── Command Center ── */
.command-hero { background: linear-gradient(135deg, var(--surface) 0%, var(--accent-soft) 100%); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.75rem 2rem; box-shadow: var(--shadow-md); margin-bottom: 1.25rem; display: flex; flex-wrap: wrap; gap: 1.5rem; align-items: flex-start; }
.command-hero-main { flex: 1; min-width: 280px; }
.command-hero-side { flex: 0 0 auto; min-width: 160px; }
.command-hero-eyebrow { color: var(--accent); font-size: 0.7rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.25rem; }
.command-hero h1 { color: var(--text); font-size: 1.65rem; line-height: 1.25; letter-spacing: -0.03em; margin: 0.15rem 0 0.35rem; font-weight: 700; }
.command-hero p { color: var(--muted); max-width: 640px; line-height: 1.55; font-size: 0.88rem; margin: 0 0 0.6rem; }
.command-hero-badges { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 0.5rem; }
.command-hero-badge { display: inline-flex; align-items: center; border-radius: 999px; padding: 0.15rem 0.55rem; font-size: 0.65rem; font-weight: 650; line-height: 1.4; border: 1px solid; }
.command-hero-badge-local { color: #1e40af; background: #eff6ff; border-color: #bfdbfe; }
.command-hero-badge-validated { color: #15803d; background: #f0fdf4; border-color: #bbf7d0; }
.command-hero-badge-architect { color: #6b21a8; background: #faf5ff; border-color: #e9d5ff; }
.command-hero-actions { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.command-hero-actions .stButton > button { padding: 0.35rem 1rem; font-size: 0.82rem; width: auto; }
.command-hero-testcount { background: var(--alt); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.7rem 1rem; text-align: center; }
.command-hero-testcount strong { display: block; font-size: 1.5rem; color: var(--success); font-weight: 700; }
.command-hero-testcount small { display: block; color: var(--muted); font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.1rem; }
@media (max-width: 700px) {
  .command-hero { padding: 1.25rem; flex-direction: column; }
  .command-hero h1 { font-size: 1.35rem; }
  .command-hero-side { width: 100%; }
  .command-hero-testcount { display: inline-block; }
}

.status-strip { display: flex; flex-wrap: wrap; gap: 0.6rem; margin: 0 0 1.25rem; }
.status-strip-item { flex: 1; min-width: 120px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.7rem 0.9rem; transition: box-shadow 150ms ease; }
.status-strip-item:hover { box-shadow: var(--shadow); }
.status-strip-label { display: block; color: var(--muted); font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.15rem; }
.status-strip-value { display: block; color: var(--text); font-size: 1.1rem; font-weight: 700; }
.status-strip-sub { display: block; color: var(--muted); font-size: 0.7rem; margin-top: 0.05rem; }

.health-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.65rem; margin: 0.5rem 0 1.25rem; }
.health-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.85rem 1rem; transition: box-shadow 150ms ease, border-color 150ms ease; }
.health-card:hover { box-shadow: var(--shadow-md); border-color: var(--accent); }
.health-card-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.3rem; }
.health-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.health-dot-ready { background: var(--success); }
.health-dot-partial { background: var(--warning); }
.health-dot-unavailable { background: var(--danger); }
.health-card-title { font-size: 0.8rem; font-weight: 600; color: var(--text); }
.health-card-status { font-size: 0.75rem; color: var(--muted); line-height: 1.4; }
.health-card-detail { margin-top: 0.3rem; font-size: 0.7rem; color: var(--muted); line-height: 1.3; }

.capability-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 0.65rem; margin: 0.5rem 0 1.25rem; }
.cap-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.9rem 1rem; display: flex; flex-direction: column; transition: box-shadow 150ms ease, border-color 150ms ease; }
.cap-card:hover { box-shadow: var(--shadow-md); border-color: var(--accent); }
.cap-card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.25rem; }
.cap-card-name { font-size: 0.9rem; font-weight: 600; color: var(--text); }
.cap-card-cat { font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: var(--accent); padding: 0.1rem 0.4rem; background: var(--accent-soft); border-radius: 4px; }
.cap-card-desc { font-size: 0.75rem; color: var(--muted); line-height: 1.45; flex: 1; margin-bottom: 0.5rem; }
.cap-card-cta { margin-top: auto; }

.pipeline-flow { display: flex; flex-wrap: wrap; gap: 0.35rem; align-items: center; margin: 0.5rem 0 1.25rem; padding: 0.75rem 1rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.pipeline-stage { background: var(--alt); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.45rem 0.7rem; min-width: 100px; text-align: center; flex-shrink: 0; }
.pipeline-stage-label { display: block; font-size: 0.72rem; font-weight: 700; color: var(--text); }
.pipeline-stage-detail { display: block; font-size: 0.62rem; color: var(--muted); margin-top: 0.05rem; }
.pipeline-arrow { color: var(--muted); font-size: 1rem; font-weight: 300; flex-shrink: 0; padding: 0 0.1rem; }

.arch-cards { display: flex; flex-wrap: wrap; align-items: center; gap: 0; margin: 0.75rem 0 1.25rem; }
.arch-card { display: flex; align-items: center; gap: 0.65rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.65rem 0.85rem; min-width: 120px; flex: 1 0 auto; }
.arch-card-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.arch-card-body { display: flex; flex-direction: column; }
.arch-card-title { font-size: 0.78rem; font-weight: 600; color: var(--text); white-space: nowrap; }
.arch-card-status { font-size: 0.62rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.arch-connector { display: flex; align-items: center; justify-content: center; width: 1.5rem; flex-shrink: 0; }
.arch-connector-arrow { color: var(--muted); font-size: 0.9rem; }

@media (max-width: 700px) {
  .arch-cards { flex-direction: column; align-items: stretch; }
  .arch-connector { transform: rotate(90deg); width: auto; height: 0.75rem; }
  .arch-card { min-width: 0; }
  .pipeline-flow { gap: 0.25rem; padding: 0.5rem; }
  .pipeline-stage { min-width: 70px; padding: 0.35rem 0.5rem; }
  .pipeline-arrow { display: none; }
  .pipeline-stage::after { content: " →"; color: var(--muted); }
  .pipeline-stage:last-child::after { content: ""; }
}

.search-snapshot { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.15rem; margin: 0.5rem 0 1.25rem; display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; }
.search-snapshot-vis { display: flex; flex-wrap: wrap; align-items: center; gap: 0.3rem; flex: 1; min-width: 200px; }
.search-snapshot-step { display: flex; align-items: center; gap: 0.25rem; }
.search-snapshot-step-label { font-size: 0.65rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.search-snapshot-step-value { font-size: 0.75rem; color: var(--text); white-space: nowrap; }
.search-snapshot-info { flex: 0 0 auto; display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; }
.search-snapshot-stat { font-size: 0.75rem; color: var(--muted); }
.search-snapshot-stat strong { color: var(--text); }

.data-artifact-panels { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin: 0.5rem 0 1.25rem; }
@media (max-width: 700px) { .data-artifact-panels { grid-template-columns: 1fr; } }
.data-panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.9rem 1rem; }
.data-panel h3 { font-size: 0.82rem; font-weight: 600; color: var(--text); margin: 0 0 0.4rem; }
.data-panel-list { list-style: none; padding: 0; margin: 0; }
.data-panel-list li { font-size: 0.75rem; color: var(--muted); padding: 0.2rem 0; display: flex; justify-content: space-between; }
.data-panel-list li strong { color: var(--text); }
.data-panel-cta { margin-top: 0.5rem; }

.quick-action-grid { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.5rem 0 1.25rem; }
.quick-action-grid .stButton > button { font-size: 0.78rem; padding: 0.3rem 0.8rem; width: auto; white-space: nowrap; }
.quick-action-grid .stButton > button[kind="primary"] { background: var(--accent); color: #fff; border-color: var(--accent); }

.transparency-panel { background: var(--alt); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.85rem 1rem; margin: 0.5rem 0; }
.transparency-panel h3 { font-size: 0.82rem; font-weight: 600; color: var(--muted); margin: 0 0 0.4rem; }
.transparency-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.4rem; }
.transparency-item { font-size: 0.72rem; color: var(--muted); line-height: 1.4; }
.transparency-item strong { color: var(--text); }

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0b1120; --surface: #111827; --alt: #172033; --text: #f1f5f9; --muted: #94a3b8;
    --border: #2b3548; --accent: #a5b4fc; --accent-hover: #c7d2fe; --accent-soft: #1e2550;
    --success: #4ade80; --success-soft: #123323; --warning: #fbbf24; --warning-soft: #392b12;
    --danger: #f87171; --danger-soft: #3b171b;
  }
  section[data-testid="stSidebar"] > div { background: var(--surface); }
  .callout { background: var(--accent-soft); border-color: #2e3a6e; }
  div.stButton > button:disabled { background: #4a5568; border-color: #4a5568; }
  div.stDownloadButton > button { background: var(--accent); border-color: var(--accent); }
  div.stDownloadButton > button:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
  .command-hero { background: linear-gradient(135deg, var(--surface) 0%, #1a1f3a 100%); }
  .command-hero-badge-local { color: #93c5fd; background: #1e3a5f; border-color: #3b82f6; }
  .command-hero-badge-validated { color: #86efac; background: #14532d; border-color: #22c55e; }
  .command-hero-badge-architect { color: #d8b4fe; background: #3b0764; border-color: #a855f7; }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
