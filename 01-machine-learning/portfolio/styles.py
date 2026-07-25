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

.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; margin-bottom: 0.5rem; box-shadow: var(--shadow); }
.card h3 { font-size: 1rem; margin: 0 0 0.4rem; color: var(--text); font-weight: 600; }
.card p { color: var(--muted); line-height: 1.55; font-size: 0.88rem; margin: 0; }

.metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem 1.15rem; min-width: 0; }
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

.sidebar-brand { padding: 0.3rem 0 0.8rem; }
.sidebar-brand strong { color: var(--text); font-size: 1rem; font-weight: 700; }
.sidebar-brand span { display: block; color: var(--muted); font-size: 0.75rem; margin-top: 0.15rem; }

section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.05rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] label { padding: 0.15rem 0.1rem; font-size: 0.85rem; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] { margin-bottom: 0.3rem; }
section[data-testid="stSidebar"] [data-testid="stRadio"] > label { color: var(--muted); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; }

div.stButton > button { border-radius: var(--radius-sm); border-color: var(--accent); color: var(--accent); font-weight: 600; width: 100%; }
div.stButton > button:hover { border-color: var(--accent-hover); color: var(--accent-hover); background: var(--accent-soft); }

@media (max-width: 700px) {
  .hero { padding: 1.25rem; }
  .hero h1 { font-size: 1.5rem; }
  .card-grid { grid-template-columns: 1fr; }
  .kpi-grid { grid-template-columns: 1fr 1fr; }
}

@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; transition: none !important; } }

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0b1120; --surface: #111827; --alt: #172033; --text: #f1f5f9; --muted: #94a3b8;
    --border: #2b3548; --accent: #a5b4fc; --accent-hover: #c7d2fe; --accent-soft: #1e2550;
    --success: #4ade80; --success-soft: #123323; --warning: #fbbf24; --warning-soft: #392b12;
    --danger: #f87171; --danger-soft: #3b171b;
  }
  section[data-testid="stSidebar"] > div { background: var(--surface); }
  .callout { background: var(--accent-soft); border-color: #2e3a6e; }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
