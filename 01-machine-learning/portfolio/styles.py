import streamlit as st

CSS = """
<style>
/* ── Design Tokens ────────────────────────────────────────────── */
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
  --info: #2563eb;
  --info-soft: #eff6ff;

  /* Elevation */
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-md: 0 4px 14px rgba(15, 23, 42, 0.06);
  --shadow-lg: 0 8px 28px rgba(15, 23, 42, 0.1);
  --shadow-xl: 0 12px 40px rgba(15, 23, 42, 0.12);

  /* Radii */
  --radius-sm: 8px;
  --radius: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;

  /* Typography scale */
  --font-display: 2rem;
  --font-h1: 1.5rem;
  --font-h2: 1.25rem;
  --font-h3: 1rem;
  --font-body: 0.88rem;
  --font-small: 0.78rem;
  --font-xs: 0.7rem;

  /* Spacing scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  --space-12: 48px;

  /* Transitions */
  --ease-fast: 150ms ease;
  --ease-base: 200ms ease;
  --ease-slow: 300ms ease;
}

/* ── Base ──────────────────────────────────────────────────────── */
.stApp { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }
.block-container { max-width: 1320px; padding-top: 1.5rem; padding-bottom: 3rem; }
section[data-testid="stSidebar"] > div { background: var(--surface); border-right: 1px solid var(--border); }

/* ── Focus ring (global) ──────────────────────────────────────── */
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: var(--radius-sm); }

/* ── Hero ──────────────────────────────────────────────────────── */
.hero { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: var(--space-8) var(--space-8); box-shadow: var(--shadow-md); margin-bottom: var(--space-6); }
.hero-kicker { color: var(--accent); font-size: 0.72rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.4rem; }
.hero h1 { color: var(--text); font-size: var(--font-display); line-height: 1.15; letter-spacing: -0.03em; margin: var(--space-2) 0 var(--space-3); font-weight: 700; }
.hero p { color: var(--muted); max-width: 840px; line-height: 1.65; font-size: var(--font-body); margin: 0; }

/* ── Section headings ──────────────────────────────────────────── */
.section-heading { margin: var(--space-8) 0 var(--space-4); }
.section-heading h2 { font-size: var(--font-h2); color: var(--text); margin: 0 0 var(--space-1); font-weight: 600; letter-spacing: -0.02em; }
.section-heading p { color: var(--muted); font-size: var(--font-small); margin: 0; }

/* ── Card system ───────────────────────────────────────────────── */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.25rem; margin-bottom: 0.5rem; box-shadow: var(--shadow); transition: box-shadow var(--ease-base), border-color var(--ease-base), transform var(--ease-base); }
.card:hover { box-shadow: var(--shadow-md); border-color: var(--accent); transform: translateY(-2px); }
.card:focus-visible { box-shadow: 0 0 0 2px var(--accent); }
.card h3 { font-size: var(--font-h3); margin: 0 0 0.4rem; color: var(--text); font-weight: 600; }
.card p { color: var(--muted); line-height: 1.55; font-size: var(--font-body); margin: 0; }

.card-interactive { cursor: pointer; }
.card-interactive:active { transform: translateY(0); box-shadow: var(--shadow-xs); }

.card-primary { border-left: 3px solid var(--accent); }
.card-warning { border-left: 3px solid var(--warning); }
.card-danger { border-left: 3px solid var(--danger); }

/* ── Metric card ────────────────────────────────────────────────── */
.metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--space-4) var(--space-4); min-width: 0; transition: box-shadow var(--ease-fast), border-color var(--ease-fast); box-shadow: var(--shadow-xs); }
.metric-card:hover { box-shadow: var(--shadow-md); border-color: var(--accent); }
.metric-card:focus-visible { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-soft); }
.metric-card small { color: var(--muted); display: block; font-size: 0.72rem; font-weight: 650; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-card strong { color: var(--text); display: block; font-size: 1.35rem; margin: var(--space-1) 0; font-weight: 700; letter-spacing: -0.02em; }
.metric-card span { color: var(--muted); font-size: 0.75rem; line-height: 1.4; display: block; }

/* ── Badge system ──────────────────────────────────────────────── */
.badge { display: inline-flex; align-items: center; border-radius: 999px; padding: 0.2rem 0.65rem; font-size: 0.72rem; font-weight: 650; line-height: 1.4; transition: opacity var(--ease-fast), transform var(--ease-fast); }
.badge:hover { opacity: 0.85; }
.badge-verified { color: #15803d; background: #f0fdf4; }
.badge-available { color: #1e40af; background: #eff6ff; }
.badge-experimental { color: #b45309; background: #fffbeb; }
.badge-limited { color: #6b21a8; background: #faf5ff; }
.badge-archived { color: #64748b; background: #f1f5f9; }
.badge-roadmap { color: #a16207; background: #fefce8; }
.badge-unavailable { color: #b91c1c; background: #fef2f2; }
.badge-error { color: #b91c1c; background: #fef2f2; }

/* ── Grids ──────────────────────────────────────────────────────── */
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--space-3); margin: var(--space-3) 0 var(--space-6); }
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: var(--space-3); margin: var(--space-3) 0; }

/* ── Safe table ────────────────────────────────────────────────── */
.safe-table-wrap { width: 100%; overflow-x: auto; margin: 0.5rem 0 1rem; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow-xs); }
.safe-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; line-height: 1.4; }
.safe-table th { text-align: left; color: var(--muted); background: var(--alt); font-weight: 650; white-space: nowrap; padding: 0.55rem 0.7rem; border-bottom: 1px solid var(--border); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; position: sticky; top: 0; }
.safe-table td { padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--border); vertical-align: top; color: var(--text); max-width: 22rem; overflow-wrap: break-word; }
.safe-table tbody tr:last-child td { border-bottom: 0; }
.safe-table tbody tr:hover { background: var(--alt); }
.safe-table tbody tr:nth-child(even) { background: rgba(0,0,0,0.02); }
.safe-table tbody tr:nth-child(even):hover { background: var(--alt); }

/* ── Callout / Information panel ────────────────────────────────── */
.callout { background: var(--accent-soft); border: 1px solid #dde3ff; border-radius: var(--radius); padding: var(--space-4) var(--space-4); margin: var(--space-3) 0; }
.callout strong { color: var(--accent); display: block; margin-bottom: var(--space-1); font-size: 0.88rem; }
.callout p { color: var(--muted); margin: 0; font-size: 0.85rem; line-height: 1.5; }

.information-panel { background: var(--accent-soft); border: 1px solid #dde3ff; border-radius: var(--radius); padding: var(--space-3) var(--space-4); margin: var(--space-3) 0; }
.information-panel strong { color: var(--accent); display: block; font-size: 0.82rem; font-weight: 600; margin-bottom: 0.15rem; }
.information-panel p { color: var(--muted); margin: 0; font-size: 0.82rem; line-height: 1.5; }

/* ── Empty state ────────────────────────────────────────────────── */
.empty-state { background: var(--alt); border: 1px dashed var(--border); border-radius: var(--radius); padding: 2.5rem var(--space-6); text-align: center; margin: var(--space-3) 0; transition: border-color var(--ease-base); }
.empty-state:hover { border-color: var(--muted); }
.empty-state .empty-icon { font-size: 2rem; display: block; margin-bottom: var(--space-3); opacity: 0.5; }
.empty-state strong { color: var(--muted); display: block; font-size: var(--font-h3); margin-bottom: var(--space-1); font-weight: 600; }
.empty-state p { color: var(--muted); font-size: var(--font-body); margin: 0; max-width: 360px; margin: 0 auto; }

/* ── Skeleton loading ───────────────────────────────────────────── */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skeleton { background: linear-gradient(90deg, var(--alt) 25%, var(--border) 50%, var(--alt) 75%); background-size: 200% 100%; animation: shimmer 1.4s ease-in-out infinite; border-radius: var(--radius-sm); }
.skeleton-text { height: 14px; margin-bottom: var(--space-2); width: 80%; }
.skeleton-text.short { width: 50%; }
.skeleton-text.long { width: 95%; }
.skeleton-card { height: 100px; margin-bottom: var(--space-3); }
.skeleton-metric { height: 80px; }

/* ── Tooltip ────────────────────────────────────────────────────── */
.tooltip-trigger { position: relative; cursor: help; }
.tooltip-trigger .tooltip-content { visibility: hidden; opacity: 0; position: absolute; bottom: calc(100% + 8px); left: 50%; transform: translateX(-50%); background: var(--text); color: var(--bg); font-size: 0.72rem; padding: 0.4rem 0.7rem; border-radius: var(--radius-sm); white-space: nowrap; z-index: 100; transition: opacity var(--ease-fast), visibility var(--ease-fast); pointer-events: none; box-shadow: var(--shadow-lg); }
.tooltip-trigger .tooltip-content::after { content: ''; position: absolute; top: 100%; left: 50%; margin-left: -5px; border: 5px solid transparent; border-top-color: var(--text); }
.tooltip-trigger:hover .tooltip-content { visibility: visible; opacity: 1; }

/* ── Search experience ──────────────────────────────────────────── */
.search-page .search-result-card { overflow-wrap: anywhere; word-break: break-word; transition: box-shadow var(--ease-base), transform var(--ease-base); }
.search-page .search-result-card:hover { box-shadow: var(--shadow-md); transform: translateY(-1px); }
.search-page .search-result-card:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.search-page .search-timing { display: inline-flex; align-items: center; gap: var(--space-1); background: var(--alt); border-radius: 999px; padding: 0.15rem 0.6rem; font-size: 0.68rem; color: var(--muted); font-weight: 600; white-space: nowrap; }
.search-page input:focus, .search-page textarea:focus, .search-page button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
@media (max-width: 768px) {
  .search-page .search-result-card { padding: 0.85rem !important; }
}

/* ── Activity feed ──────────────────────────────────────────────── */
.activity-feed { display: flex; flex-direction: column; gap: var(--space-2); margin: var(--space-3) 0; }
.activity-entry { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3); background: var(--alt); border-radius: var(--radius); font-size: 0.85rem; transition: background var(--ease-fast); }
.activity-entry:hover { background: var(--border); }
.activity-cap { font-weight: 600; color: var(--text); min-width: 9rem; }
.activity-summary { color: var(--text); flex: 1; }
.activity-ago { color: var(--muted); font-size: 0.78rem; white-space: nowrap; }

/* ── Sidebar ────────────────────────────────────────────────────── */
.sidebar-brand { padding: var(--space-1) 0 var(--space-4); }
.sidebar-brand strong { color: var(--text); font-size: var(--font-h3); font-weight: 700; }
.sidebar-brand span { display: block; color: var(--muted); font-size: 0.75rem; margin-top: 0.15rem; }

section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.05rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] label { padding: 0.2rem 0.2rem; font-size: 0.85rem; transition: opacity var(--ease-fast); }
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { opacity: 0.8; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] { margin-bottom: var(--space-1); }
section[data-testid="stSidebar"] [data-testid="stRadio"] > label { color: var(--muted); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; }

/* ── Button system ──────────────────────────────────────────────── */
div.stButton > button {
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  font-weight: 600;
  width: 100%;
  cursor: pointer;
  transition: background var(--ease-fast), border-color var(--ease-fast), box-shadow var(--ease-fast), opacity var(--ease-fast), transform var(--ease-fast);
}
div.stButton > button:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);
  transform: translateY(-1px);
}
div.stButton > button:active {
  background: #3730a3;
  border-color: #3730a3;
  transform: translateY(0);
}
div.stButton > button:disabled {
  background: #94a3b8;
  border-color: #94a3b8;
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
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
  transform: translateY(-1px);
}
div.stButton > button[kind="secondary"]:active,
div.stButton > button[kind="tertiary"]:active {
  background: var(--border);
  transform: translateY(0);
}

/* Ghost buttons */
div.stButton > button[kind="secondary"][data-ghost="true"] {
  border-color: transparent;
  background: transparent;
}
div.stButton > button[kind="secondary"][data-ghost="true"]:hover {
  background: var(--alt);
  border-color: var(--border);
}

/* Destructive buttons */
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
  transform: translateY(-1px);
}
div.stButton > button[kind="destructive"]:active {
  transform: translateY(0);
}

/* Suggested query cards */
div.stButton > button[data-testid*="sug_"] {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.65rem 0.5rem;
  font-weight: 600;
  font-size: 0.82rem;
  line-height: 1.4;
  min-height: 48px;
  box-shadow: var(--shadow);
  transition: box-shadow var(--ease-base), border-color var(--ease-base), transform var(--ease-base);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-1);
}
div.stButton > button[data-testid*="sug_"]:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-lg);
  transform: translateY(-3px);
  background: var(--surface);
  color: var(--text);
}
div.stButton > button[data-testid*="sug_"]:active {
  transform: translateY(-1px);
  background: var(--alt);
}

/* Download buttons */
div.stDownloadButton > button {
  background: var(--accent);
  color: #ffffff;
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  font-weight: 600;
  transition: background var(--ease-fast), border-color var(--ease-fast), transform var(--ease-fast);
}
div.stDownloadButton > button:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
  transform: translateY(-1px);
}

/* ── Responsive ──────────────────────────────────────────────────── */
@media (max-width: 700px) {
  .hero { padding: var(--space-6); }
  .hero h1 { font-size: var(--font-h1); }
  .card-grid { grid-template-columns: 1fr; }
  .kpi-grid { grid-template-columns: 1fr 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important; }
}

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

/* ── Search Health Metrics ── */
.sh-metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin: 0.75rem 0 1.25rem; }
.sh-metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 0.85rem 1rem; transition: box-shadow 150ms ease; }
.sh-metric-card:hover { box-shadow: var(--shadow-md); }
.sh-metric-card.metric-pass { border-left: 3px solid var(--success); }
.sh-metric-card.metric-fail { border-left: 3px solid var(--danger); }
.sh-metric-card.metric-missing { border-left: 3px solid var(--warning); }
.sh-metric-card.metric-na { border-left: 3px solid var(--muted); }
.sh-metric-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.2rem; }
.sh-metric-title { font-size: 0.82rem; font-weight: 700; color: var(--text); }
.sh-status-badge { font-size: 0.6rem; font-weight: 700; padding: 0.1rem 0.4rem; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.04em; white-space: nowrap; }
.sh-pass { color: #15803d; background: #f0fdf4; }
.sh-fail { color: #b91c1c; background: #fef2f2; }
.sh-data-missing { color: #b45309; background: #fffbeb; }
.sh-not-evaluated { color: #64748b; background: #f1f5f9; }
.sh-skipped-missing-metric { color: #b45309; background: #fffbeb; }
.sh-metric-subtitle { font-size: 0.72rem; color: var(--muted); margin-bottom: 0.3rem; }
.sh-metric-value { font-size: 1.25rem; font-weight: 700; color: var(--text); margin-bottom: 0.2rem; }
.sh-metric-meta { font-size: 0.65rem; color: var(--muted); display: flex; gap: 0.5rem; flex-wrap: wrap; }
.sh-metric-direction { font-style: italic; }
.sh-metric-gate { opacity: 0.7; }
.sh-metric-note { font-size: 0.65rem; color: var(--warning); margin-top: 0.15rem; }
@media (prefers-color-scheme: dark) {
  .sh-pass { color: #4ade80; background: #123323; }
  .sh-fail { color: #f87171; background: #3b171b; }
  .sh-data-missing { color: #fbbf24; background: #392b12; }
  .sh-not-evaluated { color: #94a3b8; background: #172033; }
  .sh-skipped-missing-metric { color: #fbbf24; background: #392b12; }
  .sh-metric-card:hover { border-color: #4f5b7a; }
}

/* ── Evolution Pathway ──────────────────────────────────────────── */
@keyframes evol-glow {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
@keyframes evol-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(79, 70, 229, 0.3); }
  50% { box-shadow: 0 0 0 8px rgba(79, 70, 229, 0); }
}
.evol-container { margin: 1.5rem 0; padding: 1.5rem; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); }
.evol-container h3 { font-size: 1rem; margin: 0 0 1.25rem; color: var(--text); font-weight: 700; letter-spacing: -0.01em; }
.evol-pathway { display: flex; flex-wrap: wrap; gap: 0; align-items: stretch; position: relative; margin-bottom: 1rem; }
.evol-node { flex: 1; min-width: 110px; position: relative; padding: 0.75rem 0.5rem; text-align: center; transition: transform 200ms ease, filter 200ms ease; cursor: default; }
.evol-node:hover { transform: translateY(-4px); }
.evol-node:hover .evol-node-body { filter: brightness(1.1); }
.evol-node-dot { width: 18px; height: 18px; border-radius: 50%; margin: 0 auto 0.5rem; position: relative; z-index: 2; border: 2px solid var(--border); transition: box-shadow 300ms ease, border-color 300ms ease, transform 300ms ease; }
.evol-node-dot::after { content: ''; position: absolute; top: -4px; left: -4px; right: -4px; bottom: -4px; border-radius: 50%; opacity: 0; transition: opacity 500ms ease; }
.evol-node:hover .evol-node-dot { transform: scale(1.15); }
.evol-node:hover .evol-node-dot::after { opacity: 1; }
.evol-node-dot-baseline { background: #94a3b8; border-color: #94a3b8; }
.evol-node-dot-baseline::after { background: radial-gradient(circle, rgba(148,163,184,0.3) 0%, transparent 70%); }
.evol-node-dot-experimental { background: #f59e0b; border-color: #f59e0b; }
.evol-node-dot-experimental::after { background: radial-gradient(circle, rgba(245,158,11,0.3) 0%, transparent 70%); }
.evol-node-dot-available { background: #3b82f6; border-color: #3b82f6; }
.evol-node-dot-available::after { background: radial-gradient(circle, rgba(59,130,246,0.3) 0%, transparent 70%); }
.evol-node-dot-verified { background: #22c55e; border-color: #22c55e; animation: evol-glow 2s ease-in-out infinite; }
.evol-node-dot-verified::after { background: radial-gradient(circle, rgba(34,197,94,0.3) 0%, transparent 70%); }
.evol-node-label { font-size: 0.78rem; font-weight: 700; color: var(--text); margin-bottom: 0.1rem; }
.evol-node-name { font-size: 0.7rem; color: var(--muted); margin-bottom: 0.25rem; }
.evol-node-badge { display: inline-block; font-size: 0.6rem; font-weight: 650; padding: 0.1rem 0.4rem; border-radius: 999px; }
.evol-node-badge-baseline { color: #64748b; background: #f1f5f9; }
.evol-node-badge-experimental { color: #b45309; background: #fffbeb; }
.evol-node-badge-available { color: #1e40af; background: #eff6ff; }
.evol-node-badge-verified { color: #15803d; background: #f0fdf4; }
.evol-connector { flex: 0 0 24px; display: flex; align-items: center; justify-content: center; color: var(--muted); font-size: 0.9rem; }
.evol-connector-line { width: 100%; height: 2px; background: var(--border); position: relative; }
.evol-connector-line::after { content: ''; position: absolute; right: -2px; top: -4px; border: 5px solid transparent; border-left-color: var(--border); }
.evol-detail-panel { background: var(--alt); border: 1px solid var(--border); border-radius: var(--radius); padding: var(--space-4); margin-top: var(--space-4); }
.evol-detail-item { display: flex; gap: var(--space-3); padding: var(--space-2) 0; border-bottom: 1px solid var(--border); }
.evol-detail-item:last-child { border-bottom: 0; }
.evol-detail-version { font-weight: 700; color: var(--text); min-width: 60px; font-size: 0.85rem; }
.evol-detail-body { flex: 1; }
.evol-detail-name { font-weight: 600; color: var(--text); font-size: 0.82rem; }
.evol-detail-desc { color: var(--muted); font-size: 0.78rem; margin-top: 0.1rem; }
.evol-detail-tech { color: var(--muted); font-size: 0.72rem; margin-top: 0.05rem; }
@media (prefers-reduced-motion: reduce) {
  .evol-node { transition: none; } .evol-node-dot::after { transition: none; }
  .evol-node-dot-verified { animation: none; }
}
@media (max-width: 700px) {
  .evol-pathway { flex-direction: column; align-items: stretch; }
  .evol-node { min-width: 0; display: flex; align-items: center; gap: 0.75rem; text-align: left; padding: 0.6rem 0.5rem; }
  .evol-node-dot { margin: 0; flex-shrink: 0; }
  .evol-node-body { flex: 1; }
  .evol-node-label { margin-bottom: 0; }
  .evol-node-name { margin-bottom: 0; }
  .evol-connector { flex: 0 0 12px; transform: rotate(90deg); }
  .evol-connector-line { width: 2px; height: 16px; }
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0b1120; --surface: #111827; --alt: #172033; --text: #f1f5f9; --muted: #94a3b8;
    --border: #2b3548; --accent: #a5b4fc; --accent-hover: #c7d2fe; --accent-soft: #1e2550;
    --success: #4ade80; --success-soft: #123323; --warning: #fbbf24; --warning-soft: #392b12;
    --danger: #f87171; --danger-soft: #3b171b;
  }
  section[data-testid="stSidebar"] > div { background: var(--surface); }
  .callout { background: var(--accent-soft); border-color: #2e3a6e; }
  .information-panel { background: var(--accent-soft); border-color: #2e3a6e; }
  div.stButton > button:disabled { background: #4a5568; border-color: #4a5568; }
  div.stDownloadButton > button { background: var(--accent); border-color: var(--accent); }
  div.stDownloadButton > button:hover { background: var(--accent-hover); border-color: var(--accent-hover); }
  .command-hero { background: linear-gradient(135deg, var(--surface) 0%, #1a1f3a 100%); }
  .command-hero-badge-local { color: #93c5fd; background: #1e3a5f; border-color: #3b82f6; }
  .command-hero-badge-validated { color: #86efac; background: #14532d; border-color: #22c55e; }
  .command-hero-badge-architect { color: #d8b4fe; background: #3b0764; border-color: #a855f7; }
  .badge-verified { color: #4ade80; background: #123323; }
  .badge-available { color: #93c5fd; background: #1e3a5f; }
  .badge-experimental { color: #fde68a; background: #392b12; }
  .badge-limited { color: #d8b4fe; background: #3b0764; }
  .badge-archived { color: #94a3b8; background: #1e293b; }
  .badge-roadmap { color: #fde68a; background: #392b12; }
  .health-dot-ready { background: #4ade80; }
  .health-dot-partial { background: #fbbf24; }
  .health-dot-unavailable { background: #f87171; }
  .evol-node-dot-baseline { background: #64748b; border-color: #64748b; }
  .evol-node-dot-experimental { background: #f59e0b; border-color: #f59e0b; }
  .evol-node-dot-available { background: #60a5fa; border-color: #60a5fa; }
  .evol-node-dot-verified { background: #4ade80; border-color: #4ade80; }
  .evol-node-badge-baseline { color: #94a3b8; background: #1e293b; }
  .evol-node-badge-experimental { color: #fbbf24; background: #392b12; }
  .evol-node-badge-available { color: #93c5fd; background: #1e3a5f; }
  .evol-node-badge-verified { color: #4ade80; background: #123323; }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
