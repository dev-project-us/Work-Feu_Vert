"""
engine/global_stats.py
────────────────────────────────────────────────────────────────────────────
Parse the SUC 'Situation de chiffre' and 'Objectifs Journaliers' CSV files.

Teaching note:
  The SUC files are NOT clean tables. They contain multiple independent data
  blocks separated by blank lines, each with its own header row.
  Strategy: scan line by line, detect each block header, then read the
  immediately following data row into a dict keyed by the header columns.
  We never use pandas read_csv() because it would mis-detect headers.

Entry point:
  weekly_kpis(folder=SUC_DIR) -> dict

Returned structure:
  {
    "available":  bool,
    "period":     (date_debut, date_fin),
    "week_num":   int,
    "global":     { ca_ht, ca_ht_n1, ca_obj_ht, ca_evo, ca_ecart,
                    marge, marge_n1, marge_obj, marge_evo, marge_ecart,
                    freq, freq_n1, freq_evo, panier, panier_evo },
    "ls":         { ca, ca_evo, ca_obj, marge, marge_evo,
                    freq, freq_evo, panier, panier_evo },
    "atelier":    { ca, ca_evo, ca_obj, marge, marge_evo,
                    nb_or, nb_or_evo, panier, panier_evo },
    "mtd":        { ca, ca_obj, ca_pct, ca_raf,
                    marge_eur, marge_obj, marge_pct, marge_raf,
                    contrats },
    "errors":     [list of error strings]
  }
"""

from __future__ import annotations

import csv
import glob
import pathlib
from datetime import datetime
from typing import Optional

from engine.utils import (
    SUC_DIR, parse_pct, parse_int, parse_float, read_raw
)


# ── File identification ──────────────────────────────────────────────────────

def _identify_files(folder: pathlib.Path) -> dict[str, Optional[str]]:
    """
    Scan folder and classify the 3 SUC files by their content signature.

    The 3 files are:
      SEMAINE   – period starts mid-month  (e.g. "Du 16/03/2026,22/03/2026")
      MTD       – period starts on 1st     (e.g. "Du 01/03/2026,22/03/2026")
      OBJECTIFS – contains column 'libelleJour' (daily objectives)
    """
    result: dict[str, Optional[str]] = {
        "semaine": None, "mtd": None, "objectifs": None
    }
    csv_files = glob.glob(str(folder / "SUC - *.csv"))
    for f in csv_files:
        content = read_raw(f)
        if "libelleJour" in content:
            result["objectifs"] = f
        elif "Du 01/" in content:
            result["mtd"] = f
        else:
            result["semaine"] = f
    return result


# ── Period extraction ────────────────────────────────────────────────────────

def _parse_period(content: str) -> tuple:
    """
    Extract (date_debut, date_fin, week_num) from the period header line.
    Line format: "Du 16/03/2026,22/03/2026"
    """
    for line in content.replace("\r\n", "\n").split("\n"):
        if line.startswith("Du "):
            parts = line.split(",")
            if len(parts) >= 2:
                try:
                    date_debut = datetime.strptime(
                        parts[0].replace("Du ", "").strip(), "%d/%m/%Y"
                    )
                    date_fin   = datetime.strptime(parts[1].strip(), "%d/%m/%Y")
                    week_num   = date_fin.isocalendar()[1]
                    return date_debut, date_fin, week_num
                except ValueError:
                    pass
    return None, None, None


# ── Situation de chiffre parser ──────────────────────────────────────────────

def _parse_situation(content: str) -> dict[str, str]:
    """
    Scan a 'Situation de chiffre' CSV and return a flat {column: value} dict.

    The file has 4 independent data blocks, each starting with a known
    header row. We detect each header, then read the immediately next line
    as values, then merge everything into one flat dict.
    """
    BLOCK_HEADERS = {
        "caht_n",        # Global block
        "textbox22",     # Libre Service block
        "textbox43",     # Atelier block
        "nbContratEntretien_DECI",  # Contracts block
    }

    fields: dict[str, str] = {}
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")

    for i, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            row = next(csv.reader([stripped]))
        except StopIteration:
            continue
        if not row:
            continue

        if row[0] in BLOCK_HEADERS and i + 1 < len(lines):
            try:
                val_row = next(csv.reader([lines[i + 1].strip()]))
                for k, v in zip(row, val_row):
                    fields[k.strip()] = v.strip()
            except (StopIteration, IndexError):
                pass

    return fields


# ── Objectifs Journaliers parser ─────────────────────────────────────────────

def _parse_objectifs(content: str) -> dict[str, str]:
    """
    Parse the 'Objectifs Journaliers' CSV to extract monthly target values.

    The monthly objectives are identical on every data row.
    We skip Sunday rows (CATTC == 0) and read the first valid row.

    Key columns:
      textbox8  → monthly objective CA TTC
      textbox50 → monthly objective marge %
      textbox42 → monthly objective marge € (last column)
    """
    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    fields: dict[str, str] = {}

    header_row: Optional[list[str]] = None
    header_idx: int = -1

    for i, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            row = next(csv.reader([stripped]))
        except StopIteration:
            continue
        if row and row[0] == "dateDatetime":
            header_idx = i
            header_row = row
            break

    if header_row is None:
        return fields

    for raw_line in lines[header_idx + 1:]:
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            row = next(csv.reader([stripped]))
        except StopIteration:
            continue
        if len(row) < len(header_row):
            continue
        row_dict = dict(zip(header_row, row))
        # Skip zero-CA rows (Sundays / closed days)
        if parse_float(row_dict.get("CATTC", "0")) in (0, None):
            continue
        fields["textbox8"]  = row_dict.get("textbox8", "")   # CA TTC obj
        fields["textbox50"] = row_dict.get("textbox50", "")  # marge % obj
        fields["textbox42"] = row_dict.get("textbox42", "")  # marge € obj
        break

    return fields


# ── Main entry point ─────────────────────────────────────────────────────────

def weekly_kpis(folder: pathlib.Path = SUC_DIR) -> dict:
    """
    Parse all 3 SUC files and return a unified KPI dict.

    Never raises – errors are collected in result["errors"] so the
    Streamlit UI can display a warning instead of crashing.
    """
    errors: list[str] = []
    result = {
        "available": False,
        "period": None,
        "week_num": None,
        "global": {},
        "ls": {},
        "atelier": {},
        "mtd": {},
        "errors": errors,
    }

    files = _identify_files(folder)

    if not files["semaine"]:
        errors.append("⚠️  Fichier SEMAINE (SUC - Situation de chiffre) introuvable dans /app/resources/SUC/")
        return result
    if not files["objectifs"]:
        errors.append("⚠️  Fichier OBJECTIFS (SUC - Objectifs Journaliers) introuvable dans /app/resources/SUC/")

    # ── Parse week file ──────────────────────────────────────────────────────
    content_s = read_raw(files["semaine"])
    date_debut, date_fin, week_num = _parse_period(content_s)
    result["period"]   = (date_debut, date_fin)
    result["week_num"] = week_num

    fs = _parse_situation(content_s)

    # ── Parse objectifs file ─────────────────────────────────────────────────
    obj = {}
    if files["objectifs"]:
        obj = _parse_objectifs(read_raw(files["objectifs"]))

    # ── Derive objective values ──────────────────────────────────────────────
    obj_ttc   = parse_float(obj.get("textbox8",  "0")) or 0
    caht_obj  = round(obj_ttc / 1.2) if obj_ttc else None
    marge_obj = parse_pct(obj.get("textbox50", "0"))

    # ── Global KPIs ──────────────────────────────────────────────────────────
    caht_n    = parse_int(fs.get("caht_n",    "0"))
    marge_n   = parse_pct(fs.get("marge_n",   "0"))
    freq_n    = parse_int(fs.get("textbox14", "0"))
    panier_ttc = parse_float(fs.get("cattc_n_2", "0"))
    panier_n  = round(panier_ttc / 1.2, 1) if panier_ttc else None

    ca_evo    = parse_pct(fs.get("textbox4",  "0"))
    marge_evo = parse_pct(fs.get("textbox24", "0"))
    freq_evo  = parse_pct(fs.get("textbox17", "0"))

    # Derive N-1 values from current and evolution
    caht_n1   = round(caht_n  / (1 + ca_evo    / 100)) if (caht_n  and ca_evo)    else None
    marge_n1  = round(marge_n - marge_evo, 1)           if (marge_n and marge_evo) else None
    freq_n1   = round(freq_n  / (1 + freq_evo  / 100)) if (freq_n  and freq_evo)  else None

    ca_ecart   = round((caht_n / caht_obj - 1) * 100, 1) if (caht_n and caht_obj) else None
    marge_ecart = round(marge_n - marge_obj, 1)           if (marge_n and marge_obj) else None

    result["global"] = {
        "ca_ht": caht_n,       "ca_ht_n1": caht_n1,  "ca_obj_ht": caht_obj,
        "ca_evo": ca_evo,      "ca_ecart": ca_ecart,
        "marge": marge_n,      "marge_n1": marge_n1,  "marge_obj": marge_obj,
        "marge_evo": marge_evo,"marge_ecart": marge_ecart,
        "freq": freq_n,        "freq_n1": freq_n1,     "freq_evo": freq_evo,
        "panier": panier_n,    "panier_evo": None,
    }

    # ── Libre Service ────────────────────────────────────────────────────────
    result["ls"] = {
        "ca":         parse_int(fs.get("textbox22",  "0")),
        "ca_evo":     parse_pct(fs.get("textbox25",  "0")),
        "ca_obj":     parse_int(fs.get("textbox27",  "0")),
        "marge":      parse_pct(fs.get("textbox31",  "0")),
        "marge_evo":  parse_pct(fs.get("textbox33",  "0")),
        "freq":       parse_int(fs.get("textbox35",  "0")),
        "freq_evo":   parse_pct(fs.get("textbox37",  "0")),
        "panier":     parse_float(fs.get("textbox39", "0")),
        "panier_evo": parse_pct(fs.get("textbox41",  "0")),
    }

    # ── Atelier ──────────────────────────────────────────────────────────────
    result["atelier"] = {
        "ca":         parse_int(fs.get("textbox43",  "0")),
        "ca_evo":     parse_pct(fs.get("textbox45",  "0")),
        "ca_obj":     parse_int(fs.get("textbox47",  "0")),
        "marge":      parse_pct(fs.get("textbox51",  "0")),
        "marge_evo":  parse_pct(fs.get("textbox53",  "0")),
        "nb_or":      parse_int(fs.get("textbox55",  "0")),
        "nb_or_evo":  parse_pct(fs.get("textbox57",  "0")),
        "panier":     parse_float(fs.get("textbox62", "0")),
        "panier_evo": parse_pct(fs.get("textbox64",  "0")),
    }

    # ── MTD (month-to-date) ──────────────────────────────────────────────────
    if files["mtd"]:
        fm = _parse_situation(read_raw(files["mtd"]))

        ca_mtd      = parse_int(fm.get("caht_n", "0"))
        marge_mtd_p = parse_pct(fm.get("marge_n", "0"))

        marge_obj_eur = parse_int(obj.get("textbox42", "0"))

        ca_pct  = round(ca_mtd / caht_obj * 100, 1)   if (ca_mtd and caht_obj)    else None
        ca_raf  = (caht_obj - ca_mtd)                  if (caht_obj and ca_mtd)    else None

        marge_mtd_eur = round(ca_mtd * (marge_mtd_p or 0) / 100) if ca_mtd else None
        m_pct   = round(marge_mtd_eur / marge_obj_eur * 100, 1)  if (marge_mtd_eur and marge_obj_eur) else None
        m_raf   = (marge_obj_eur - marge_mtd_eur)                 if (marge_obj_eur and marge_mtd_eur) else None

        c_deci  = parse_int(fm.get("nbContratEntretien_DECI", "0")) or 0
        c_g6k   = parse_int(fm.get("nbCE_G6K", "0")) or 0

        result["mtd"] = {
            "ca": ca_mtd,           "ca_obj": caht_obj,
            "ca_pct": ca_pct,       "ca_raf": ca_raf,
            "marge_eur": marge_mtd_eur, "marge_obj": marge_obj_eur,
            "marge_pct": m_pct,     "marge_raf": m_raf,
            "contrats": c_deci + c_g6k,
        }

    result["available"] = True
    return result
