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
    initial_sidebar_state="collapsed",
)

# Remove Streamlit chrome so the iframe fills cleanly
st.markdown(
    "<style>.block-container{padding:0 !important;} "
    ".stApp{background:#111827;} "
    ".stTabs [data-baseweb='tab-list']{padding:0 24px;background:#111827;}"
    ".stTabs [data-baseweb='tab'][aria-selected='true']"
    "{background:#78BE20!important;color:#111827!important;font-weight:600;}"
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
      <h1 class="header-title">Feu Vert Annecy</h1>
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


def build_weekly_html(data: dict) -> str:
    kpis = data["kpis"]
    w    = kpis.get("week_num") or "?"
    p    = kpis.get("period") or (None, None)
    wl   = f"S{w}"
    ps   = (f"{p[0].strftime('%d/%m')} – {p[1].strftime('%d/%m/%Y')}"
            if p[0] and p[1] else "—")

    if not kpis.get("available"):
        body = (f'<div class="dashboard" style="grid-template-columns:1fr">'
                f'{_header(wl, "—")}'
                f'<div style="padding:48px;text-align:center;color:var(--muted);font-size:15px;">'
                f'⏳&nbsp; En attente des CSV dans <code>/app/resources/SUC/</code><br><br>'
                f'Dépose les exports dans <strong>inbox/</strong> et lance <code>./push_week.sh</code>'
                f'</div></div>')
    else:
        g  = kpis.get("global", {})
        ls = kpis.get("ls", {})
        at = kpis.get("atelier", {})
        body = (f'<div class="dashboard">'
                f'{_header(wl, ps)}'
                f'{_kpi_strip(g, ls, at)}'
                f'<main class="main-content">'
                f'{_familles_html(data["fam"])}'
                f'<div class="two-col">'
                f'{_pneus_html(data["tires"], w)}'
                f'{_raf_html(kpis)}'
                f'</div></main>'
                f'<aside class="sidebar">'
                f'{_ratios_html(data["ratios"], w)}'
                f'{_staff_html(data["vendors"], w)}'
                f'{_actions_html(data["fam"], data["ratios"])}'
                f'</aside></div>')
    return _wrap(body)


def build_monthly_html(data: dict) -> str:
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
            f'{_header(f"S{w}", "Revue Mensuelle")}'
            f'<main class="main-content" style="grid-column:1/-1">'
            f'{_raf_html(kpis)}'
            f'<div class="two-col">'
            f'<div class="card"><div class="card-header">'
            f'<span class="card-title">Libre Service — Semaine</span></div>'
            f'<table class="kv-table">{lsr}</table></div>'
            f'<div class="card"><div class="card-header">'
            f'<span class="card-title">Atelier — Semaine</span></div>'
            f'<table class="kv-table">{atr}</table></div>'
            f'</div></main></div>')
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

@st.cache_data(ttl=300)
def load_data() -> dict:
    return {
        "kpis":    global_stats.weekly_kpis(),
        "fam":     families.parse_families(),
        "tires":   tires.parse_tires(),
        "ratios":  ratios.parse_ratios(),
        "vendors": vendor_ratios.parse_vendor_ratios(),
        "defects": defects.parse_defects(),
    }


data = load_data()

# Minimal top bar: errors + refresh
all_errors = sum((v.get("errors",[]) for v in data.values() if isinstance(v,dict)),[])
col_e, col_b = st.columns([11, 1])
with col_e:
    if all_errors:
        with st.expander(f"⚠️ {len(all_errors)} avertissement(s)", expanded=False):
            for e in all_errors:
                st.warning(e)
with col_b:
    if st.button("⟳", help="Rafraîchir"):
        st.cache_data.clear()
        st.rerun()

tab1, tab2, tab3 = st.tabs([
    "📋  Briefing Hebdomadaire",
    "📅  Revue Mensuelle",
    "📊  Analyse Trimestrielle",
])

def _render(html: str, height: int) -> None:
    """Render an HTML string in an isolated iframe (Streamlit 1.35+)."""
    try:
        # st.iframe with srcdoc is the current API (replaces components.v1.html)
        st.iframe(srcdoc=html, height=height, scrolling=False)
    except TypeError:
        # Fallback for older Streamlit builds that don't accept srcdoc
        import streamlit.components.v1 as _cv1
        _cv1.html(html, height=height, scrolling=False)

with tab1:
    _render(build_weekly_html(data), height=2400)

with tab2:
    _render(build_monthly_html(data), height=1100)

with tab3:
    _render(build_quarterly_html(data), height=900)
