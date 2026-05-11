"""
engine/markdown_parser.py
────────────────────────────────────────────────────────────────────────────
Parse the latest "Rapport hebdomadaire" markdown file and return the unified
data dict required by the dashboard.
"""

from __future__ import annotations

import re
import glob
import pathlib
import pandas as pd

REPORT_DIR = pathlib.Path("Rapport hebdomadaire")

def parse_euros(s):
    if pd.isna(s) or not isinstance(s, str):
        return s
    s = s.replace('€', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
    try:
        return float(s.replace(',', '.'))
    except:
        return None

def parse_pct_str(s):
    if pd.isna(s) or not isinstance(s, str):
        return s
    s = s.replace('%', '').replace('pts', '').replace('+', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
    try:
        return float(s.replace(',', '.'))
    except:
        return None

def parse_int(s):
    if pd.isna(s) or not isinstance(s, str):
        return s
    s = s.replace('clts', '').replace(' ', '').replace('\xa0', '').replace('\u202f', '').strip()
    try:
        return int(s)
    except:
        return None

def extract_tables(content: str) -> list[pd.DataFrame]:
    # Extract markdown tables
    tables = re.findall(r'(\|[^\n]+\|\n)((?:\|[-:|\s]+\|\n)+)(\|[^\n]+\|\n(?:\|[^\n]+\|\n)*)', content)
    
    extracted = []
    for header, sep, body in tables:
        lines = [header.strip()] + [b.strip() for b in body.strip().split('\n')]
        data = []
        for line in lines:
            row = [cell.strip() for cell in line.split('|')[1:-1]]
            data.append(row)
        
        df = pd.DataFrame(data[1:], columns=data[0])
        extracted.append(df)
    
    return extracted

def parse_latest_report() -> dict:
    _week_re = re.compile(r"semaine (\d+)")
    files = sorted(glob.glob(str(REPORT_DIR / "*.md")),
                   key=lambda f: int(m.group(1)) if (m := _week_re.search(f.lower())) else 0,
                   reverse=True)
    
    if not files:
        return {"kpis": {"available": False}, "fam": {"available": False}, "tires": {"available": False}, "ratios": {"available": False}, "vendors": {"available": False}, "defects": {"available": False}}
    
    latest_file = files[0]
    content = pathlib.Path(latest_file).read_text(encoding='utf-8')
    
    week_match = re.search(r"semaine (\d+)", latest_file.lower())
    week_num = int(week_match.group(1)) if week_match else None
    
    tables = extract_tables(content)
    
    # Extract Brief Global text
    brief_match = re.search(r'\*\*Vision Globale\s*:\*\*\s*(.+?)(?=\n---|\n##|\Z)', content, re.DOTALL)
    brief_text = brief_match.group(1).strip() if brief_match else None

    # Extract period string from header line
    period_match = re.search(r'\*\*Période\s*:\*\*\s*(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})', content)
    period_str = f"{period_match.group(1)} – {period_match.group(2)}" if period_match else None

    # Section 8 — RH
    rh_data = {"available": False, "alerte": [], "absence": [], "recrutement": []}
    rh_sec = re.search(r'## 8\. RH\s*\n([\s\S]+?)(?=\n---|\Z)', content)
    if rh_sec:
        rh_text = rh_sec.group(1)
        rh_data["available"] = True
        for key, pat in [
            ("alerte",      r'### 8\.1[^\n]+\n((?:> [^\n]*\n?)+)'),
            ("absence",     r'### 8\.2[^\n]+\n((?:> [^\n]*\n?)+)'),
            ("recrutement", r'### 8\.3[^\n]+\n((?:> [^\n]*\n?)+)'),
        ]:
            m = re.search(pat, rh_text)
            if m:
                rh_data[key] = [ln.lstrip('> ').strip() for ln in m.group(1).strip().split('\n') if ln.strip()]

    # Bullet-point notes (familles + pneus key points)
    def _bullets(pat):
        m = re.search(pat, content, re.DOTALL)
        if not m:
            return []
        return [re.sub(r'\*+', '', ln.lstrip('*- ')).strip()
                for ln in m.group(1).split('\n')
                if ln.strip() and ln.strip()[0] in ('*', '-')]

    notes_fam  = _bullets(r"### Points clés de l'analyse par famille\s*\n([\s\S]+?)(?=\n###|\n##|\n---)")
    notes_pneu = _bullets(r"### Points clés de l'analyse pneus\s*\n([\s\S]+?)(?=\n###|\n##|\n---)")

    # Action plans (numbered lists → list of {title, obj} dicts)
    def _plan_items(pat):
        m = re.search(pat, content, re.DOTALL)
        if not m:
            return []
        items, cur = [], None
        for ln in m.group(1).split('\n'):
            ln = ln.strip()
            nm = re.match(r'^\d+\.\s+\*\*(.+?)\*\*', ln)
            if nm:
                cur = {"title": nm.group(1), "obj": ""}
                items.append(cur)
            elif cur and ln.startswith('- ') and 'Objectif' in ln:
                cur["obj"] = re.sub(r'\*(.+?)\*', r'\1', ln.lstrip('- '))
        return items

    plan_ls = _plan_items(r"### Plan d'Action Libre Service[^\n]*\n([\s\S]+?)(?=\n### |\n## |\n---|\Z)")
    plan_at = _plan_items(r"### Plan d'Action Atelier[^\n]*\n([\s\S]+?)(?=\n### |\n## |\n---|\Z)")

    kpis = {"available": True, "week_num": week_num, "brief": brief_text, "period_str": period_str, "global": {}, "ls": {}, "atelier": {}, "mtd": {}, "period": (None, None)}
    fam = {"available": True, "df": pd.DataFrame(), "margin_alerts": [], "top_losers": []}
    tires = {"available": True, "summary": {}, "season_df": pd.DataFrame(), "category_mix_df": pd.DataFrame()}
    ratios = {"available": True, "df": pd.DataFrame()}
    vendors = {"available": True, "df": pd.DataFrame()}
    defects = {"available": True, "df": pd.DataFrame()}
    tire_brands = {"available": False, "df": pd.DataFrame()}

    for df in tables:
        cols = df.columns.tolist()
        
        # Chiffres Globaux
        if "Indicateur" in cols and "Réalisé (N)" in cols and not "RAF" in cols:
            for _, r in df.iterrows():
                if "CA TTC Total" in r["Indicateur"]:
                    kpis["global"]["ca_ht"] = parse_euros(r["Réalisé (N)"])
                    kpis["global"]["ca_obj_ht"] = parse_euros(r["Objectif"])
                    kpis["global"]["ca_evo"] = parse_pct_str(r["Évolution / N-1"])
                    kpis["global"]["ca_ecart"] = parse_pct_str(r["Écart / Obj"])
                elif "Marge Brute" in r["Indicateur"]:
                    kpis["global"]["marge"] = parse_pct_str(r["Réalisé (N)"])
                    kpis["global"]["marge_obj"] = parse_pct_str(r["Objectif"])
                    kpis["global"]["marge_evo"] = parse_pct_str(r["Évolution / N-1"])
                    kpis["global"]["marge_ecart"] = parse_pct_str(r["Écart / Obj"])
                elif "Fréquentation" in r["Indicateur"]:
                    kpis["global"]["freq"] = parse_int(r["Réalisé (N)"])
                    kpis["global"]["freq_n1"] = parse_int(r["N-1"])
                    kpis["global"]["freq_evo"] = parse_pct_str(r["Évolution / N-1"])
                elif "Panier Moyen" in r["Indicateur"]:
                    kpis["global"]["panier"] = parse_euros(r["Réalisé (N)"])
                    kpis["global"]["panier_evo"] = parse_pct_str(r["Évolution / N-1"])
        
        # LS & Atelier
        elif "Métrique" in cols:
            for _, r in df.iterrows():
                if "CA TTC Magasin" in r["Métrique"]:
                    kpis["ls"]["ca"] = parse_euros(r["Réalisé (N)"])
                    kpis["ls"]["ca_obj"] = parse_euros(r["Objectif"])
                    kpis["ls"]["ca_evo"] = parse_pct_str(r["Évolution"])
                elif "Marge Magasin" in r["Métrique"]:
                    kpis["ls"]["marge"] = parse_pct_str(r["Réalisé (N)"])
                    kpis["ls"]["marge_evo"] = parse_pct_str(r["Évolution"])
                elif "Panier Moyen LS" in r["Métrique"]:
                    kpis["ls"]["panier"] = parse_euros(r["Réalisé (N)"])
                    kpis["ls"]["panier_n1"] = parse_euros(r["N-1"])
                    kpis["ls"]["panier_evo"] = parse_pct_str(r["Évolution"])
                elif "CA TTC Atelier" in r["Métrique"]:
                    kpis["atelier"]["ca"] = parse_euros(r["Réalisé (N)"])
                    kpis["atelier"]["ca_obj"] = parse_euros(r["Objectif"])
                    kpis["atelier"]["ca_evo"] = parse_pct_str(r["Évolution"])
                elif "Marge Atelier" in r["Métrique"]:
                    kpis["atelier"]["marge"] = parse_pct_str(r["Réalisé (N)"])
                    kpis["atelier"]["marge_evo"] = parse_pct_str(r["Évolution"])
                elif "Nombre d'OR" in r["Métrique"]:
                    kpis["atelier"]["nb_or"] = parse_int(r["Réalisé (N)"])
                    kpis["atelier"]["nb_or_n1"] = parse_int(r["N-1"])
                    kpis["atelier"]["nb_or_evo"] = parse_pct_str(r["Évolution"])
                elif "Panier Moyen Atel." in r["Métrique"]:
                    kpis["atelier"]["panier"] = parse_euros(r["Réalisé (N)"])
                    kpis["atelier"]["panier_n1"] = parse_euros(r["N-1"])
                    kpis["atelier"]["panier_evo"] = parse_pct_str(r["Évolution"])

        # RAF
        elif "Indicateur" in cols and "RAF" in cols:
            for _, r in df.iterrows():
                if "CA" in r["Indicateur"]:
                    kpis["mtd"]["ca"] = parse_euros(r["Réalisé (N)"])
                    kpis["mtd"]["ca_obj"] = parse_euros(r["Objectif"])
                    kpis["mtd"]["ca_pct"] = parse_pct_str(r["% Réalisé"])
                    kpis["mtd"]["ca_raf"] = parse_euros(r["RAF"])
                elif "Marge" in r["Indicateur"]:
                    kpis["mtd"]["marge_eur"] = parse_euros(r["Réalisé (N)"])
                    kpis["mtd"]["marge_obj"] = parse_euros(r["Objectif"])
                    kpis["mtd"]["marge_pct"] = parse_pct_str(r["% Réalisé"])
                    kpis["mtd"]["marge_raf"] = parse_euros(r["RAF"])
                elif "Contrat" in r["Indicateur"]:
                    kpis["mtd"]["contrats"] = parse_int(r["Réalisé (N)"])

        # Familles
        elif "Famille" in cols and "CA n (€)" in cols:
            df_fam = df.copy()
            df_fam["CA N (€)"] = df_fam["CA n (€)"].apply(parse_euros)
            df_fam["Évo. CA (%)"] = df_fam["Evol. CA (%)"].apply(parse_pct_str)
            df_fam["Δ Marge (pts)"] = df_fam["Marge +/- (pts)"].apply(parse_pct_str)
            df_fam["Marge N (%)"] = df_fam["Marge n (%)"].apply(parse_pct_str)
            df_fam["CA N-1 (€)"] = df_fam["CA n-1 (€)"].apply(parse_euros)
            df_fam["Qté N"] = df_fam["Qté n"].apply(parse_int)
            fam["df"] = df_fam
            
            valid = df_fam[df_fam["Évo. CA (%)"].notna()]
            fam["top_gainers"] = valid.nlargest(3, "Évo. CA (%)").to_dict("records")
            fam["top_losers"] = valid.nsmallest(3, "Évo. CA (%)").to_dict("records")
            fam["margin_alerts"] = df_fam[
                df_fam["Δ Marge (pts)"].notna() & (df_fam["Δ Marge (pts)"] < -5)
            ].to_dict("records")

        # Pneus Saison et Catégorie
        elif "Saison" in cols and "Catégorie" in cols and "PdM %" in cols:
            df_tires = df.copy()
            df_tires["Qté"] = df_tires["Qté"].apply(parse_int)
            df_tires["CA (€)"] = df_tires["CA (€)"].apply(parse_euros)
            df_tires["Marge (%)"] = df_tires["Marge %"].apply(parse_pct_str)
            df_tires["Évo. CA (%)"] = df_tires["Évo CA %"].apply(parse_pct_str)
            
            # extract category mix (sum qty over all PREMIUM, MEDIUM, BUDGET)
            valid_tires = df_tires[~df_tires["Catégorie"].isna() & (df_tires["Catégorie"] != "")]
            df_c = valid_tires.groupby("Catégorie")["Qté"].sum().reset_index()
            tires["category_mix_df"] = df_c
            
            # extract seasons
            rows = []
            for s in ["ÉTÉ", "4 SAISONS", "HIVER"]:
                total_row = df_tires[df_tires["Saison"].str.contains(f"Total {s}", na=False)]
                if not total_row.empty:
                    tr = total_row.iloc[0]
                    rows.append({
                        "Saison": s,
                        "Qté": tr["Qté"],
                        "CA (€)": tr["CA (€)"],
                        "Marge (%)": tr["Marge (%)"],
                        "Évo. CA (%)": tr["Évo. CA (%)"]
                    })
            tires["season_df"] = pd.DataFrame(rows)
            
            total_tires = df_tires[df_tires["Saison"].str.contains("TOTAL PNEUS", na=False)]
            if not total_tires.empty:
                tr = total_tires.iloc[0]
                tires["summary"] = {
                    "qty": tr["Qté"],
                    "ca": tr["CA (€)"],
                    "marge_pct": tr["Marge (%)"],
                }

        # Ratios
        elif "KPI Prioritaire" in cols and "Réalisé (N)" in cols:
            df_rat = df.copy()
            df_rat["KPI"] = df_rat["KPI Prioritaire"]
            df_rat["Réalisé (%)"] = df_rat["Réalisé (N)"].apply(parse_pct_str)
            df_rat["Objectif (%)"] = df_rat["Objectif"].apply(parse_pct_str)
            df_rat["Écart obj"] = df_rat["Écart"].apply(parse_pct_str)
            df_rat["Statut"] = df_rat["Statut"]
            ratios["df"] = df_rat

        # Vendors
        elif "Collaborateur LS" in cols:
            df_v = df.copy()
            df_v["Vendeur"] = df_v["Collaborateur LS"]
            for c in ["Garantie Pneu", "Géométrie", "VCR", "VCF", "Plaquette", "Dépoll."]:
                if c in df_v.columns:
                    df_v[c] = df_v[c].apply(parse_pct_str)
            vendors["df"] = df_v

        # Defects
        elif "Technicien" in cols and "Nb OR" in cols:
            df_d = df.copy()
            defects["df"] = df_d

        # Tire brands (Détail par Marque)
        elif "Catégorie" in cols and "Marque" in cols and "Qté" in cols:
            df_b = df.copy()
            df_b["Qté_n"]     = df_b["Qté"].apply(parse_int)
            df_b["CA_n"]      = df_b["CA (€)"].apply(parse_euros)
            df_b["Marge_pct"] = df_b["Marge %"].apply(parse_pct_str)
            df_b["Evo_pct"]   = df_b["Évo CA %"].apply(parse_pct_str)
            tire_brands["df"]        = df_b
            tire_brands["available"] = True

    return {
        "kpis":        kpis,
        "fam":         fam,
        "tires":       tires,
        "ratios":      ratios,
        "vendors":     vendors,
        "defects":     defects,
        "tire_brands": tire_brands,
        "rh":          rh_data,
        "notes_fam":   notes_fam,
        "notes_pneu":  notes_pneu,
        "plan_ls":     plan_ls,
        "plan_at":     plan_at,
    }
