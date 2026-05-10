"""
app.py — Feu Vert Annecy · Live Dashboard
────────────────────────────────────────────────────────────────────────────
Entry point for the Streamlit application.

Architecture:
  • All CSV parsing is in engine/ modules (no Streamlit imports there).
  • This file handles only UI rendering.
  • @st.cache_data(ttl=300) refreshes data every 5 minutes automatically.

Run locally:  streamlit run app.py
In Docker:    docker-compose up  (see docker-compose.yml)
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

# ── Page config (must be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="Feu Vert Annecy — Dashboard",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Engine imports ────────────────────────────────────────────────────────────
from engine import defects, families, global_stats, ratios, tires, vendor_ratios
from engine.utils import QUARTERLY_DIR, fmt_eur, fmt_pct, status_from_evo

# ── Global CSS overrides (complement .streamlit/config.toml) ─────────────────
st.markdown(
    """
    <style>
    /* Hide default Streamlit top bar padding */
    .block-container { padding-top: 1.5rem; }

    /* Metric cards — accent the delta color */
    [data-testid="stMetricDelta"] svg { display: none; }
    [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; }

    /* Tabs — active tab uses accent green */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #78BE20 !important;
        color: #111827 !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"] { border-radius: 4px !important; }

    /* DataFrames — compact header */
    thead tr th { font-size: 12px !important; white-space: nowrap; }
    tbody tr td { font-size: 12px !important; }

    /* Section titles */
    .section-title {
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .08em;
        color: #9ca3af;
        margin-bottom: .5rem;
    }

    /* Progress bar label container */
    .raf-item { margin-bottom: .6rem; }
    .raf-label {
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        margin-bottom: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Data loading (cached for 5 minutes) ─────────────────────────────────────

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
kpis = data["kpis"]

# ── Header ────────────────────────────────────────────────────────────────────
week_label = ""
if kpis.get("period") and kpis["period"][0]:
    d0, d1 = kpis["period"]
    week_label = f"S{kpis['week_num']} · {d0.strftime('%d/%m')} – {d1.strftime('%d/%m/%Y')}"

col_logo, col_title, col_refresh = st.columns([1, 8, 2])
with col_logo:
    st.markdown(
        '<div style="background:#78BE20;color:#111827;font-weight:700;font-size:22px;'
        'width:48px;height:48px;border-radius:8px;display:flex;align-items:center;'
        'justify-content:center;">FV</div>',
        unsafe_allow_html=True,
    )
with col_title:
    st.markdown(
        f'<h1 style="margin:0;font-size:22px;font-weight:700;">Feu Vert Annecy</h1>'
        f'<p style="margin:0;color:#9ca3af;font-size:13px;font-family:monospace;">'
        f'Briefing Hebdomadaire &nbsp;·&nbsp; {week_label}</p>',
        unsafe_allow_html=True,
    )
with col_refresh:
    if st.button("⟳ Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.divider()

# ── Error banner ─────────────────────────────────────────────────────────────
all_errors = (
    kpis.get("errors", [])
    + data["fam"].get("errors", [])
    + data["tires"].get("errors", [])
    + data["ratios"].get("errors", [])
    + data["vendors"].get("errors", [])
    + data["defects"].get("errors", [])
)
if all_errors:
    with st.expander("⚠️  Données manquantes — détails", expanded=not kpis["available"]):
        for err in all_errors:
            st.warning(err)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_weekly, tab_monthly, tab_quarterly = st.tabs(
    ["📋  Briefing Hebdomadaire", "📅  Revue Mensuelle", "📊  Analyse Trimestrielle"]
)


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — WEEKLY BRIEFING
# ════════════════════════════════════════════════════════════════════════════
with tab_weekly:
    if not kpis["available"]:
        st.info("⏳  En attente des fichiers CSV de la semaine dans `/app/resources/SUC/`")
        st.stop()

    g  = kpis["global"]
    ls = kpis["ls"]
    at = kpis["atelier"]

    # ── KPI strip (6 metrics) ────────────────────────────────────────────────
    st.markdown('<p class="section-title">📈 Performance Globale — Semaine</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    def _delta_str(val, suffix="%", sign=True) -> str:
        if val is None:
            return "N/A"
        prefix = "+" if sign and val >= 0 else ""
        return f"{prefix}{val:.1f} {suffix}"

    with c1:
        st.metric(
            "CA HT Total",
            fmt_eur(g.get("ca_ht")),
            _delta_str(g.get("ca_evo"), "%", True) + " vs N-1",
            delta_color="normal",
        )
        if g.get("ca_obj_ht"):
            st.caption(f"Obj. {fmt_eur(g['ca_obj_ht'])} · écart {_delta_str(g.get('ca_ecart'), '%')}")

    with c2:
        st.metric(
            "Marge Globale",
            fmt_pct(g.get("marge")),
            _delta_str(g.get("marge_evo"), "pts", True) + " vs N-1",
            delta_color="normal",
        )
        if g.get("marge_obj"):
            st.caption(f"Obj. {fmt_pct(g['marge_obj'])} · écart {_delta_str(g.get('marge_ecart'), 'pts')}")

    with c3:
        st.metric(
            "Fréquentation",
            f"{g.get('freq', 'N/A')}",
            _delta_str(g.get("freq_evo"), "%", True) + " vs N-1",
            delta_color="normal",
        )
        if g.get("freq_n1"):
            st.caption(f"N-1 : {g['freq_n1']} clients")

    with c4:
        st.metric(
            "Panier Moyen HT",
            fmt_eur(g.get("panier"), 1) if g.get("panier") else "N/A",
            None,
        )
        if g.get("panier") and g.get("ca_ht") and g.get("freq"):
            computed = round(g["ca_ht"] / g["freq"], 1)
            st.caption(f"({computed} € calculé)")

    with c5:
        st.metric(
            "CA Atelier HT",
            fmt_eur(at.get("ca")),
            _delta_str(at.get("ca_evo"), "%", True) + " vs N-1",
            delta_color="normal",
        )
        st.caption(f"{at.get('nb_or', '—')} OR · Marge {fmt_pct(at.get('marge'))}")

    with c6:
        st.metric(
            "CA Libre Service HT",
            fmt_eur(ls.get("ca")),
            _delta_str(ls.get("ca_evo"), "%", True) + " vs N-1",
            delta_color="normal",
        )
        st.caption(f"Panier {fmt_eur(ls.get('panier'), 1)} · Marge {fmt_pct(ls.get('marge'))}")

    st.divider()

    # ── Main layout: 2 columns (chart | sidebar) ────────────────────────────
    col_main, col_side = st.columns([3, 1], gap="large")

    # ── LEFT: Familles bar chart ─────────────────────────────────────────────
    with col_main:
        st.markdown('<p class="section-title">📦 Performance par Famille</p>', unsafe_allow_html=True)

        fam_data = data["fam"]
        if not fam_data["available"]:
            st.warning("Données familles indisponibles.")
        else:
            df_fam = fam_data["df"].copy()
            df_fam_sorted = df_fam.dropna(subset=["CA N (€)"]).sort_values("CA N (€)", ascending=False)

            # Colour each bar by growth direction
            def _bar_color(row):
                if row["Évo. CA (%)"] is None:
                    return "neutral"
                if row["Évo. CA (%)"] >= 0:
                    return "positive"
                return "negative"

            df_fam_sorted["Couleur"] = df_fam_sorted.apply(_bar_color, axis=1)
            color_map = {"positive": "#78BE20", "negative": "#ef4444", "neutral": "#6b7280"}

            fig = px.bar(
                df_fam_sorted,
                y="Famille",
                x="CA N (€)",
                color="Couleur",
                color_discrete_map=color_map,
                orientation="h",
                text=df_fam_sorted["Évo. CA (%)"].apply(
                    lambda v: f"{v:+.1f}%" if v is not None else ""
                ),
                height=420,
                template="plotly_dark",
            )
            fig.update_layout(
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=20, t=10, b=0),
                xaxis_title="CA HT (€)",
                yaxis_title="",
                font=dict(size=11),
                yaxis=dict(autorange="reversed"),
            )
            fig.update_traces(textposition="outside", textfont_size=10)
            st.plotly_chart(fig, use_container_width=True)

            # Detailed table below the chart
            with st.expander("Tableau détail familles"):
                display_df = df_fam[[
                    "Famille", "CA N (€)", "CA N-1 (€)", "Évo. CA (%)",
                    "Marge N (%)", "Δ Marge (pts)", "Qté N", "Statut"
                ]].copy()
                # Format for display
                display_df["CA N (€)"]    = display_df["CA N (€)"].apply(lambda v: f"{int(v):,} €".replace(",", " ") if pd.notna(v) else "—")
                display_df["CA N-1 (€)"]  = display_df["CA N-1 (€)"].apply(lambda v: f"{int(v):,} €".replace(",", " ") if pd.notna(v) else "—")
                display_df["Évo. CA (%)"] = display_df["Évo. CA (%)"].apply(lambda v: f"{v:+.1f} %" if pd.notna(v) else "—")
                display_df["Marge N (%)"] = display_df["Marge N (%)"].apply(lambda v: f"{v:.1f} %" if pd.notna(v) else "—")
                display_df["Δ Marge (pts)"] = display_df["Δ Marge (pts)"].apply(lambda v: f"{v:+.1f} pts" if pd.notna(v) else "—")
                st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.divider()

        # ── Pneus par Saison ─────────────────────────────────────────────────
        st.markdown('<p class="section-title">🔵 Analyse Pneus — S{}</p>'.format(
            kpis.get("week_num", "?")), unsafe_allow_html=True)

        tire_data = data["tires"]
        if not tire_data["available"]:
            st.warning("Données pneus indisponibles.")
        else:
            s = tire_data["summary"]
            st.caption(
                f"**Total semaine :** {s.get('qty', 0)} unités · "
                f"{fmt_eur(s.get('ca'))} · Marge {fmt_pct(s.get('marge_pct'))}"
            )

            t1, t2 = st.columns(2)

            with t1:
                st.markdown("**Par saison**")
                df_saison = tire_data["season_df"].copy()
                df_saison["CA (€)"]    = df_saison["CA (€)"].apply(lambda v: f"{int(v):,} €".replace(",", " ") if pd.notna(v) else "—")
                df_saison["Marge (%)"] = df_saison["Marge (%)"].apply(lambda v: f"{v:.1f} %" if pd.notna(v) else "—")
                df_saison["Évo. CA (%)"] = df_saison["Évo. CA (%)"].apply(lambda v: f"{v:+.1f} %" if pd.notna(v) else "—")
                st.dataframe(
                    df_saison[["Saison", "Qté", "CA (€)", "Évo. CA (%)", "Marge (%)", "Statut"]],
                    use_container_width=True, hide_index=True,
                )

            with t2:
                st.markdown("**Mix catégorie (toutes saisons)**")
                df_cat = tire_data["category_mix_df"].copy()
                df_cat["CA (€)"]    = df_cat["CA (€)"].apply(lambda v: f"{int(v):,} €".replace(",", " ") if pd.notna(v) else "—")
                df_cat["Marge (%)"] = df_cat["Marge (%)"].apply(lambda v: f"{v:.1f} %" if pd.notna(v) else "—")
                # Add share
                total_qty = df_cat["Qté"].sum()
                df_cat["Part (%)"] = df_cat["Qté"].apply(
                    lambda v: f"{v/total_qty*100:.1f} %" if total_qty else "—"
                )
                st.dataframe(
                    df_cat[["Catégorie", "Qté", "Part (%)", "CA (€)", "Marge (%)"]],
                    use_container_width=True, hide_index=True,
                )

            with st.expander("Détail marques ÉTÉ"):
                df_brands = tire_data["ete_brand_df"].copy()
                df_brands["CA (€)"]      = df_brands["CA (€)"].apply(lambda v: f"{int(v):,} €".replace(",", " ") if pd.notna(v) and v else "—")
                df_brands["Évo. CA (%)"] = df_brands["Évo. CA (%)"].apply(lambda v: f"{v:+.1f} %" if pd.notna(v) else "—")
                df_brands["Marge (%)"]   = df_brands["Marge (%)"].apply(lambda v: f"{v:.1f} %" if pd.notna(v) else "—")
                st.dataframe(
                    df_brands[["Catégorie","Marque","Qté","CA (€)","Évo. CA (%)","Marge (%)","Statut"]],
                    use_container_width=True, hide_index=True,
                )

    # ── RIGHT SIDEBAR: Ratios + Staff ────────────────────────────────────────
    with col_side:
        # Ratios Prioritaires
        st.markdown('<p class="section-title">⚙️ Ratios Prioritaires</p>', unsafe_allow_html=True)
        ratio_data = data["ratios"]
        if not ratio_data["available"]:
            st.warning("Données ratios indisponibles.")
        else:
            df_r = ratio_data["df"]
            for _, row in df_r.iterrows():
                realise  = row["Réalisé (%)"]
                objectif = row["Objectif (%)"]
                ecart    = row["Écart obj"]
                ok       = row["Statut"] == "🟢"

                label_color = "#78BE20" if ok else "#ef4444"
                ecart_str   = f"{ecart:+.1f} pts" if ecart is not None else "—"

                st.markdown(
                    f'<div class="raf-item">'
                    f'<div class="raf-label">'
                    f'<span style="font-size:12px;font-weight:500;">{row["Statut"]} {row["KPI"]}</span>'
                    f'<span style="font-family:monospace;font-size:11px;color:{label_color};">'
                    f'{fmt_pct(realise)} <span style="color:#6b7280;">/ {fmt_pct(objectif)}</span>'
                    f'</span></div></div>',
                    unsafe_allow_html=True,
                )
                pct_bar = min(100, int((realise or 0) / objectif * 100)) if objectif else 0
                st.progress(pct_bar / 100)
                st.caption(f"Écart obj. : {ecart_str}")

        st.divider()

        # Staff LS
        st.markdown('<p class="section-title">👥 Vendeurs LS — Ratios</p>', unsafe_allow_html=True)
        vendor_data = data["vendors"]
        if not vendor_data["available"]:
            st.warning("Données vendeurs indisponibles.")
        else:
            df_v = vendor_data["df"].copy()

            # Colour values using background gradient: green if ≥ obj, red if < obj
            OBJ_MAP = {
                "Garantie Pneu": 50.0, "Géométrie": 19.0,
                "VCR": 7.0, "VCF": 11.0, "Plaquette": 11.0, "Dépoll.": 35.0,
            }

            def _fmt_cell(val, obj):
                if val is None or pd.isna(val):
                    return "—"
                color = "#78BE20" if val >= obj else "#ef4444"
                return f'<span style="color:{color};font-weight:600;">{val:.1f}%</span>'

            # Build HTML table
            cols = list(OBJ_MAP.keys())
            html = '<table style="width:100%;font-size:11px;border-collapse:collapse;">'
            html += "<thead><tr>"
            html += '<th style="text-align:left;padding:4px 4px;color:#9ca3af;">Vendeur</th>'
            for c in cols:
                abbr = c[:3] if len(c) > 6 else c
                html += f'<th style="text-align:center;padding:4px 2px;color:#9ca3af;">{abbr}</th>'
            html += "</tr></thead><tbody>"
            for _, row in df_v.iterrows():
                html += f'<tr><td style="padding:4px 4px;font-weight:500;">{row["Vendeur"]}</td>'
                for c in cols:
                    html += f'<td style="text-align:center;padding:4px 2px;">{_fmt_cell(row.get(c), OBJ_MAP[c])}</td>'
                html += "</tr>"
            html += "</tbody></table>"
            st.markdown(html, unsafe_allow_html=True)
            st.caption("Vert ≥ objectif · Rouge < objectif · GP=Garantie Pneu · Dép.=Dépollution")

        st.divider()

        # Atelier Défectuosité
        st.markdown('<p class="section-title">🔧 Atelier — Défectuosité</p>', unsafe_allow_html=True)
        def_data = data["defects"]
        if not def_data["available"]:
            st.warning("Données défectuosité indisponibles.")
        else:
            df_def = def_data["df"]
            # Show compact table (Technicien + key columns)
            key_cols = ["Technicien", "Nb OR", "Batterie", "VCR", "VCF", "BEG", "Amort."]
            available_cols = [c for c in key_cols if c in df_def.columns]
            st.dataframe(
                df_def[available_cols],
                use_container_width=True, hide_index=True,
            )
            with st.expander("Tableau complet"):
                st.dataframe(df_def, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — MONTHLY REVIEW
# ════════════════════════════════════════════════════════════════════════════
with tab_monthly:
    mtd = kpis.get("mtd", {})

    if not mtd:
        st.info("⏳  En attente des fichiers CSV MTD dans `/app/resources/SUC/`")
    else:
        st.markdown('<p class="section-title">📅 Reste à Faire — Mois en Cours</p>', unsafe_allow_html=True)

        # ── RAF progress cards ────────────────────────────────────────────────
        def _raf_card(label, current, objective, pct, raf, unit="€"):
            if pct is None:
                color = "#6b7280"
                bar_v = 0
            elif pct >= 100:
                color = "#78BE20"
                bar_v = 1.0
            elif pct >= 85:
                color = "#f59e0b"
                bar_v = pct / 100
            else:
                color = "#ef4444"
                bar_v = pct / 100

            raf_str = (
                fmt_eur(raf) if unit == "€" and raf is not None
                else f"{raf}" if raf is not None else "—"
            )
            current_str = fmt_eur(current) if unit == "€" else f"{current}"
            obj_str     = fmt_eur(objective) if unit == "€" else f"{objective}"

            st.markdown(
                f'<div style="background:#1f2937;border-radius:8px;padding:16px 20px;'
                f'margin-bottom:8px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="font-size:13px;font-weight:600;">{label}</span>'
                f'<span style="font-family:monospace;font-size:14px;color:{color};">'
                f'{pct:.1f} %</span></div>'
                f'<div style="margin:8px 0;background:#374151;border-radius:4px;height:6px;">'
                f'<div style="background:{color};width:{bar_v*100:.1f}%;height:100%;'
                f'border-radius:4px;"></div></div>'
                f'<div style="display:flex;justify-content:space-between;font-size:11px;'
                f'color:#9ca3af;font-family:monospace;">'
                f'<span>Réalisé : {current_str}</span>'
                f'<span>Obj : {obj_str}</span>'
                f'<span style="color:{color};">RAF : {raf_str}</span>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

        col_raf1, col_raf2 = st.columns(2)

        with col_raf1:
            _raf_card(
                "Chiffre d'Affaires",
                mtd.get("ca"), mtd.get("ca_obj"),
                mtd.get("ca_pct"), mtd.get("ca_raf"),
            )
            _raf_card(
                "Marge €",
                mtd.get("marge_eur"), mtd.get("marge_obj"),
                mtd.get("marge_pct"), mtd.get("marge_raf"),
            )

        with col_raf2:
            # Contrats — no RAF "amount" just count
            contrats = mtd.get("contrats")
            st.metric("Contrats Entretien (MTD)", contrats or "—", None)
            st.caption("Objectif mensuel non fourni dans ce fichier CSV")

        st.divider()

        # ── LS vs Atelier dissociation ────────────────────────────────────────
        st.markdown('<p class="section-title">⚖️ LS vs Atelier — Semaine</p>', unsafe_allow_html=True)
        ls  = kpis["ls"]
        at  = kpis["atelier"]

        col_ls, col_at = st.columns(2)
        with col_ls:
            st.markdown("**Libre Service**")
            ls_rows = [
                ("CA HT",        fmt_eur(ls.get("ca"))),
                ("Obj. CA HT",   fmt_eur(ls.get("ca_obj"))),
                ("Évo. vs N-1",  fmt_pct(ls.get("ca_evo"), sign=True)),
                ("Marge",        fmt_pct(ls.get("marge"))),
                ("Évo. Marge",   fmt_pct(ls.get("marge_evo"), sign=True) + " pts"),
                ("Fréquentation",f"{ls.get('freq', '—')}"),
                ("Panier Moyen", fmt_eur(ls.get("panier"), 1)),
            ]
            st.table(pd.DataFrame(ls_rows, columns=["Indicateur", "Valeur"]))

        with col_at:
            st.markdown("**Atelier**")
            at_rows = [
                ("CA HT",        fmt_eur(at.get("ca"))),
                ("Obj. CA HT",   fmt_eur(at.get("ca_obj"))),
                ("Évo. vs N-1",  fmt_pct(at.get("ca_evo"), sign=True)),
                ("Marge",        fmt_pct(at.get("marge"))),
                ("Évo. Marge",   fmt_pct(at.get("marge_evo"), sign=True) + " pts"),
                ("Nb OR",        f"{at.get('nb_or', '—')}"),
                ("Évo. OR",      fmt_pct(at.get("nb_or_evo"), sign=True)),
                ("Panier Moyen", fmt_eur(at.get("panier"), 1)),
            ]
            st.table(pd.DataFrame(at_rows, columns=["Indicateur", "Valeur"]))


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — QUARTERLY ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
with tab_quarterly:
    st.markdown('<p class="section-title">📊 Analyse Trimestrielle</p>', unsafe_allow_html=True)

    # Check for quarterly CSV files
    import glob as _glob
    q_files = _glob.glob(str(QUARTERLY_DIR / "*.csv"))

    if not q_files:
        st.info(
            "⏳  Aucun fichier trimestriel détecté dans `/app/trimestres/`.\n\n"
            "Déposez vos exports CSV SUC trimestriels dans ce dossier pour activer cet onglet."
        )
    else:
        st.success(f"{len(q_files)} fichier(s) trimestriel(s) détecté(s).")
        st.markdown(
            "**Les données trimestrielles sont disponibles.**  "
            "Cet onglet affichera les agrégats Q1/Q2/Q3/Q4 dès que les parsers "
            "trimestriels seront connectés."
        )
        # Display file list for transparency
        with st.expander("Fichiers disponibles"):
            for f in q_files:
                st.text(f.split("/")[-1])

    # Always show ratios trends across weeks
    st.divider()
    st.markdown('<p class="section-title">📈 Tendance Ratios (semaine courante)</p>', unsafe_allow_html=True)

    ratio_data = data["ratios"]
    if ratio_data["available"]:
        df_r = ratio_data["df"]
        fig_r = px.bar(
            df_r,
            x="KPI",
            y=["Réalisé (%)", "Objectif (%)"],
            barmode="group",
            color_discrete_map={"Réalisé (%)": "#78BE20", "Objectif (%)": "#6b7280"},
            template="plotly_dark",
            height=350,
            title="Ratios Prioritaires : Réalisé vs Objectif",
        )
        fig_r.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend_title_text="",
            margin=dict(l=0, r=0, t=40, b=0),
        )
        st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.warning("Données ratios indisponibles pour le graphique de tendance.")
