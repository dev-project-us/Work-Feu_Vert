"""
engine/defects.py
────────────────────────────────────────────────────────────────────────────
Parse the CA_Main_d_oeuvre*.csv file for atelier technician defect rates.

Teaching note:
  The file has several blocks.  Only the LAST block is needed:
  it starts with the header 'technicien3' and is a clean CSV table
  that can be read directly with csv.DictReader.

  We split the whole content on double-newline sequences to find
  that block, then parse it.

Column mapping:
  technicien3              → Technicien
  nb_diag_realises         → Nb OR
  taux_def_batterie3       → Batterie
  taux_def_disques_av3     → Disq AV
  taux_def_disques_ar3     → Disq AR
  taux_def_plaquettes_av3  → Plaq AV
  taux_def_plaquettes_ar3  → Plaq AR
  taux_def_nci3            → NCI
  taux_def_vcf3            → VCF
  taux_def_geometrie3      → Géo
  taux_def_beg3            → BEG
  taux_def_vcr3            → VCR
  taux_def_amortisseurs3   → Amort.
  taux_def_pare_brise      → Pare-brise

Entry point:
  parse_defects(folder=DEFECT_DIR) -> dict with keys:
    df, errors, available
"""

from __future__ import annotations

import csv
import glob
import io
import pathlib
from datetime import datetime
from typing import Optional

import pandas as pd

from engine.utils import DEFECT_DIR, read_raw

NOM_MAP = {
    "ALISHAN A.":      "Alishan A.",
    "CHANDRACK K.":    "Chandrack K.",
    "MOHAMMED ALI M.": "Mohammed Ali M.",
    "VICTOR B.":       "Victor B.",
    "GAEL R.":         "Gael R.",
    "DENIS D.":        "Denis D.",
}

# CSV columns → display columns
COLS = [
    ("nb_diag_realises",        "Nb OR"),
    ("taux_def_batterie3",      "Batterie"),
    ("taux_def_disques_av3",    "Disq AV"),
    ("taux_def_disques_ar3",    "Disq AR"),
    ("taux_def_plaquettes_av3", "Plaq AV"),
    ("taux_def_plaquettes_ar3", "Plaq AR"),
    ("taux_def_nci3",           "NCI"),
    ("taux_def_vcf3",           "VCF"),
    ("taux_def_geometrie3",     "Géo"),
    ("taux_def_beg3",           "BEG"),
    ("taux_def_vcr3",           "VCR"),
    ("taux_def_amortisseurs3",  "Amort."),
    ("taux_def_pare_brise",     "Pare-brise"),
]


def parse_defects(folder: pathlib.Path = DEFECT_DIR) -> dict:
    """
    Parse the defect CSV and return a per-technician DataFrame.
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
        if "technicien3" in content:
            fichier = f
            break

    if not fichier:
        errors.append("⚠️  Aucun fichier CA_Main_d_oeuvre*.csv dans /app/resources/defectuosite/")
        return result

    content = read_raw(fichier)

    # Extract period from the ANNECY line
    for line in content.replace("\r\n", "\n").split("\n"):
        if "ANNECY" in line and "/" in line:
            parts = line.split(",")
            if len(parts) >= 3:
                try:
                    date_fin = datetime.strptime(parts[2].strip(), "%d/%m/%Y")
                    result["period"]   = f"{parts[1].strip()} – {parts[2].strip()}"
                    result["week_num"] = date_fin.isocalendar()[1]
                    break
                except ValueError:
                    pass

    # Find the synthese block (starts with 'technicien3')
    # The file uses \r\n line endings; split on double blank lines
    for sep in ("\r\n\r\n", "\n\n"):
        blocks = content.split(sep)
        synthese_block: Optional[str] = None
        for block in blocks:
            if block.strip().startswith("technicien3"):
                synthese_block = block.strip()
                break
        if synthese_block:
            break

    if not synthese_block:
        errors.append("⚠️  Bloc synthèse (technicien3) introuvable dans le fichier défectuosité")
        return result

    # Parse the clean table with DictReader
    techniciens: dict[str, dict] = {}
    reader = csv.DictReader(io.StringIO(synthese_block.replace("\r\n", "\n")))
    for row in reader:
        nom = row.get("technicien3", "").strip()
        if nom:
            techniciens[nom] = {k.strip(): v.strip() for k, v in row.items()}

    # Build DataFrame (template names, ordered)
    display_cols = ["Technicien"] + [display for _, display in COLS]
    rows = []
    for csv_name, display_name in NOM_MAP.items():
        d   = techniciens.get(csv_name, {})
        row = {"Technicien": display_name}
        for csv_col, display_col in COLS:
            row[display_col] = d.get(csv_col, "-").strip() or "-"
        rows.append(row)

    result["df"]        = pd.DataFrame(rows, columns=display_cols)
    result["available"] = True
    return result
