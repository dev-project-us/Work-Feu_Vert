"""
engine/families.py
────────────────────────────────────────────────────────────────────────────
Parse the comparatifCAv2_Famille*.csv file.

Teaching note:
  The file has 4 header lines before the actual data:
    Line 1: Store header  (LIBELLEMAGASIN, ...)
    Line 2: Store values  (ANNECY SEYNOD, ...)
    Line 3: Empty
    Line 4: Column names  (textbox48, ...)
    Line 5+: Data rows    (one row per article, families repeat)

  Strategy: skip the first 4 lines, then collect the FIRST row for each
  unique codeFamille (column index 14).

Column mapping (0-indexed):
  [14] codeFamille   – family code e.g. "A-ENTRETIEN"
  [15] CAHT_n_4      – CA HT realised N (€)
  [16] CAHT_n_1_1    – CA HT realised N-1 (€)
  [18] textbox57     – CA evolution % vs N-1
  [21] MARGE_n       – Margin rate N (%)
  [22] MARGE_n_1     – Margin rate N-1 (%)
  [26] textbox63     – Quantity N

Entry point:
  parse_families(folder=FAMILLES_DIR) -> dict with keys:
    df, top_gainers, top_losers, margin_alerts, errors, available
"""

from __future__ import annotations

import csv
import glob
import pathlib

import pandas as pd

from engine.utils import (
    FAMILLES_DIR, parse_pct, parse_int, clean, status_from_evo
)

TEMPLATE_FAMILIES = [
    "A-ENTRETIEN",
    "B-ELECTRICITE",
    "C-PIECES TECHNIQUES",
    "D-OUTILLAGE",
    "E-EQUIPEMENT EXTERIEUR",
    "F-EQUIPEMENT INTERIEUR",
    "G-AUTO SON",
    "H-LUBRIFIANTS",
    "I-PNEUMATIQUES",
    "J-2 ROUES",
    "U-SERVICES",
    "W-DIVERS",
    "X-TARIF MAIN D'OEUVRE",
]


def parse_families(folder: pathlib.Path = FAMILLES_DIR) -> dict:
    """
    Parse the famille CSV and return a unified result dict.
    Never raises – errors go into result['errors'].
    """
    errors: list[str] = []
    result = {
        "df": pd.DataFrame(),
        "top_gainers": [],
        "top_losers": [],
        "margin_alerts": [],
        "errors": errors,
        "available": False,
    }

    csv_files = glob.glob(str(folder / "comparatifCAv2_Famille*.csv"))
    if not csv_files:
        errors.append(
            "⚠️  Aucun fichier comparatifCAv2_Famille*.csv dans /app/resources/familles/"
        )
        return result

    # Read all lines; skip the 4-line preamble
    with open(csv_files[0], "r", encoding="utf-8-sig") as fh:
        lines = fh.readlines()

    seen: dict[str, dict] = {}
    for row in csv.reader(lines[4:]):
        if len(row) < 27:
            continue
        fam = row[14].strip()
        if not fam or fam in seen:
            continue  # keep first occurrence only
        seen[fam] = {
            "ca_n":     row[15].strip(),
            "ca_n1":    row[16].strip(),
            "evo_ca":   row[18].strip(),
            "marge_n":  row[21].strip(),
            "marge_n1": row[22].strip(),
            "qty_n":    row[26].strip(),
        }

    # Build a DataFrame row for every expected family
    rows = []
    for fam in TEMPLATE_FAMILIES:
        d = seen.get(fam)
        if d:
            ca_n    = parse_int(d["ca_n"])
            ca_n1   = parse_int(d["ca_n1"])
            evo     = parse_pct(d["evo_ca"])
            mg_n    = parse_pct(d["marge_n"])
            mg_n1   = parse_pct(d["marge_n1"])
            mg_delta = round(mg_n - mg_n1, 1) if (mg_n is not None and mg_n1 is not None) else None
            qty     = parse_int(d["qty_n"])
            statut  = status_from_evo(d["evo_ca"])
        else:
            ca_n = ca_n1 = evo = mg_n = mg_delta = qty = None
            statut = "⚪"

        rows.append({
            "Famille":       fam,
            "CA N (€)":      ca_n,
            "CA N-1 (€)":    ca_n1,
            "Évo. CA (%)":   evo,
            "Marge N (%)":   mg_n,
            "Δ Marge (pts)": mg_delta,
            "Qté N":         qty,
            "Statut":        statut,
        })

    df = pd.DataFrame(rows)
    result["df"]        = df
    result["available"] = True

    valid = df[df["Évo. CA (%)"].notna()]
    result["top_gainers"]   = valid.nlargest(3,  "Évo. CA (%)").to_dict("records")
    result["top_losers"]    = valid.nsmallest(3, "Évo. CA (%)").to_dict("records")
    result["margin_alerts"] = df[
        df["Δ Marge (pts)"].notna() & (df["Δ Marge (pts)"] < -5)
    ].to_dict("records")

    return result
