"""
engine/tires.py
────────────────────────────────────────────────────────────────────────────
Parse the Pneus*.csv file (tyre analysis by season, category and brand).

Teaching note:
  The file has 4 data blocks separated by blank lines, one per season type.
  Each block starts with a header row whose first column identifies it:
    marque4  → ÉTÉ    (Summer)
    marque   → 4 SAISONS  (All-season)
    marque2  → HIVER  (Winter)
    marque3  → Autre  (ignored)

  Column positions are the same across all blocks:
    [0]  brand name
    [3]  qty N
    [4]  market share %
    [8]  CA N (€)
    [9]  CA evolution % vs N-1
    [14] margin € N
    [15] margin % N
    [16] category: PREMIUM / MEDIUM / BUDGET
    [19] category qty total
    [20] category market-share %
    [24] category CA total €
    [25] category CA evo %
    [30] category margin total €
    [31] category margin %

Entry point:
  parse_tires(folder=PNEUS_DIR) -> dict with keys:
    season_df         (DataFrame: ÉTÉ / 4S / HIVER totals)
    category_mix_df   (DataFrame: PREMIUM / MEDIUM / BUDGET totals)
    ete_brand_df      (DataFrame: ÉTÉ brand detail)
    summary           (grand total dict)
    errors, available
"""

from __future__ import annotations

import csv
import datetime
import glob
import pathlib
from typing import Optional

import pandas as pd

from engine.utils import (
    PNEUS_DIR, parse_pct, parse_int, clean, status_from_evo
)

CATS = ["PREMIUM", "MEDIUM", "BUDGET"]
TEMPLATE_BRANDS = {
    "PREMIUM": ["AUTRE", "CONTINENTAL", "GOODYEAR", "MICHELIN", "PIRELLI"],
    "MEDIUM":  ["AUTRE", "FEU VERT",  "HANKOOK",  "KUMHO",    "NEXEN", "NOKIAN"],
    "BUDGET":  ["AUTRE", "ROVELO",    "TRACMAX"],
}


def _find_block(lines: list[str], col0_value: str) -> tuple[int, int]:
    """Return (start, end) line indices for the block starting with col0_value."""
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            row = next(csv.reader([line]))
        except StopIteration:
            continue
        if row and row[0].strip() == col0_value:
            start = i + 1
            for j in range(start, len(lines)):
                if not lines[j].strip():
                    return start, j
            return start, len(lines)
    return -1, -1


def _parse_block(lines: list[str], start: int, end: int) -> tuple[dict, dict]:
    """
    Parse one season block.
    Returns:
      brand_data : {(category, brand) -> metrics_dict}
      cat_totals : {category -> totals_dict}
    """
    brand_data: dict = {}
    cat_totals: dict = {}

    for line in lines[start:end]:
        if not line.strip():
            continue
        try:
            row = next(csv.reader([line]))
        except StopIteration:
            continue
        if len(row) < 20:
            continue

        brand = row[0].strip()
        cat   = row[16].strip() if len(row) > 16 else ""
        if not brand or not cat:
            continue

        brand_data[(cat, brand)] = {
            "qty":       clean(row[3])  if len(row) > 3  else None,
            "pdm":       clean(row[4])  if len(row) > 4  else None,
            "ca":        clean(row[8])  if len(row) > 8  else None,
            "ca_evo":    clean(row[9])  if len(row) > 9  else None,
            "marge_eur": clean(row[14]) if len(row) > 14 else None,
            "marge_pct": clean(row[15]) if len(row) > 15 else None,
        }

        if cat not in cat_totals:
            cat_totals[cat] = {
                "qty":       clean(row[19]) if len(row) > 19 else None,
                "pdm":       clean(row[20]) if len(row) > 20 else None,
                "ca":        clean(row[24]) if len(row) > 24 else None,
                "ca_evo":    clean(row[25]) if len(row) > 25 else None,
                "marge_eur": clean(row[30]) if len(row) > 30 else None,
                "marge_pct": clean(row[31]) if len(row) > 31 else None,
            }

    return brand_data, cat_totals


def _season_totals(cat_totals: dict) -> dict:
    """Sum PREMIUM + MEDIUM + BUDGET from a season's cat_totals."""
    s_qty = s_ca = s_marge = 0
    evo_list = []
    for cat in CATS:
        ct = cat_totals.get(cat, {})
        s_qty   += parse_int(ct.get("qty",       "0") or "0") or 0
        s_ca    += parse_int(ct.get("ca",         "0") or "0") or 0
        s_marge += parse_int(ct.get("marge_eur",  "0") or "0") or 0
        evo = parse_pct(ct.get("ca_evo", "0") or "0")
        if evo is not None:
            evo_list.append(evo)
    avg_evo    = round(sum(evo_list) / len(evo_list), 1) if evo_list else None
    marge_pct  = round(s_marge / s_ca * 100, 2) if s_ca else None
    return {
        "qty": s_qty, "ca": s_ca, "marge_eur": s_marge,
        "marge_pct": marge_pct, "evo": avg_evo,
    }


def parse_tires(folder: pathlib.Path = PNEUS_DIR) -> dict:
    """
    Parse the tyre CSV and return a unified result dict.
    Never raises – errors go into result['errors'].
    """
    errors: list[str] = []
    result = {
        "season_df":       pd.DataFrame(),
        "category_mix_df": pd.DataFrame(),
        "ete_brand_df":    pd.DataFrame(),
        "summary":         {},
        "errors":          errors,
        "available":       False,
        "period":          "",
        "week_num":        None,
    }

    csv_files = glob.glob(str(folder / "Pneus*.csv"))
    if not csv_files:
        errors.append("⚠️  Aucun fichier Pneus*.csv dans /app/resources/Pneus/")
        return result

    with open(csv_files[0], "r", encoding="utf-8-sig") as fh:
        content = fh.read()

    lines = content.split("\n")

    # Extract period from line 2: "ANNECY 2,20/04/2026 - 26/04/2026"
    try:
        meta = next(csv.reader([lines[1]]))
        period_str = meta[1].strip()
        end_date   = datetime.datetime.strptime(
            period_str.split(" - ")[1].strip(), "%d/%m/%Y"
        ).date()
        result["period"]   = period_str
        result["week_num"] = end_date.isocalendar()[1]
    except Exception:
        pass

    # Parse the 3 season blocks
    s1, e1 = _find_block(lines, "marque4")
    s2, e2 = _find_block(lines, "marque")
    s3, e3 = _find_block(lines, "marque2")

    brand_ete,   cat_ete   = _parse_block(lines, s1, e1) if s1 >= 0 else ({}, {})
    brand_4s,    cat_4s    = _parse_block(lines, s2, e2) if s2 >= 0 else ({}, {})
    brand_hiver, cat_hiver = _parse_block(lines, s3, e3) if s3 >= 0 else ({}, {})

    # ── Season summary DataFrame ─────────────────────────────────────────────
    season_rows = []
    for label, ct in [("ÉTÉ", cat_ete), ("4 SAISONS", cat_4s), ("HIVER", cat_hiver)]:
        tot = _season_totals(ct)
        season_rows.append({
            "Saison":      label,
            "Qté":         tot["qty"],
            "CA (€)":      tot["ca"],
            "Évo. CA (%)": tot["evo"],
            "Marge (€)":   tot["marge_eur"],
            "Marge (%)":   tot["marge_pct"],
            "Statut":      status_from_evo(str(tot["evo"] or 0)),
        })
    result["season_df"] = pd.DataFrame(season_rows)

    # ── Category mix DataFrame (across all seasons) ──────────────────────────
    cat_rows = []
    for cat in CATS:
        cat_qty = cat_ca = cat_marge = 0
        for ct in [cat_ete, cat_4s, cat_hiver]:
            c = ct.get(cat, {})
            cat_qty   += parse_int(c.get("qty",       "0") or "0") or 0
            cat_ca    += parse_int(c.get("ca",         "0") or "0") or 0
            cat_marge += parse_int(c.get("marge_eur",  "0") or "0") or 0
        mp = round(cat_marge / cat_ca * 100, 1) if cat_ca else None
        cat_rows.append({
            "Catégorie":   cat,
            "Qté":         cat_qty,
            "CA (€)":      cat_ca,
            "Marge (%)":   mp,
        })
    result["category_mix_df"] = pd.DataFrame(cat_rows)

    # ── Grand total summary ──────────────────────────────────────────────────
    g_qty = g_ca = g_marge = 0
    for tot in [_season_totals(cat_ete), _season_totals(cat_4s), _season_totals(cat_hiver)]:
        g_qty   += tot["qty"]
        g_ca    += tot["ca"]
        g_marge += tot["marge_eur"]
    g_marge_pct = round(g_marge / g_ca * 100, 2) if g_ca else None
    result["summary"] = {
        "qty": g_qty, "ca": g_ca,
        "marge_eur": g_marge, "marge_pct": g_marge_pct,
    }

    # ── ÉTÉ brand detail DataFrame ───────────────────────────────────────────
    brand_rows = []
    for cat, brands in TEMPLATE_BRANDS.items():
        for brand in brands:
            d = brand_ete.get((cat, brand), {})
            brand_rows.append({
                "Catégorie":   cat,
                "Marque":      brand,
                "Qté":         parse_int(d.get("qty", "0") or "0"),
                "PdM (%)":     parse_pct(d.get("pdm", "0") or "0"),
                "CA (€)":      parse_int(d.get("ca", "0") or "0"),
                "Évo. CA (%)": parse_pct(d.get("ca_evo", "0") or "0"),
                "Marge (€)":   parse_int(d.get("marge_eur", "0") or "0"),
                "Marge (%)":   parse_pct(d.get("marge_pct", "0") or "0"),
                "Statut":      status_from_evo(d.get("ca_evo", "0") or "0"),
            })
    result["ete_brand_df"] = pd.DataFrame(brand_rows)
    result["available"]    = True

    return result
