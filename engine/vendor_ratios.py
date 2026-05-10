"""
engine/vendor_ratios.py
────────────────────────────────────────────────────────────────────────────
Parse the 'Suivi Individuel des ratios atelier' CSV.

Teaching note:
  The file has 5 blocks separated by blank lines (matching 4 PDF pages).
  We need 3 of them:
    BLOC 1  (header: textbox3,...)    – Garantie Pneu & Géométrie
    BLOC 2  (header: textbox590,...)  – VCR, Plaquette, VCF
    BLOC 4  (header: textbox326,...)  – Dépollution (NCI)

  Each block contains one row per vendeur.
  Name positions differ per block (see column docs below).

  IMPORTANT: In Bloc 1, the GP/Géo columns sometimes shift by 1 position
  depending on how many tyre lines a vendeur has. We detect this by checking
  whether the extracted value contains '%'; if not, we try position+1.

Entry point:
  parse_vendor_ratios(folder=SUIVI_DIR) -> dict with keys:
    df, errors, available
"""

from __future__ import annotations

import csv
import glob
import pathlib
from datetime import datetime
from typing import Optional

import pandas as pd

from engine.utils import SUIVI_DIR, parse_pct, read_raw

# Maps template display name → CSV raw name
NOM_MAP = {
    "Sandrine": "SANDRINE R.",
    "Paul":     "PAUL P.",
    "Kamilia":  "KAMILIA A.",
    "Chouaib":  "CHOUAIB G.",
    "Pauline":  "PAULINE R.",
    "Valentin": "VALENTIN C.",
}

KPI_OBJECTIVES = {
    "Garantie Pneu": 50.0,
    "Géométrie":     19.0,
    "VCR":           7.0,
    "VCF":           11.0,
    "Plaquette":     11.0,
    "Dépoll.":       35.0,
}


def _pct_or_fallback(row: list[str], pos: int, fallback: int) -> str:
    """
    Try to get a % value at `pos`.  If it doesn't contain '%', try `fallback`.
    This handles the occasional column shift in Bloc 1.
    """
    val = row[pos].strip() if len(row) > pos else ""
    if "%" not in val and len(row) > fallback:
        val = row[fallback].strip()
    return val


def parse_vendor_ratios(folder: pathlib.Path = SUIVI_DIR) -> dict:
    """
    Parse the suivi vendeur CSV and return a per-vendeur DataFrame.
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
    fichier: Optional[str] = None
    for f in csv_files:
        content = read_raw(f)
        if "textbox390" in content:
            fichier = f
            break

    if not fichier:
        errors.append("⚠️  Aucun fichier Suivi Individuel*.csv dans /app/resources/suivi vendeur/")
        return result

    content = read_raw(fichier)
    lines   = content.splitlines()

    # Extract period from line 2: "ANNECY 2,16/03/2026 - 22/03/2026"
    try:
        meta     = next(csv.reader([lines[1]]))
        period_s = meta[1].strip()
        date_fin = datetime.strptime(period_s.split(" - ")[1].strip(), "%d/%m/%Y")
        result["period"]   = period_s
        result["week_num"] = date_fin.isocalendar()[1]
    except Exception:
        pass

    # Initialise per-vendor storage (csv name → kpi values)
    vendeurs: dict[str, dict[str, str]] = {
        csv_name: {k: "" for k in KPI_OBJECTIVES}
        for csv_name in NOM_MAP.values()
    }

    # ── Bloc 1: Garantie Pneu & Géométrie ───────────────────────────────────
    try:
        b1 = next(i for i, l in enumerate(lines) if l.startswith("textbox3,"))
        i  = b1 + 1
        while i < len(lines) and lines[i].strip():
            row = next(csv.reader([lines[i]]))
            nom = row[8].strip() if len(row) > 8 else ""
            if nom in vendeurs:
                vendeurs[nom]["Garantie Pneu"] = _pct_or_fallback(row, 22, 23)
                vendeurs[nom]["Géométrie"]     = _pct_or_fallback(row, 28, 29)
            i += 1
    except StopIteration:
        errors.append("⚠️  Bloc 1 (GP/Géo) introuvable dans le fichier suivi vendeur")

    # ── Bloc 2: VCR, Plaquette, VCF ─────────────────────────────────────────
    try:
        b2 = next(i for i, l in enumerate(lines) if l.startswith("textbox590,"))
        i  = b2 + 1
        while i < len(lines) and lines[i].strip():
            row = next(csv.reader([lines[i]]))
            nom = row[11].strip() if len(row) > 11 else ""
            if nom in vendeurs:
                vendeurs[nom]["VCR"]       = row[19].strip() if len(row) > 19 else ""
                vendeurs[nom]["Plaquette"] = row[21].strip() if len(row) > 21 else ""
                vendeurs[nom]["VCF"]       = row[23].strip() if len(row) > 23 else ""
            i += 1
    except StopIteration:
        errors.append("⚠️  Bloc 2 (VCR/VCF/Plaquette) introuvable dans le fichier suivi vendeur")

    # ── Bloc 4: Dépollution ──────────────────────────────────────────────────
    try:
        b4 = next(i for i, l in enumerate(lines) if l.startswith("textbox326,"))
        i  = b4 + 1
        while i < len(lines) and lines[i].strip():
            row = next(csv.reader([lines[i]]))
            nom = row[9].strip() if len(row) > 9 else ""
            if nom in vendeurs:
                vendeurs[nom]["Dépoll."] = row[17].strip() if len(row) > 17 else ""
            i += 1
    except StopIteration:
        errors.append("⚠️  Bloc 4 (Dépollution) introuvable dans le fichier suivi vendeur")

    # Build display DataFrame (template names, ordered)
    rows = []
    for display_name, csv_name in NOM_MAP.items():
        d    = vendeurs.get(csv_name, {})
        row  = {"Vendeur": display_name}
        for kpi, obj in KPI_OBJECTIVES.items():
            val_str = d.get(kpi, "")
            val     = parse_pct(val_str)
            row[kpi] = val
        rows.append(row)

    result["df"]        = pd.DataFrame(rows)
    result["available"] = True
    return result
