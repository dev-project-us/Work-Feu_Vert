"""
app.py — Feu Vert Annecy · Live Dashboard
────────────────────────────────────────────────────────────────────────────
Renders the custom index.html design, populated with live engine data.

Strategy:
  • st.components.v1.html() creates an isolated iframe → full CSS control,
    zero conflict with Streamlit's own styles.
  • All HTML/CSS is generated in Python; engine/ modules stay pure data.
  • Auto-height JS resizes the iframe to fit content automatically.
"""
from __future__ import annotations

import html as _html
import streamlit as st

from engine import defects, families, global_stats, ratios, tires, vendor_ratios
from engine.utils import QUARTERLY_DIR

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Feu Vert Annecy",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Remove Streamlit chrome + style sidebar to match dark theme
st.markdown(
    "<style>"
    "[data-testid='stHeader']{display:none !important;} "
    "#MainMenu{visibility:hidden !important;} "
    "footer{visibility:hidden !important;} "
    ".block-container{padding:0 !important;} "
    ".stApp{background:#111827;} "
    "[data-testid='stSidebar']{background:#111827 !important;border-right:1px solid #1f2937 !important;} "
    "[data-testid='stSidebar'] .stButton button{"
    "  border-radius:6px !important;font-size:13px !important;font-weight:500 !important;"
    "  border:1px solid #1f2937 !important;background:#1f2937 !important;color:#9ca3af !important;"
    "  text-align:left !important;padding:8px 12px !important;transition:background .15s;} "
    "[data-testid='stSidebar'] .stButton button:hover{background:#374151 !important;color:#f9fafb !important;} "
    "[data-testid='stSidebar'] .stButton button[kind='primary']{"
    "  background:#78BE20 !important;color:#111827 !important;border-color:#78BE20 !important;font-weight:600 !important;} "
    "[data-testid='stSidebar'] hr{border-color:#1f2937;} "
    ".stAlert{background-color:oklch(25% 0.05 85) !important;border:1px solid oklch(40% 0.1 85) !important;color:oklch(95% 0.02 85) !important;}"
    ".stExpander{background-color:oklch(20% 0.02 240) !important;border:1px solid oklch(30% 0.02 240) !important;}"
    "</style>",
    unsafe_allow_html=True,
)


# ════════════════════════════════════════════════════════════════════════════
# CSS — verbatim from index.html  +  Google Fonts
# ════════════════════════════════════════════════════════════════════════════
_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:               oklch(15% 0.015 240);
  --surface:          oklch(20% 0.012 240);
  --surface-elevated: oklch(24% 0.010 240);
  --border:           oklch(30% 0.010 240);
  --border-subtle:    oklch(22% 0.010 240);
  --fg:               oklch(95% 0.005 240);
  --muted:            oklch(65% 0.010 240);
  --accent:           oklch(72% 0.20 130);
  --accent-dim:       oklch(40% 0.12 130);
  --positive:         oklch(72% 0.20 130);
  --negative:         oklch(65% 0.20 25);
  --warning:          oklch(75% 0.18 85);
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, Menlo, monospace;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: var(--font-body); background: var(--bg); color: var(--fg);
       line-height: 1.5; font-size: 14px; }
.dashboard { display: grid; grid-template-columns: 1fr 320px;
             grid-template-rows: auto auto 1fr; gap: 16px;
             padding: 24px; max-width: 1600px; margin: 0 auto; }
/* HEADER */
.header { grid-column: 1 / -1; display: flex; align-items: center;
          justify-content: space-between; padding-bottom: 16px;
          border-bottom: 1px solid var(--border); }
.header-left { display: flex; align-items: center; gap: 16px; }
.logo { width: 40px; height: 40px; background: var(--accent); border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 18px; color: var(--bg); }
.header-title  { font-size: 20px; font-weight: 600; letter-spacing: -0.02em; }
.header-subtitle { font-size: 13px; color: var(--muted); font-family: var(--font-mono); }
.week-badge { background: var(--surface); padding: 8px 16px; border-radius: 6px;
              border: 1px solid var(--border); font-family: var(--font-mono); font-size: 13px; }
/* KPI STRIP */
.kpi-strip { grid-column: 1 / -1; display: grid;
             grid-template-columns: repeat(6, 1fr); gap: 12px; }
.kpi-card { background: var(--surface); border: 1px solid var(--border);
            border-radius: 6px; padding: 16px;
            display: flex; flex-direction: column; gap: 6px; }
.kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: .08em;
             color: var(--muted); font-weight: 500; }
.kpi-sublabel { font-size: 10px; color: var(--muted); font-family: var(--font-mono); }
.kpi-value-row { display: flex; align-items: baseline; gap: 10px; }
.kpi-value { font-family: var(--font-mono); font-size: 24px; font-weight: 600;
             font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
.kpi-delta { font-family: var(--font-mono); font-size: 11px; font-variant-numeric: tabular-nums; }
.kpi-delta.pos  { color: var(--positive); }
.kpi-delta.neg  { color: var(--negative); }
.kpi-delta.warn { color: var(--warning);  }
.kpi-sparkline { height: 20px; display: flex; align-items: flex-end; gap: 2px; margin-top: 2px; }
.spark-bar     { flex: 1; background: var(--accent-dim); border-radius: 1px; }
.spark-bar.cur { background: var(--accent); }
/* LAYOUT */
.main-content { display: flex; flex-direction: column; gap: 16px; }
.card { background: var(--surface); border: 1px solid var(--border);
        border-radius: 6px; padding: 16px; }
.card-header { display: flex; justify-content: space-between; align-items: center;
               margin-bottom: 14px; }
.card-title { font-size: 13px; font-weight: 600; text-transform: uppercase;
              letter-spacing: .06em; color: var(--muted); }
.card-meta { font-size: 11px; color: var(--muted); font-family: var(--font-mono); }
/* FAMILLES */
.famille-header-row { display: grid; grid-template-columns: 140px 1fr 80px 58px;
                      gap: 10px; padding-bottom: 6px; margin-bottom: 2px;
                      border-bottom: 1px solid var(--border); }
.col-label { font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
.famille-item { display: grid; grid-template-columns: 140px 1fr 80px 58px;
                gap: 10px; align-items: center;
                padding: 5px 0; border-bottom: 1px solid var(--border-subtle); }
.famille-item:last-child { border-bottom: none; }
.famille-name { font-size: 12px; font-weight: 500; white-space: nowrap;
                overflow: hidden; text-overflow: ellipsis; }
.bar-track { height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 4px; }
.bar-green  { background: var(--accent); }
.bar-red    { background: var(--negative); }
.bar-orange { background: var(--warning); }
.famille-ca { font-family: var(--font-mono); font-size: 12px;
              font-variant-numeric: tabular-nums; text-align: right; }
.evo-badge { font-family: var(--font-mono); font-size: 10px; font-variant-numeric: tabular-nums;
             padding: 2px 5px; border-radius: 3px; text-align: center; white-space: nowrap; }
.evo-up   { background: oklch(22% 0.08 130); color: var(--positive); }
.evo-down { background: oklch(22% 0.08 25);  color: var(--negative); }
/* TWO COL */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
/* PNEUS */
.saison-list { display: flex; flex-direction: column; gap: 8px; }
.saison-row { display: grid; grid-template-columns: 76px 1fr auto; gap: 12px;
              align-items: center; background: var(--surface-elevated);
              border-radius: 4px; padding: 10px 12px; }
.saison-name { font-size: 12px; font-weight: 600; }
.ete   { color: var(--warning); }
.qs    { color: var(--accent); }
.hiver { color: oklch(70% 0.12 220); }
.saison-stats { display: flex; gap: 18px; }
.s-stat { display: flex; flex-direction: column; gap: 1px; }
.s-val  { font-family: var(--font-mono); font-size: 14px; font-weight: 600;
          font-variant-numeric: tabular-nums; }
.s-lbl  { font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }
.pneus-cat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-top: 10px; }
.pneu-cat { background: var(--surface-elevated); border-radius: 4px; padding: 8px 10px; }
.pneu-cat-lbl { font-size: 10px; text-transform: uppercase; letter-spacing: .05em;
                color: var(--muted); margin-bottom: 3px; }
.pneu-cat-val { font-family: var(--font-mono); font-size: 16px; font-weight: 600; }
.pneu-cat-sub { font-family: var(--font-mono); font-size: 10px; color: var(--muted); }
/* RAF */
.obj-list { display: flex; flex-direction: column; gap: 13px; }
.obj-item { display: flex; flex-direction: column; gap: 5px; }
.obj-row  { display: flex; justify-content: space-between; align-items: center; }
.obj-lbl  { font-size: 13px; }
.obj-vals { display: flex; align-items: baseline; gap: 8px; }
.obj-cur  { font-family: var(--font-mono); font-size: 14px;
            font-variant-numeric: tabular-nums; color: var(--accent); }
.obj-tgt  { font-family: var(--font-mono); font-size: 12px;
            font-variant-numeric: tabular-nums; color: var(--muted); }
.obj-bar  { height: 4px; background: var(--border); border-radius: 2px; }
.obj-fill { height: 100%; border-radius: 2px; }
.fill-ok   { background: var(--positive); }
.fill-warn { background: var(--warning); }
.fill-bad  { background: var(--negative); }
.obj-foot  { display: flex; justify-content: space-between;
             font-size: 10px; color: var(--muted); font-family: var(--font-mono); }
/* SIDEBAR */
.sidebar { display: flex; flex-direction: column; gap: 16px; grid-row: 3 / 4; }
/* RATIOS */
.ratio-item { display: flex; flex-direction: column; gap: 4px;
              padding: 8px 0; border-bottom: 1px solid var(--border-subtle); }
.ratio-item:last-child { border-bottom: none; }
.ratio-header { display: flex; justify-content: space-between; align-items: center; }
.ratio-name   { font-size: 12px; font-weight: 500; }
.ratio-vals   { display: flex; align-items: baseline; gap: 5px; }
.ratio-cur    { font-family: var(--font-mono); font-size: 14px; font-weight: 600;
                font-variant-numeric: tabular-nums; }
.r-good { color: var(--positive); }
.r-bad  { color: var(--negative); }
.ratio-obj   { font-family: var(--font-mono); font-size: 11px; color: var(--muted); }
.ratio-ecart { font-family: var(--font-mono); font-size: 10px; }
.ratio-track { height: 4px; background: var(--border); border-radius: 2px; }
.ratio-fill  { height: 100%; border-radius: 2px; }
.rf-good { background: var(--positive); }
.rf-bad  { background: var(--negative); }
/* STAFF */
.staff-table { width: 100%; border-collapse: collapse; }
.staff-table th { color: var(--muted); font-size: 10px; font-weight: 500;
                  text-transform: uppercase; letter-spacing: .04em;
                  padding: 4px; text-align: right;
                  border-bottom: 1px solid var(--border); }
.staff-table th:first-child { text-align: left; }
.staff-table td { padding: 5px 4px; text-align: right; font-family: var(--font-mono);
                  font-size: 10px; border-bottom: 1px solid var(--border-subtle); }
.staff-table td:first-child { text-align: left; font-family: var(--font-body);
                               font-size: 11px; font-weight: 500; }
.staff-table tr:last-child td { border-bottom: none; }
.t-good { color: var(--positive); }
.t-bad  { color: var(--negative); }
/* ACTIONS */
.action-list { display: flex; flex-direction: column; gap: 7px; }
.action-item { background: var(--surface-elevated); border-radius: 4px;
               padding: 9px 11px; display: flex; gap: 9px; align-items: flex-start; }
.action-tag  { flex-shrink: 0; font-size: 9px; text-transform: uppercase;
               letter-spacing: .06em; padding: 2px 5px; border-radius: 3px; margin-top: 1px; }
.tag-ls   { background: oklch(28% 0.08 130); color: var(--accent); }
.tag-atel { background: oklch(28% 0.08 240); color: oklch(68% 0.14 240); }
.tag-prio { background: oklch(28% 0.10 25);  color: var(--negative); }
.action-text { font-size: 11px; line-height: 1.45; }
.action-text strong { font-weight: 600; display: block; margin-bottom: 1px; }

/* CHARTS */
.chart-stack { display: flex; flex-direction: column; gap: 16px; }
.chart-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
.chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.chart-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
.chart-legend { display: flex; gap: 16px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--muted); }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; }
.chart-area { height: 140px; position: relative; display: flex; align-items: flex-end; }
.chart-svg { width: 100%; height: 100%; }
.chart-grid-line { stroke: var(--border); stroke-width: 1; }
.chart-line { fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.chart-line.primary { stroke: var(--accent); }
.chart-line.secondary { stroke: var(--muted); }
.chart-area-fill { opacity: 0.15; }
.chart-area-fill.primary { fill: var(--accent); }

/* RETENTION GRID */
.retention-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
.retention-header { margin-bottom: 12px; }
.retention-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
.retention-grid { display: grid; grid-template-columns: 60px repeat(4, 1fr); gap: 2px; font-family: var(--font-mono); font-size: 10px; font-variant-numeric: tabular-nums; }
.retention-label { color: var(--muted); display: flex; align-items: center; }
.retention-label.header { justify-content: center; padding-bottom: 4px; }
.retention-cell { background: var(--accent-dim); padding: 6px 4px; text-align: center; border-radius: 2px; color: var(--fg); }
.retention-cell[data-value="high"] { background: var(--accent); color: var(--bg); }
.retention-cell[data-value="medium"] { background: oklch(50% 0.14 130); }
.retention-cell[data-value="low"] { background: oklch(35% 0.10 130); }
/* HEATMAP */
.heatmap-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
.heatmap-header { margin-bottom: 12px; }
.heatmap-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
.heatmap-grid { display: grid; grid-template-columns: 40px repeat(12, 1fr); gap: 2px; }
.heatmap-label { font-family: var(--font-mono); font-size: 10px; color: var(--muted); display: flex; align-items: center; }
.heatmap-label.hour { justify-content: center; padding-bottom: 4px; }
.heatmap-cell { aspect-ratio: 1; border-radius: 2px; background: var(--accent-dim); opacity: 0.2; transition: opacity 0.15s; }
.heatmap-cell[data-intensity="1"] { opacity: 0.3; }
.heatmap-cell[data-intensity="2"] { opacity: 0.5; }
.heatmap-cell[data-intensity="3"] { opacity: 0.7; }
.heatmap-cell[data-intensity="4"] { opacity: 0.9; }
.heatmap-cell[data-intensity="5"] { opacity: 1; background: var(--accent); }
/* LEADERBOARD */
.leaderboard-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
.leaderboard-header { margin-bottom: 12px; }
.leaderboard-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
.leaderboard-list { display: flex; flex-direction: column; gap: 8px; }
.leaderboard-item { display: grid; grid-template-columns: 20px 1fr auto; gap: 8px; align-items: center; padding: 8px; background: var(--surface-elevated); border-radius: 4px; }
.leaderboard-rank { font-family: var(--font-mono); font-size: 11px; color: var(--muted); font-variant-numeric: tabular-nums; }
.leaderboard-name { font-size: 13px; font-weight: 500; }
.leaderboard-value { font-family: var(--font-mono); font-size: 13px; font-variant-numeric: tabular-nums; color: var(--accent); }
.leaderboard-bar { grid-column: 2 / 3; height: 3px; background: var(--border); border-radius: 2px; margin-top: 4px; }
.leaderboard-bar-fill { height: 100%; background: var(--accent); border-radius: 2px; }
/* FEED */
.feed-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 16px; min-height: 200px; display: flex; flex-direction: column; }
.feed-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.feed-title { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
.feed-live { display: flex; align-items: center; gap: 6px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); }
.feed-live-dot { width: 6px; height: 6px; background: var(--accent); border-radius: 50%; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.feed-list { display: flex; flex-direction: column; gap: 4px; overflow-y: auto; flex: 1; }
.feed-item { display: grid; grid-template-columns: 50px 1fr auto; gap: 8px; padding: 8px; background: var(--surface-elevated); border-radius: 4px; font-size: 12px; }
.feed-time { font-family: var(--font-mono); font-size: 10px; color: var(--muted); font-variant-numeric: tabular-nums; }
.feed-event { color: var(--fg); }
.feed-amount { font-family: var(--font-mono); font-variant-numeric: tabular-nums; color: var(--accent); }
.feed-tag { display: inline-block; padding: 2px 6px; border-radius: 3px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em; background: var(--accent-dim); color: var(--accent); margin-right: 6px; }
.feed-tag.service { background: oklch(30% 0.08 240); color: oklch(70% 0.12 240); }
.feed-tag.vente { background: oklch(30% 0.10 130); color: var(--accent); }
/* BRIEF GLOBAL */
.brief-card { background: var(--surface); border: 1px solid var(--border);
              border-radius: 6px; padding: 14px 16px; grid-column: 1 / -1; }
.brief-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.brief-title { font-size: 11px; font-weight: 600; text-transform: uppercase;
               letter-spacing: .08em; color: var(--muted); }
.brief-period { font-family: var(--font-mono); font-size: 10px; color: var(--muted);
                background: var(--surface-elevated); padding: 2px 8px; border-radius: 3px; }
.brief-text { font-size: 13px; line-height: 1.65; color: var(--fg); }
/* UTIL */
.no-data { color: var(--muted); font-size: 13px; padding: 24px;
           text-align: center; font-style: italic; }
.kv-table { width: 100%; border-collapse: collapse; }
.kv-table td { padding: 6px 4px; font-size: 12px;
               border-bottom: 1px solid var(--border-subtle); }
.kv-table td:last-child { text-align: right; font-family: var(--font-mono);
                           font-variant-numeric: tabular-nums; }
.kv-table tr:last-child td { border-bottom: none; }
</style>"""

# Auto-height JS — tells Streamlit to resize the iframe to fit
_AUTOHEIGHT = """<script>
function sendH(){
  const h = Math.max(document.documentElement.scrollHeight, document.body.scrollHeight);
  window.parent.postMessage({type:'streamlit:setFrameHeight', height:h}, '*');
}
window.addEventListener('load', sendH);
window.addEventListener('resize', sendH);
new MutationObserver(sendH).observe(document.body,{subtree:true,childList:true});
</script>"""


# ════════════════════════════════════════════════════════════════════════════
# FORMATTING HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _e(s) -> str:
    """HTML-escape a value for safe inline injection."""
    return _html.escape(str(s)) if s is not None else "—"

def _eur(v, d: int = 0) -> str:
    if v is None: return "—"
    try:
        s = f"{int(v):,}".replace(",", "\u202f")
        return f"{s}\u202f€"
    except (TypeError, ValueError): return "—"

def _pct(v, sign: bool = False) -> str:
    if v is None: return "—"
    try:
        f = float(v)
        prefix = "+" if sign and f >= 0 else ""
        return f"{prefix}{f:.1f}\u202f%".replace(".", ",")
    except (TypeError, ValueError): return "—"

def _dcls(v) -> str:
    if v is None: return ""
    try: return "pos" if float(v) > 0 else "neg" if float(v) < 0 else ""
    except: return ""

def _evo_badge(v) -> str:
    if v is None: return ""
    try:
        f   = float(v)
        cls = "evo-up" if f >= 0 else "evo-down"
        return f'<span class="evo-badge {cls}">{_pct(f, sign=True)}</span>'
    except: return ""

def _spark(trend: str = "up") -> str:
    h = {"up":[35,42,50,58,62,70,80], "down":[85,78,72,68,65,60,55], "flat":[60,58,63,60,62,59,62]}
    heights = h.get(trend, h["flat"])
    bars = "".join(
        f'<div class="spark-bar{"  cur" if i==len(heights)-1 else ""}" style="height:{v}%"></div>'
        for i, v in enumerate(heights)
    )
    return f'<div class="kpi-sparkline">{bars}</div>'

def _bar_w(val, max_val) -> float:
    if not max_val: return 0
    try: return min(100.0, max(0.0, abs(float(val)) / abs(float(max_val)) * 100))
    except: return 0


# ════════════════════════════════════════════════════════════════════════════
# HTML SECTION BUILDERS
# ════════════════════════════════════════════════════════════════════════════

def _header(week_label: str, period_str: str) -> str:
    return f"""
<header class="header">
  <div class="header-left">
    <div class="logo">FV</div>
    <div>
      <h1 class="header-title">Feu Vert Annecy 203</h1>
      <p class="header-subtitle">Briefing Hebdomadaire</p>
    </div>
  </div>
  <div class="week-badge">{_e(week_label)}&nbsp;&nbsp;·&nbsp;&nbsp;{_e(period_str)}</div>
</header>"""


def _kpi_strip(g: dict, ls: dict, at: dict) -> str:
    def card(label, sublabel, value, dv, dlabel, trend="up"):
        arrow = "↑" if dv and float(dv) > 0 else ("↓" if dv and float(dv) < 0 else "→")
        return (f'<div class="kpi-card">'
                f'<span class="kpi-label">{_e(label)}</span>'
                f'<p class="kpi-sublabel">{sublabel}</p>'
                f'<div class="kpi-value-row">'
                f'<span class="kpi-value">{value}</span>'
                f'<span class="kpi-delta {_dcls(dv)}">{arrow} {_e(dlabel)}</span>'
                f'</div>{_spark(trend)}</div>')

    cards = "".join([
        card("CA TTC Total",
             f"obj. {_eur(g.get('ca_obj_ht'))} · écart {_pct(g.get('ca_ecart'),True)}",
             _eur(g.get("ca_ht")),
             g.get("ca_evo"), _pct(g.get("ca_evo"), True) + " vs N-1",
             "up" if (g.get("ca_evo") or 0) >= 0 else "down"),
        card("Marge Globale",
             f"obj. {_pct(g.get('marge_obj'))} · {_pct(g.get('marge_ecart'),True)} pts",
             _pct(g.get("marge")),
             g.get("marge_evo"), _pct(g.get("marge_evo"), True) + " pts vs N-1", "up"),
        card("Fréquentation",
             f"N-1&nbsp;: {g.get('freq_n1','—')} clients",
             str(g.get("freq") or "—"),
             g.get("freq_evo"), _pct(g.get("freq_evo"), True) + " vs N-1", "up"),
        card("Panier Moyen",
             f"N-1&nbsp;: {_eur(g.get('panier'),1)} · Atel. {_eur(at.get('panier'),1)}",
             _eur(g.get("panier"), 1) if g.get("panier") else "—",
             g.get("panier_evo"), _pct(g.get("panier_evo"), True) + " vs N-1", "down"),
        card("CA Atelier",
             f"{at.get('nb_or','—')} OR · Marge {_pct(at.get('marge'))}",
             _eur(at.get("ca")),
             at.get("ca_evo"), _pct(at.get("ca_evo"), True) + " vs N-1", "up"),
        card("CA Libre Service",
             f"Panier {_eur(ls.get('panier'),1)} · Marge {_pct(ls.get('marge'))}",
             _eur(ls.get("ca")),
             ls.get("ca_evo"), _pct(ls.get("ca_evo"), True) + " vs N-1", "up"),
    ])
    return f'<section class="kpi-strip">{cards}</section>'

def _ls_kpi_strip(ls: dict) -> str:
    def card(label, sublabel, value, dv, dlabel, trend):
        arrow = "↑" if trend == "up" else "↓" if trend == "down" else "→"
        return (f'<div class="kpi-card">'
                f'<span class="kpi-label">{_e(label)}</span>'
                f'<p class="kpi-sublabel">{sublabel}</p>'
                f'<div class="kpi-value-row">'
                f'<span class="kpi-value">{value}</span>'
                f'<span class="kpi-delta {_dcls(dv)}">{arrow} {_e(dlabel)}</span>'
                f'</div>{_spark(trend)}</div>')

    cards = "".join([
        card("CA Libre Service",
             f"obj. {_eur(ls.get('ca_obj'))}",
             _eur(ls.get("ca")),
             ls.get("ca_evo"), _pct(ls.get("ca_evo"), True) + " vs N-1", "up"),
        card("Marge LS",
             f"obj. {_pct(ls.get('marge_obj'))}",
             _pct(ls.get("marge")),
             ls.get("marge_evo"), _pct(ls.get("marge_evo"), True) + " pts vs N-1", "up"),
        card("Fréquentation LS",
             f"N-1&nbsp;: {ls.get('freq_n1','—')} clients",
             str(ls.get("freq") or "—"),
             ls.get("freq_evo"), _pct(ls.get("freq_evo"), True) + " vs N-1", "up"),
        card("Panier Moyen LS",
             f"N-1&nbsp;: {_eur(ls.get('panier_n1'),1)}",
             _eur(ls.get("panier"), 1) if ls.get("panier") else "—",
             ls.get("panier_evo"), _pct(ls.get("panier_evo"), True) + " vs N-1", "down"),
    ])
    return f'<section class="kpi-strip">{cards}</section>'

def _at_kpi_strip(at: dict) -> str:
    def card(label, sublabel, value, dv, dlabel, trend):
        arrow = "↑" if trend == "up" else "↓" if trend == "down" else "→"
        return (f'<div class="kpi-card">'
                f'<span class="kpi-label">{_e(label)}</span>'
                f'<p class="kpi-sublabel">{sublabel}</p>'
                f'<div class="kpi-value-row">'
                f'<span class="kpi-value">{value}</span>'
                f'<span class="kpi-delta {_dcls(dv)}">{arrow} {_e(dlabel)}</span>'
                f'</div>{_spark(trend)}</div>')

    cards = "".join([
        card("CA Atelier",
             f"obj. {_eur(at.get('ca_obj'))}",
             _eur(at.get("ca")),
             at.get("ca_evo"), _pct(at.get("ca_evo"), True) + " vs N-1", "up"),
        card("Marge Atelier",
             f"obj. {_pct(at.get('marge_obj'))}",
             _pct(at.get("marge")),
             at.get("marge_evo"), _pct(at.get("marge_evo"), True) + " pts vs N-1", "up"),
        card("Nombre d'OR",
             f"N-1&nbsp;: {at.get('nb_or_n1','—')}",
             str(at.get("nb_or") or "—"),
             at.get("nb_or_evo"), _pct(at.get("nb_or_evo"), True) + " vs N-1", "up"),
        card("Panier Moyen Atelier",
             f"N-1&nbsp;: {_eur(at.get('panier_n1'),1)}",
             _eur(at.get("panier"), 1) if at.get("panier") else "—",
             at.get("panier_evo"), _pct(at.get("panier_evo"), True) + " vs N-1", "up"),
    ])
    return f'<section class="kpi-strip">{cards}</section>'


def _familles_html(fam_data: dict) -> str:
    if not fam_data.get("available"):
        return '<div class="card"><p class="no-data">⏳ Données familles indisponibles</p></div>'

    NAME_MAP = {
        "X-TARIF MAIN D'OEUVRE":   "X · Main d'Œuvre",
        "E-EQUIPEMENT EXTERIEUR":  "E · Équip. Extérieur",
        "F-EQUIPEMENT INTERIEUR":  "F · Équip. Intérieur",
        "I-PNEUMATIQUES":          "I · Pneumatiques",
        "C-PIECES TECHNIQUES":     "C · Pièces Techniques",
        "A-ENTRETIEN":             "A · Entretien",
        "H-LUBRIFIANTS":           "H · Lubrifiants",
        "B-ELECTRICITE":           "B · Électricité",
        "G-AUTO SON":              "G · Auto Son",
        "J-2 ROUES":               "J · 2 Roues",
        "D-OUTILLAGE":             "D · Outillage",
        "W-DIVERS":                "W · Divers",
        "U-SERVICES":              "U · Services",
    }

    df      = fam_data["df"].copy()
    valid   = df[df["CA N (€)"].notna()].sort_values("CA N (€)", ascending=False)
    max_ca  = valid["CA N (€)"].abs().max() or 1

    rows = ""
    for _, r in valid.iterrows():
        name  = r.get("Famille", "")
        ca    = r.get("CA N (€)")
        evo   = r.get("Évo. CA (%)")
        mg_d  = r.get("Δ Marge (pts)")

        short    = NAME_MAP.get(name, name)
        is_neg   = ca is not None and ca < 0
        mg_alert = mg_d is not None and mg_d < -5
        evo_neg  = evo is not None and evo < 0

        bar_cls  = "bar-red" if (is_neg or evo_neg) else "bar-orange" if mg_alert else "bar-green"
        ca_style = ("color:var(--negative)" if is_neg
                    else "color:var(--accent)" if name.startswith("X-")
                    else "color:var(--warning)" if mg_alert else "")
        ca_str   = f"−{_eur(abs(ca))}" if is_neg and ca else _eur(ca)
        width    = _bar_w(ca, max_ca)

        rows += (f'<div class="famille-item">'
                 f'<span class="famille-name">{_e(short)}</span>'
                 f'<div class="bar-track"><div class="bar-fill {bar_cls}" style="width:{width:.1f}%"></div></div>'
                 f'<span class="famille-ca" style="{ca_style}">{ca_str}</span>'
                 f'{_evo_badge(evo)}</div>')

    return (f'<div class="card">'
            f'<div class="card-header">'
            f'<span class="card-title">Performance par Famille</span>'
            f'<span class="card-meta">CA TTC · évolution vs N-1 · trié par CA décroissant</span>'
            f'</div>'
            f'<div class="famille-header-row">'
            f'<span class="col-label">Famille</span>'
            f'<span class="col-label">Proportion</span>'
            f'<span class="col-label" style="text-align:right">CA TTC</span>'
            f'<span class="col-label" style="text-align:center">Évo.</span>'
            f'</div>{rows}</div>')


def _pneus_html(tire_data: dict, week_num) -> str:
    if not tire_data.get("available"):
        return '<div class="card"><p class="no-data">⏳ Données pneus indisponibles</p></div>'

    s    = tire_data["summary"]
    df_s = tire_data["season_df"]
    df_c = tire_data["category_mix_df"]

    srows = ""
    for label, cls, icon in [("ÉTÉ","ete","☀"),("4 SAISONS","qs","❄☀"),("HIVER","hiver","❄")]:
        r = df_s[df_s["Saison"] == label]
        if r.empty: continue
        r   = r.iloc[0]
        qty = int(r.get("Qté") or 0)
        ca  = r.get("CA (€)") or 0
        mp  = r.get("Marge (%)")
        evo = r.get("Évo. CA (%)")
        mc  = "color:var(--negative)" if mp and mp < 10 else "color:var(--accent)"
        srows += (f'<div class="saison-row">'
                  f'<span class="saison-name {cls}">{icon} {_e(label)}</span>'
                  f'<div class="saison-stats">'
                  f'<div class="s-stat"><span class="s-val">{qty}</span><span class="s-lbl">unités</span></div>'
                  f'<div class="s-stat"><span class="s-val">{_eur(ca)}</span><span class="s-lbl">CA</span></div>'
                  f'<div class="s-stat"><span class="s-val" style="{mc}">{_pct(mp)}</span><span class="s-lbl">Marge</span></div>'
                  f'</div>{_evo_badge(evo)}</div>')

    total_qty = int(df_c["Qté"].sum() or 1)
    ccards = ""
    for cat, col in [("PREMIUM","color:var(--accent)"),("MEDIUM","color:var(--warning)"),("BUDGET","color:var(--muted)")]:
        cr  = df_c[df_c["Catégorie"] == cat]
        if cr.empty: continue
        qty = int(cr.iloc[0].get("Qté") or 0)
        pct = round(qty / total_qty * 100, 1) if total_qty else 0
        ccards += (f'<div class="pneu-cat">'
                   f'<div class="pneu-cat-lbl">{_e(cat.capitalize())}</div>'
                   f'<div class="pneu-cat-val" style="{col}">{qty}</div>'
                   f'<div class="pneu-cat-sub">unités · {pct:.1f}\u202f%</div>'
                   f'</div>')

    meta = f"{s.get('qty',0)} unités · {_eur(s.get('ca'))} · marge {_pct(s.get('marge_pct'))}"
    return (f'<div class="card">'
            f'<div class="card-header">'
            f'<span class="card-title">Pneus par Saison — S{week_num or "?"}</span>'
            f'<span class="card-meta">{meta}</span>'
            f'</div>'
            f'<div class="saison-list">{srows}</div>'
            f'<div style="margin-top:14px">'
            f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.06em;'
            f'color:var(--muted);margin-bottom:8px">Mix catégorie — toutes saisons</div>'
            f'<div class="pneus-cat-grid">{ccards}</div></div></div>')


def _raf_html(kpis: dict) -> str:
    mtd = kpis.get("mtd", {})
    if not mtd:
        return '<div class="card"><p class="no-data">⏳ Données MTD indisponibles</p></div>'

    def item(label, cur_s, tgt_s, pct, raf_s, raf_color):
        pct_c = min(100.0, max(0.0, float(pct or 0)))
        fill  = "fill-ok" if pct_c >= 100 else "fill-warn" if pct_c >= 85 else "fill-bad"
        raf_l = "Objectif dépassé ✓" if pct_c >= 100 else f"RAF\u202f: {raf_s}"
        cc    = "color:var(--positive)" if pct_c >= 100 else "color:var(--accent)"
        return (f'<div class="obj-item">'
                f'<div class="obj-row">'
                f'<span class="obj-lbl">{_e(label)}</span>'
                f'<div class="obj-vals">'
                f'<span class="obj-cur" style="{cc}">{cur_s}</span>'
                f'<span class="obj-tgt">/ {tgt_s}</span>'
                f'</div></div>'
                f'<div class="obj-bar"><div class="obj-fill {fill}" style="width:{pct_c:.1f}%"></div></div>'
                f'<div class="obj-foot">'
                f'<span>{pct_c:.1f}\u202f% réalisé</span>'
                f'<span style="{raf_color}">{raf_l}</span>'
                f'</div></div>')

    ca_pct  = mtd.get("ca_pct") or 0
    mg_pct  = mtd.get("marge_pct") or 0
    items   = "".join([
        item("Chiffre d'Affaires", _eur(mtd.get("ca")), _eur(mtd.get("ca_obj")),
             ca_pct, _eur(mtd.get("ca_raf")),
             "color:var(--positive)" if ca_pct >= 100 else
             "color:var(--warning)"  if ca_pct >= 85  else "color:var(--negative)"),
        item("Marge", _eur(mtd.get("marge_eur")), _eur(mtd.get("marge_obj")),
             mg_pct, _eur(mtd.get("marge_raf")),
             "color:var(--positive)" if mg_pct >= 100 else
             "color:var(--warning)"  if mg_pct >= 85  else "color:var(--negative)"),
        item("Contrats", str(mtd.get("contrats") or "—"), "—",
             None, "—", "color:var(--muted)"),
    ])
    return (f'<div class="card">'
            f'<div class="card-header">'
            f'<span class="card-title">Reste à Faire — Mois en cours</span>'
            f'<span class="card-meta">Cumul mensuel</span>'
            f'</div><div class="obj-list">{items}</div></div>')


def _ratios_html(ratio_data: dict, week_num) -> str:
    if not ratio_data.get("available"):
        return '<div class="card"><p class="no-data">⏳ Données ratios indisponibles</p></div>'

    rows = ""
    for _, r in ratio_data["df"].iterrows():
        real = r.get("Réalisé (%)")
        obj  = r.get("Objectif (%)", 1) or 1
        ec   = r.get("Écart obj")
        ok   = r.get("Statut") == "🟢"
        cc   = "r-good" if ok else "r-bad"
        fc   = "rf-good" if ok else "rf-bad"
        ecc  = "color:var(--positive)" if ok else "color:var(--negative)"
        ecs  = (f"+{ec:.0f} pts" if ec and ec >= 0 else f"{ec:.0f} pts") if ec is not None else "—"
        w    = _bar_w(real or 0, obj)
        rows += (f'<div class="ratio-item">'
                 f'<div class="ratio-header">'
                 f'<span class="ratio-name">{_e(r.get("KPI",""))}</span>'
                 f'<div class="ratio-vals">'
                 f'<span class="ratio-cur {cc}">{_pct(real)}</span>'
                 f'<span class="ratio-obj">/ obj. {_pct(obj)}</span>'
                 f'<span class="ratio-ecart" style="{ecc}">{ecs}</span>'
                 f'</div></div>'
                 f'<div class="ratio-track"><div class="ratio-fill {fc}" style="width:{w:.0f}%"></div></div>'
                 f'</div>')

    return (f'<div class="card">'
            f'<div class="card-header">'
            f'<span class="card-title">Ratios Prioritaires</span>'
            f'<span class="card-meta">Atelier · S{week_num or "?"}</span>'
            f'</div>{rows}</div>')


def _staff_html(vendor_data: dict, week_num) -> str:
    if not vendor_data.get("available"):
        return '<div class="card"><p class="no-data">⏳ Données vendeurs indisponibles</p></div>'

    OBJ  = {"Garantie Pneu":50,"Géométrie":19,"VCR":7,"VCF":11,"Plaquette":11,"Dépoll.":35}
    COLS = [("Garantie Pneu","GP"),("Géométrie","Géo"),("VCR","VCR"),("VCF","VCF"),("Dépoll.","Dép.")]

    ths  = "".join(f'<th title="{_e(f)}">{_e(a)}</th>' for f, a in COLS)
    rows = ""
    for _, r in vendor_data["df"].iterrows():
        tds = ""
        for kpi, _ in COLS:
            v = r.get(kpi)
            o = OBJ.get(kpi, 0)
            if v is None:
                tds += "<td>—</td>"
            else:
                cls = "t-good" if v >= o else "t-bad"
                tds += f'<td class="{cls}">{str(v).replace(".",",")}</td>'
        rows += f'<tr><td>{_e(r.get("Vendeur",""))}</td>{tds}</tr>'

    return (f'<div class="card">'
            f'<div class="card-header">'
            f'<span class="card-title">Ratios LS — Vendeurs</span>'
            f'<span class="card-meta">S{week_num or "?"}</span>'
            f'</div>'
            f'<table class="staff-table">'
            f'<thead><tr><th>Vendeur</th>{ths}</tr></thead>'
            f'<tbody>{rows}</tbody>'
            f'</table>'
            f'<p style="margin-top:8px;font-size:10px;color:var(--muted)">'
            f'GP = Garantie Pneu · Dép. = Dépollution · valeurs en %</p></div>')


def _brief_html(brief_text: str | None, week_num, period_str: str | None) -> str:
    w_label = f"S{week_num}" if week_num else "—"
    p_label = period_str or "—"
    badge = f"{w_label} · {p_label}"
    text = _e(brief_text) if brief_text else "<em style='color:var(--muted)'>Brief global non disponible</em>"
    return (f'<div class="brief-card">'
            f'<div class="brief-header">'
            f'<span class="brief-title">1. Brief global</span>'
            f'<span class="brief-period">{badge}</span>'
            f'</div>'
            f'<p class="brief-text">{text}</p>'
            f'</div>')

def _section_label(number: str, title: str) -> str:
    return (f'<div style="display:flex;align-items:center;gap:12px;'
            f'padding:20px 0 6px;border-top:1px solid var(--border)">'
            f'<span style="font-size:10px;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:.1em;color:var(--bg);background:var(--accent);'
            f'padding:3px 9px;border-radius:3px">{_e(number)}</span>'
            f'<span style="font-size:14px;font-weight:600;color:var(--fg)">{_e(title)}</span>'
            f'</div>')


def _rh_html(rh: dict) -> str:
    if not rh.get("available"):
        return '<div class="card"><p class="no-data">⏳ Données RH indisponibles</p></div>'

    def sub(label, items):
        if not items:
            return ''
        lis = "".join(
            f'<li style="font-size:13px;padding:4px 0;color:var(--fg)">{_e(i)}</li>'
            for i in items
        )
        return (f'<div style="margin-bottom:14px">'
                f'<div style="font-size:10px;font-weight:600;text-transform:uppercase;'
                f'letter-spacing:.06em;color:var(--muted);margin-bottom:6px">{_e(label)}</div>'
                f'<ul style="list-style:disc;padding-left:16px;margin:0">{lis}</ul></div>')

    body = (sub("Alertes", rh.get("alerte", [])) +
            sub("Absences / Congés", rh.get("absence", [])) +
            sub("Recrutement / Départs", rh.get("recrutement", [])))
    if not body:
        body = '<p class="no-data">Aucune information RH</p>'

    return (f'<div class="card">'
            f'<div class="card-header"><span class="card-title">Ressources Humaines</span></div>'
            f'{body}</div>')


def _notes_html(notes: list, title: str) -> str:
    if not notes:
        return ''
    lis = "".join(
        f'<li style="font-size:12px;line-height:1.6;padding:5px 0;'
        f'border-bottom:1px solid var(--border-subtle);color:var(--fg)">{_e(n)}</li>'
        for n in notes
    )
    return (f'<div class="card">'
            f'<div class="card-header"><span class="card-title">{_e(title)}</span></div>'
            f'<ul style="list-style:none;padding:0;margin:0">{lis}</ul></div>')


def _tire_brands_html(brands: dict, week_num) -> str:
    if not brands.get("available") or brands["df"].empty:
        return '<div class="card"><p class="no-data">⏳ Détail marques indisponible</p></div>'

    df    = brands["df"]
    valid = df[df["Qté_n"].notna()].copy()

    rows = ""
    for _, r in valid.iterrows():
        evo = r.get("Evo_pct")
        mg  = r.get("Marge_pct")
        st  = str(r.get("Statut", ""))
        sc  = ("var(--positive)" if "🟢" in st
               else "var(--negative)" if "🔴" in st else "var(--warning)")
        rows += (f'<tr>'
                 f'<td>{_e(r.get("Catégorie",""))}</td>'
                 f'<td>{_e(r.get("Marque",""))}</td>'
                 f'<td style="text-align:right">{int(r["Qté_n"])}</td>'
                 f'<td style="text-align:right">{_eur(r.get("CA_n"))}</td>'
                 f'<td style="text-align:right">{_pct(evo, True) if evo is not None else "—"}</td>'
                 f'<td style="text-align:right;color:{sc}">{_pct(mg)}</td>'
                 f'</tr>')

    return (f'<div class="card">'
            f'<div class="card-header">'
            f'<span class="card-title">Détail par Marque</span>'
            f'<span class="card-meta">ÉTÉ · S{week_num or "?"}</span>'
            f'</div>'
            f'<table class="staff-table"><thead><tr>'
            f'<th style="text-align:left">Catégorie</th>'
            f'<th style="text-align:left">Marque</th>'
            f'<th>Qté</th><th>CA</th><th>Évo.</th><th>Marge</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>')


def _defects_html(defect_data: dict, week_num) -> str:
    if not defect_data.get("available") or defect_data["df"].empty:
        return '<div class="card"><p class="no-data">⏳ Données défectuosité indisponibles</p></div>'

    df        = defect_data["df"]
    stat_cols = [c for c in df.columns if c != "Technicien"]
    ths       = "".join(f'<th>{_e(c)}</th>' for c in stat_cols)
    rows      = ""
    for _, r in df.iterrows():
        tds = "".join(f'<td>{_e(r.get(c, "—"))}</td>' for c in stat_cols)
        rows += f'<tr><td>{_e(r.get("Technicien",""))}</td>{tds}</tr>'

    return (f'<div class="card">'
            f'<div class="card-header">'
            f'<span class="card-title">Taux de Défectuosité</span>'
            f'<span class="card-meta">S{week_num or "?"}</span>'
            f'</div>'
            f'<div style="overflow-x:auto">'
            f'<table class="staff-table"><thead><tr>'
            f'<th>Technicien</th>{ths}</tr></thead>'
            f'<tbody>{rows}</tbody></table></div></div>')


def _plan_html(items: list, title: str, tag_cls: str = "tag-ls") -> str:
    if not items:
        return (f'<div class="card"><div class="card-header">'
                f'<span class="card-title">{_e(title)}</span></div>'
                f'<p class="no-data">Plan non disponible</p></div>')

    html_items = "".join(
        f'<div class="action-item">'
        f'<span class="action-tag {tag_cls}" style="min-width:20px;text-align:center">{i + 1}</span>'
        f'<div class="action-text"><strong>{_e(it["title"])}</strong>'
        f'{"<br>" + _e(it["obj"]) if it.get("obj") else ""}'
        f'</div></div>'
        for i, it in enumerate(items)
    )
    return (f'<div class="card">'
            f'<div class="card-header"><span class="card-title">{_e(title)}</span></div>'
            f'<div class="action-list">{html_items}</div></div>')


def _charts_html() -> str:
    return (
        f'<div class="chart-stack" data-od-id="charts">'
        f'<div class="chart-card">'
        f'<div class="chart-header">'
        f'<span class="chart-title">Évolution CA hebdomadaire</span>'
        f'<div class="chart-legend">'
        f'<div class="legend-item"><span class="legend-dot" style="background: var(--accent)"></span><span>2025</span></div>'
        f'<div class="legend-item"><span class="legend-dot" style="background: var(--muted)"></span><span>2024</span></div>'
        f'</div></div>'
        f'<div class="chart-area"><svg class="chart-svg" viewBox="0 0 600 140" preserveAspectRatio="none">'
        f'<line class="chart-grid-line" x1="0" y1="35" x2="600" y2="35"/>'
        f'<line class="chart-grid-line" x1="0" y1="70" x2="600" y2="70"/>'
        f'<line class="chart-grid-line" x1="0" y1="105" x2="600" y2="105"/>'
        f'<path class="chart-area-fill primary" d="M0,100 L50,95 L100,85 L150,90 L200,70 L250,65 L300,55 L350,60 L400,45 L450,40 L500,35 L550,30 L600,25 L600,140 L0,140 Z"/>'
        f'<path class="chart-line primary" d="M0,100 L50,95 L100,85 L150,90 L200,70 L250,65 L300,55 L350,60 L400,45 L450,40 L500,35 L550,30 L600,25"/>'
        f'<path class="chart-line secondary" d="M0,110 L50,105 L100,100 L150,105 L200,95 L250,90 L300,85 L350,90 L400,80 L450,75 L500,70 L550,65 L600,60"/>'
        f'</svg></div></div>'
        f'<div class="chart-card">'
        f'<div class="chart-header">'
        f'<span class="chart-title">Volume d\'interventions</span>'
        f'<div class="chart-legend">'
        f'<div class="legend-item"><span class="legend-dot" style="background: var(--accent)"></span><span>Réalisé</span></div>'
        f'<div class="legend-item"><span class="legend-dot" style="background: var(--muted)"></span><span>Objectif</span></div>'
        f'</div></div>'
        f'<div class="chart-area"><svg class="chart-svg" viewBox="0 0 600 140" preserveAspectRatio="none">'
        f'<line class="chart-grid-line" x1="0" y1="35" x2="600" y2="35"/>'
        f'<line class="chart-grid-line" x1="0" y1="70" x2="600" y2="70"/>'
        f'<line class="chart-grid-line" x1="0" y1="105" x2="600" y2="105"/>'
        f'<path class="chart-area-fill primary" d="M0,95 L50,90 L100,80 L150,85 L200,75 L250,70 L300,60 L350,55 L400,50 L450,45 L500,40 L550,35 L600,30 L600,140 L0,140 Z"/>'
        f'<path class="chart-line primary" d="M0,95 L50,90 L100,80 L150,85 L200,75 L250,70 L300,60 L350,55 L400,50 L450,45 L500,40 L550,35 L600,30"/>'
        f'<path class="chart-line secondary" d="M0,85 L50,85 L100,85 L150,85 L200,85 L250,85 L300,85 L350,85 L400,85 L450,85 L500,85 L550,85 L600,85" stroke-dasharray="4 4"/>'
        f'</svg></div></div></div>'
    )

def _retention_html() -> str:
    return (
        f'<div class="retention-card" data-od-id="retention">'
        f'<div class="retention-header"><span class="retention-title">Rétention clients</span></div>'
        f'<div class="retention-grid">'
        f'<div class="retention-label"></div><div class="retention-label header">M1</div><div class="retention-label header">M3</div><div class="retention-label header">M6</div><div class="retention-label header">M12</div>'
        f'<div class="retention-label">Jan</div><div class="retention-cell" data-value="high">92%</div><div class="retention-cell" data-value="high">78%</div><div class="retention-cell" data-value="medium">54%</div><div class="retention-cell" data-value="low">32%</div>'
        f'<div class="retention-label">Fév</div><div class="retention-cell" data-value="high">88%</div><div class="retention-cell" data-value="high">72%</div><div class="retention-cell" data-value="medium">48%</div><div class="retention-cell" data-value="low">—</div>'
        f'<div class="retention-label">Mar</div><div class="retention-cell" data-value="high">90%</div><div class="retention-cell" data-value="medium">68%</div><div class="retention-cell" data-value="low">—</div><div class="retention-cell" data-value="low">—</div>'
        f'<div class="retention-label">Avr</div><div class="retention-cell" data-value="high">85%</div><div class="retention-cell" data-value="low">—</div><div class="retention-cell" data-value="low">—</div><div class="retention-cell" data-value="low">—</div>'
        f'<div class="retention-label">Mai</div><div class="retention-cell" data-value="high">91%</div><div class="retention-cell" data-value="low">—</div><div class="retention-cell" data-value="low">—</div><div class="retention-cell" data-value="low">—</div>'
        f'</div></div>'
    )

def _heatmap_html() -> str:
    hours = ["8h","9h","10h","11h","12h","14h","15h","16h","17h","18h","19h","20h"]
    days  = ["Lun","Mar","Mer","Jeu","Ven","Sam"]
    import random
    cells = ""
    for d in days:
        cells += f'<div class="heatmap-label">{d}</div>'
        for _ in hours:
            intensity = random.randint(0, 5)
            cells += f'<div class="heatmap-cell" data-intensity="{intensity}"></div>'
    
    h_labels = "".join(f'<div class="heatmap-label hour">{h}</div>' for h in hours)
    return (f'<div class="heatmap-card">'
            f'<div class="heatmap-header"><span class="heatmap-title">Affluence par créneau</span></div>'
            f'<div class="heatmap-grid"><div class="heatmap-label"></div>{h_labels}{cells}</div></div>')


def _leaderboard_html() -> str:
    items = [("Pneus", 18420, 100), ("Vidange", 12850, 70), ("Freinage", 8240, 45), 
             ("Climatisation", 4120, 22), ("Contrôle tech", 3200, 17)]
    rows = ""
    for i, (name, val, pct) in enumerate(items):
        rows += (f'<div class="leaderboard-item">'
                 f'<span class="leaderboard-rank">{i+1}</span>'
                 f'<span class="leaderboard-name">{_e(name)}</span>'
                 f'<span class="leaderboard-value">{_eur(val)}</span>'
                 f'<div class="leaderboard-bar"><div class="leaderboard-bar-fill" style="width:{pct}%"></div></div>'
                 f'</div>')
    return (f'<div class="leaderboard-card">'
            f'<div class="leaderboard-header"><span class="leaderboard-title">Top services — S19</span></div>'
            f'<div class="leaderboard-list">{rows}</div></div>')


def _feed_html() -> str:
    events = [
        ("14:32", "vente", "Vente", "4× Michelin Primacy 4", "+680 €"),
        ("14:18", "service", "Service", "Vidange + filtres", "+89 €"),
        ("13:55", "service", "Service", "Géométrie complète", "+75 €"),
        ("13:42", "vente", "Vente", "2× Continental EcoContact", "+320 €"),
        ("13:28", "service", "Service", "Plaquettes AV + disques", "+245 €"),
    ]
    rows = ""
    for time, tag_cls, tag, body, amt in events:
        rows += (f'<div class="feed-item">'
                 f'<span class="feed-time">{time}</span>'
                 f'<span class="feed-event"><span class="feed-tag {tag_cls}">{tag}</span>{_e(body)}</span>'
                 f'<span class="feed-amount">{amt}</span>'
                 f'</div>')
    return (f'<div class="feed-card">'
            f'<div class="feed-header">'
            f'<span class="feed-title">Activité récente</span>'
            f'<span class="feed-live"><span class="feed-live-dot"></span>Live</span>'
            f'</div><div class="feed-list">{rows}</div></div>')


def _actions_html(fam_data: dict, ratio_data: dict) -> str:
    items = []

    if fam_data.get("available"):
        for a in fam_data.get("margin_alerts", []):
            fam = a.get("Famille", "")
            pts = a.get("Δ Marge (pts)")
            items.append(("tag-ls", "LS",
                          f"Alerte marge — {fam}",
                          f"Dégradation {_pct(pts,True)} pts — revoir mix produit et tarification."))
        for l in fam_data.get("top_losers", []):
            if (l.get("Évo. CA (%)") or 0) >= 0: continue
            items.append(("tag-prio", "⚠ Prio",
                          f"Déclin — {l.get('Famille','')}",
                          f"CA {_pct(l.get('Évo. CA (%)'), True)} vs N-1 — animation commerciale ou révision stock."))

    if ratio_data.get("available"):
        for _, r in ratio_data["df"].iterrows():
            if r.get("Statut") == "🔴":
                ec = r.get("Écart obj")
                if ec is not None and ec < -3:
                    items.append(("tag-atel", "Atelier",
                                  f"{r.get('KPI','')} sous objectif",
                                  f"Écart {ec:+.0f} pts vs obj — questionnement client à renforcer."))

    if not items:
        items = [("tag-atel","Atelier","Aucune alerte critique","Maintenir le niveau de performance.")]

    html_items = "".join(
        f'<div class="action-item">'
        f'<span class="action-tag {cls}">{_e(tag)}</span>'
        f'<div class="action-text"><strong>{_e(title)}</strong>{_e(body)}</div>'
        f'</div>'
        for cls, tag, title, body in items[:6]
    )
    return (f'<div class="card">'
            f'<div class="card-header">'
            f'<span class="card-title">Plans d\'Action</span>'
            f'<span class="card-meta">Semaine en cours</span>'
            f'</div><div class="action-list">{html_items}</div></div>')


# ════════════════════════════════════════════════════════════════════════════
# PAGE ASSEMBLERS
# ════════════════════════════════════════════════════════════════════════════

def _wrap(body: str) -> str:
    return (f'<!doctype html><html lang="fr"><head>'
            f'<meta charset="UTF-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'{_CSS}</head><body>{body}{_AUTOHEIGHT}</body></html>')


def build_global_html(data: dict) -> str:
    kpis = data["kpis"]
    w    = kpis.get("week_num") or "?"
    p    = kpis.get("period") or (None, None)
    wl   = f"S{w}"
    ps   = kpis.get("period_str") or (
               f"{p[0].strftime('%d/%m')} – {p[1].strftime('%d/%m/%Y')}"
               if p and p[0] and p[1] else "—")

    body = (f'<div class="dashboard">'
            f'{_header(wl, ps)}'
            f'{_brief_html(kpis.get("brief"), w, ps)}'
            f'{_kpi_strip(kpis.get("global", {}), kpis.get("ls", {}), kpis.get("atelier", {}))}'
            f'<main class="main-content" style="grid-column:1/-1">'
            f'{_section_label("7", "Reste à Faire — Mois en cours")}'
            f'{_raf_html(kpis)}'
            f'{_section_label("8", "Ressources Humaines")}'
            f'{_rh_html(data.get("rh", {}))}'
            f'</main>'
            f'</div>')
    return _wrap(body)


def build_ls_html(data: dict) -> str:
    kpis = data["kpis"]
    w    = kpis.get("week_num") or "?"
    p    = kpis.get("period") or (None, None)
    wl   = f"S{w}"
    ps   = kpis.get("period_str") or (
               f"{p[0].strftime('%d/%m')} – {p[1].strftime('%d/%m/%Y')}"
               if p and p[0] and p[1] else "—")

    ls = kpis.get("ls", {})

    body = (f'<div class="dashboard">'
            f'{_header(wl, ps)}'
            f'<main class="main-content" style="grid-column:1/-1">'
            f'{_section_label("3", "Libre Service vs N-1")}'
            f'{_ls_kpi_strip(ls)}'
            f'{_familles_html(data["fam"])}'
            f'{_notes_html(data.get("notes_fam") or [], "Points clés — Analyse par Famille")}'
            f'<div class="two-col">'
            f'{_pneus_html(data["tires"], w)}'
            f'{_tire_brands_html(data.get("tire_brands") or {}, w)}'
            f'</div>'
            f'{_notes_html(data.get("notes_pneu") or [], "Points clés — Analyse Pneus")}'
            f'{_section_label("5", "Staff Libre Service — Ratios de Vente")}'
            f'{_staff_html(data["vendors"], w)}'
            f'{_section_label("6", "Plan d\'Action Libre Service")}'
            f'{_plan_html(data.get("plan_ls") or [], "Plan d\'Action Libre Service", "tag-ls")}'
            f'</main></div>')
    return _wrap(body)


def build_atelier_html(data: dict) -> str:
    kpis = data["kpis"]
    w    = kpis.get("week_num") or "?"
    p    = kpis.get("period") or (None, None)
    wl   = f"S{w}"
    ps   = kpis.get("period_str") or (
               f"{p[0].strftime('%d/%m')} – {p[1].strftime('%d/%m/%Y')}"
               if p and p[0] and p[1] else "—")

    at = kpis.get("atelier", {})

    body = (f'<div class="dashboard">'
            f'{_header(wl, ps)}'
            f'<main class="main-content" style="grid-column:1/-1">'
            f'{_section_label("3", "Atelier vs N-1")}'
            f'{_at_kpi_strip(at)}'
            f'{_section_label("4", "Ratios Prioritaires")}'
            f'{_ratios_html(data["ratios"], w)}'
            f'{_section_label("5", "Staff Atelier — Taux de Défectuosité")}'
            f'{_defects_html(data["defects"], w)}'
            f'{_section_label("6", "Plan d\'Action Atelier")}'
            f'{_plan_html(data.get("plan_at") or [], "Plan d\'Action Atelier", "tag-atel")}'
            f'</main></div>')
    return _wrap(body)


def build_monthly_global_html(data: dict) -> str:
    kpis = data["kpis"]
    w    = kpis.get("week_num") or "?"
    ls   = kpis.get("ls", {})
    at   = kpis.get("atelier", {})

    def kv(l, v): return f"<tr><td>{_e(l)}</td><td>{v}</td></tr>"

    lsr = "".join([kv("CA HT", _eur(ls.get("ca"))), kv("Obj. CA", _eur(ls.get("ca_obj"))),
                   kv("Évo. vs N-1", _pct(ls.get("ca_evo"),True)),
                   kv("Marge", _pct(ls.get("marge"))),
                   kv("Évo. Marge", _pct(ls.get("marge_evo"),True)+" pts"),
                   kv("Fréquentation", str(ls.get("freq") or "—")),
                   kv("Panier Moyen", _eur(ls.get("panier"),1))])
    atr = "".join([kv("CA HT", _eur(at.get("ca"))), kv("Obj. CA", _eur(at.get("ca_obj"))),
                   kv("Évo. vs N-1", _pct(at.get("ca_evo"),True)),
                   kv("Marge", _pct(at.get("marge"))),
                   kv("Évo. Marge", _pct(at.get("marge_evo"),True)+" pts"),
                   kv("Nb OR", str(at.get("nb_or") or "—")),
                   kv("Panier Moyen", _eur(at.get("panier"),1))])

    body = (f'<div class="dashboard">'
            f'{_header(f"S{w}", "Revue Mensuelle · Global")}'
            f'<main class="main-content" style="grid-column:1/-1">'
            f'{_raf_html(kpis)}'
            f'<div class="two-col">'
            f'<div class="card"><div class="card-header">'
            f'<span class="card-title">Libre Service — Mensuel</span></div>'
            f'<table class="kv-table">{lsr}</table></div>'
            f'<div class="card"><div class="card-header">'
            f'<span class="card-title">Atelier — Mensuel</span></div>'
            f'<table class="kv-table">{atr}</table></div>'
            f'</div></main></div>')
    return _wrap(body)


def build_monthly_ls_html(data: dict) -> str:
    kpis = data["kpis"]
    w    = kpis.get("week_num") or "?"
    ls   = kpis.get("ls", {})

    body = (f'<div class="dashboard">'
            f'{_header(f"S{w}", "Revue Mensuelle · Libre Service")}'
            f'{_ls_kpi_strip(ls)}'
            f'<main class="main-content">'
            f'{_familles_html(data["fam"])}'
            f'{_pneus_html(data["tires"], w)}'
            f'</main>'
            f'<aside class="sidebar">'
            f'{_staff_html(data["vendors"], w)}'
            f'{_actions_html(data["fam"], data["ratios"])}'
            f'</aside></div>')
    return _wrap(body)


def build_monthly_atelier_html(data: dict) -> str:
    kpis = data["kpis"]
    w    = kpis.get("week_num") or "?"
    at   = kpis.get("atelier", {})

    body = (f'<div class="dashboard">'
            f'{_header(f"S{w}", "Revue Mensuelle · Atelier")}'
            f'{_at_kpi_strip(at)}'
            f'<main class="main-content">'
            f'{_raf_html(kpis)}'
            f'{_ratios_html(data["ratios"], w)}'
            f'</main>'
            f'<aside class="sidebar">'
            f'{_staff_html(data["vendors"], w)}'
            f'{_actions_html(data["fam"], data["ratios"])}'
            f'</aside></div>')
    return _wrap(body)


def build_quarterly_html(data: dict) -> str:
    import glob as _g
    w = data["kpis"].get("week_num") or "?"
    qf = _g.glob(str(QUARTERLY_DIR / "*.csv"))

    q_block = (
        f'<div class="card"><ul style="list-style:none;padding:0">' +
        "".join(f'<li style="font-family:var(--font-mono);font-size:12px;padding:4px 0">{_e(f.split("/")[-1])}</li>' for f in qf) +
        '</ul></div>'
    ) if qf else (
        '<div class="card"><p class="no-data">⏳ Aucun fichier trimestriel dans '
        '<code>/app/trimestres/</code></p></div>'
    )

    body = (f'<div class="dashboard">'
            f'{_header(f"S{w}", "Analyse Trimestrielle")}'
            f'<main class="main-content" style="grid-column:1/-1">'
            f'{q_block}'
            f'{_ratios_html(data["ratios"], w)}'
            f'</main></div>')
    return _wrap(body)


# ════════════════════════════════════════════════════════════════════════════
# STREAMLIT SHELL
# ════════════════════════════════════════════════════════════════════════════

from engine import markdown_parser

@st.cache_data(ttl=300)
def load_data() -> dict:
    return markdown_parser.parse_latest_report()


data = load_data()

def _render(html: str, height: int) -> None:
    try:
        st.iframe(srcdoc=html, height=height, scrolling=False)
    except TypeError:
        import streamlit.components.v1 as _cv1
        _cv1.html(html, height=height, scrolling=False)

# ─── Sidebar navigation ───────────────────────────────────────────────────────
st.session_state.setdefault("view", "global")

with st.sidebar:
    st.markdown(
        '<div style="padding:20px 4px 4px;font-size:22px;font-weight:700;'
        'color:#78BE20;letter-spacing:-.01em">Feu Vert Annecy 203</div>'
        '<div style="font-size:11px;color:#6b7280;margin-bottom:8px;'
        'font-family:monospace">Tableau de bord</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size:10px;text-transform:uppercase;letter-spacing:.1em;'
        'color:#4b5563;font-weight:600;padding:12px 4px 6px">Périodes</div>',
        unsafe_allow_html=True,
    )

    hebdo_active = st.session_state.view in ("global", "ls", "atelier")
    if st.button("📋 Rapports hebdomadaires", use_container_width=True,
                 type="primary" if hebdo_active else "secondary", key="nav_hebdo"):
        st.session_state.view = "global"
        st.rerun()

    if hebdo_active:
        for label, view_id in [
            ("  🌍 Global centre",  "global"),
            ("  🛒 Libre Service",  "ls"),
            ("  🔧 Atelier",        "atelier"),
        ]:
            if st.button(label, use_container_width=True,
                         type="primary" if st.session_state.view == view_id else "secondary",
                         key=f"nav_{view_id}"):
                st.session_state.view = view_id
                st.rerun()

    mensuel_views = ("mensuel_global", "mensuel_ls", "mensuel_atelier")
    mensuel_active = st.session_state.view in mensuel_views
    if st.button("📅 Rapports mensuels", use_container_width=True,
                 type="primary" if mensuel_active else "secondary",
                 key="nav_mensuel"):
        st.session_state.view = "mensuel_global"
        st.rerun()

    if mensuel_active:
        for label, view_id in [
            ("  🌍 Global centre",  "mensuel_global"),
            ("  🛒 Libre Service",  "mensuel_ls"),
            ("  🔧 Atelier",        "mensuel_atelier"),
        ]:
            if st.button(label, use_container_width=True,
                         type="primary" if st.session_state.view == view_id else "secondary",
                         key=f"nav_{view_id}"):
                st.session_state.view = view_id
                st.rerun()

    if st.button("📊 Rapports trimestriels", use_container_width=True,
                 type="primary" if st.session_state.view == "trimestriel" else "secondary",
                 key="nav_trimestriel"):
        st.session_state.view = "trimestriel"
        st.rerun()

    st.markdown("---")
    if st.button("⟳ Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    all_errors = sum((v.get("errors", []) for v in data.values() if isinstance(v, dict)), [])
    if all_errors:
        with st.expander(f"⚠️ {len(all_errors)} avertissement(s)", expanded=False):
            for e in all_errors:
                st.warning(e)

# ─── Main content ─────────────────────────────────────────────────────────────
view = st.session_state.view
if view == "global":
    _render(build_global_html(data), height=2400)
elif view == "ls":
    _render(build_ls_html(data), height=2400)
elif view == "atelier":
    _render(build_atelier_html(data), height=2400)
elif view == "mensuel_global":
    _render(build_monthly_global_html(data), height=1100)
elif view == "mensuel_ls":
    _render(build_monthly_ls_html(data), height=2400)
elif view == "mensuel_atelier":
    _render(build_monthly_atelier_html(data), height=2400)
elif view == "trimestriel":
    _render(build_quarterly_html(data), height=900)
