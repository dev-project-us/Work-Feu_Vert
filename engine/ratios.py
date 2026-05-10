"""
engine/ratios.py
────────────────────────────────────────────────────────────────────────────
Parse the Ratios_Atelier*.csv file to extract the 6 priority KPIs.

Teaching note:
  The file has 3 blocks separated by blank lines:
    Block 1 (header: libelleAbrege)  – store name + period
    Block 2 (header: libelleGroupe)  – OR volumes
    Block 3 (header: libelleUnivers) – ratio table (THIS is what we need)

  We scan for the 'libelleUnivers' header, then read until the next
  blank line.  Each data row has the ratio libellé at position [1].
  We match it against KPI_MAP to extract the 6 priority ratios.

Column mapping in the ratio block:
  [1]  textbox1     – full libellé
  [2]  objectif     – target (%)
  [5]  ratioN       – realised this week (%)
  [8]  ratioN_1     – realised N-1 (%)
  [9]  textbox130   – delta N vs N-1 (pts)

Entry point:
  parse_ratios(folder=RATIOS_DIR) -> dict with keys:
    df, errors, available
"""

from __future__ import annotations

import csv
import glob
import pathlib
from datetime import datetime
from typing import Optional

import pandas as pd

from engine.utils import RATIOS_DIR, parse_pct, read_raw

# Maps CSV libellé → display name (Section 4 label)
KPI_MAP = {
    "Garantie Pneu / Pneus vendus":                 "Garantie Pneu",
    "Géométrie / Pose Pneu":                        "Géométrie",
    "Liquide de refroidissement / Nb OR":           "VCR (Refroid.)",
    "Liquide de frein / Nb OR":                     "VCF (Frein)",
    "Plaquette / Nb OR":                            "Plaquette",
    "Traitements dépollution moteurs / Nb Vidange": "Dépollution",
}

KPI_OBJECTIVES = {
    "Garantie Pneu":   50.0,
    "Géométrie":       19.0,
    "VCR (Refroid.)":  7.0,
    "VCF (Frein)":     11.0,
    "Plaquette":       11.0,
    "Dépollution":     35.0,
}

KPI_ORDER = list(KPI_OBJECTIVES.keys())


def parse_ratios(folder: pathlib.Path = RATIOS_DIR) -> dict:
    """
    Parse the ratios CSV and return a DataFrame with the 6 priority KPIs.
    Never raises – errors go into result['errors'].
    """
    errors: list[str] = []
    result = {
        "df":        pd.DataFrame(),
        "period":    "",
        "week_num":  None,
        "errors":    errors,
        "available": False,
    }

    csv_files = glob.glob(str(folder / "*.csv"))
    fichier_ratios: Optional[str] = None
    for f in csv_files:
        content = read_raw(f)
        if "libelleUnivers" in content:
            fichier_ratios = f
            break

    if not fichier_ratios:
        errors.append("⚠️  Aucun fichier Ratios_Atelier*.csv dans /app/resources/ratios prioritaires/")
        return result

    content = read_raw(fichier_ratios)
    lines   = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    # Extract period from line 2: "ANNECY 2,16/03/2026-22/03/2026"
    try:
        meta     = next(csv.reader([lines[1]]))
        period_s = meta[1].strip()
        date_fin = datetime.strptime(period_s.split("-")[1].strip(), "%d/%m/%Y")
        result["period"]   = period_s
        result["week_num"] = date_fin.isocalendar()[1]
    except Exception:
        pass

    # Parse the libelleUnivers ratio block
    raw: dict[str, dict] = {}
    in_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("libelleUnivers"):
            in_block = True
            continue
        if in_block:
            if not stripped:
                break
            try:
                parts = next(csv.reader([stripped]))
            except StopIteration:
                continue
            if len(parts) < 9:
                continue
            libelle = parts[1].strip()
            if libelle in KPI_MAP:
                raw[KPI_MAP[libelle]] = {
                    "objectif": parse_pct(parts[2]),
                    "realise":  parse_pct(parts[5]),
                    "n1":       parse_pct(parts[8]),
                    "ecart_n1": parse_pct(parts[9]) if len(parts) > 9 else None,
                }

    # Build ordered DataFrame
    rows = []
    for kpi_name in KPI_ORDER:
        obj_default = KPI_OBJECTIVES[kpi_name]
        d = raw.get(kpi_name, {})
        realise  = d.get("realise")
        objectif = d.get("objectif") or obj_default
        ecart_obj = round(realise - objectif, 1) if (realise is not None) else None
        ok = (realise is not None) and (realise >= objectif)
        rows.append({
            "KPI":          kpi_name,
            "Réalisé (%)":  realise,
            "Objectif (%)": objectif,
            "Écart obj":    ecart_obj,
            "N-1 (%)":      d.get("n1"),
            "Écart N-1":    d.get("ecart_n1"),
            "Statut":       "🟢" if ok else "🔴" if realise is not None else "⚪",
        })

    result["df"]        = pd.DataFrame(rows)
    result["available"] = True
    return result
