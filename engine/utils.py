"""
engine/utils.py
────────────────────────────────────────────────────────────────────────────
Shared utilities for Feu Vert data engine.

Teaching note:
  The CSV files from SUC use French formatting conventions:
    - Numbers: spaces as thousands separator  → "47 832"
    - Decimals: comma instead of dot          → "12,5 %"
    - BOM marker at file start (utf-8-sig)    → handled by encoding param
  All parse_* helpers normalise these into plain Python types.
"""

from __future__ import annotations

import glob
import pathlib
from typing import Optional

# ── Data directory constants ─────────────────────────────────────────────────
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent
BASE_DIR      = _PROJECT_ROOT / "resources"
SUC_DIR       = BASE_DIR / "SUC"
FAMILLES_DIR  = BASE_DIR / "familles"
PNEUS_DIR     = BASE_DIR / "Pneus"
RATIOS_DIR    = BASE_DIR / "ratios prioritaires"
SUIVI_DIR     = BASE_DIR / "suivi vendeur"
DEFECT_DIR    = BASE_DIR / "defectuosite"
MONTHLY_DIR   = BASE_DIR / "Resources mensuelles"
QUARTERLY_DIR = BASE_DIR / "trimestres"


# ── Value parsers ────────────────────────────────────────────────────────────

def parse_pct(s: str) -> Optional[float]:
    """
    Parse a French percentage string into a float.
    Examples: ' 12,5 %' → 12.5   |  '+42,3 pts' → 42.3   |  '' → None
    """
    try:
        return float(
            s.replace(" %", "").replace("%", "")
             .replace(" pts", "").replace("pts", "")
             .replace(",", ".").replace("+", "").strip()
        )
    except (ValueError, AttributeError):
        return None


def parse_int(s: str) -> Optional[int]:
    """
    Parse a French integer string (with space thousands sep) into an int.
    Examples: '47 832' → 47832  |  '47\xa0832 €' → 47832  |  '' → None
    """
    try:
        return int(
            s.replace("\xa0", "").replace("\u202f", "").replace(" ", "")
             .replace("€", "").replace("+", "").strip()
        )
    except (ValueError, AttributeError):
        return None


def parse_float(s: str) -> Optional[float]:
    """
    Parse a French decimal string into a float.
    Examples: '75,4' → 75.4   |  '75.4 €' → 75.4   |  '' → None
    """
    try:
        return float(
            s.replace(",", ".").replace(" ", "")
             .replace("€", "").replace("+", "").strip()
        )
    except (ValueError, AttributeError):
        return None


def clean(s: str) -> Optional[str]:
    """Return stripped string, or None if empty/dash/N/A."""
    val = s.strip() if isinstance(s, str) else ""
    return val if val and val not in ("-", "N/A", "") else None


# ── Status helper ────────────────────────────────────────────────────────────

def status_from_evo(evo_str: str) -> str:
    """
    Return a colour emoji based on evolution value.
    Positive growth → 🟢, flat → 🟡, decline → 🔴, unknown → ⚪
    """
    val = parse_pct(evo_str) if isinstance(evo_str, str) else evo_str
    if val is None:
        return "⚪"
    if val > 0:
        return "🟢"
    if val == 0:
        return "🟡"
    return "🔴"


# ── File discovery ───────────────────────────────────────────────────────────

def find_csv(directory: pathlib.Path, pattern: str) -> Optional[str]:
    """Find the first CSV matching *pattern* in *directory*. Returns None if absent."""
    files = glob.glob(str(directory / pattern))
    return files[0] if files else None


def read_raw(path: str) -> str:
    """Read a CSV as raw text, handling the UTF-8 BOM that SUC files use."""
    with open(path, "r", encoding="utf-8-sig") as fh:
        return fh.read()


# ── Formatting helpers ───────────────────────────────────────────────────────

def fmt_eur(value: Optional[int | float], decimals: int = 0) -> str:
    """Format a number as a French euro amount. None → 'N/A'."""
    if value is None:
        return "N/A"
    if decimals:
        return f"{value:,.{decimals}f} €".replace(",", " ")
    return f"{int(value):,} €".replace(",", " ")


def fmt_pct(value: Optional[float], sign: bool = False) -> str:
    """Format a float as a percentage string. None → 'N/A'."""
    if value is None:
        return "N/A"
    prefix = "+" if sign and value >= 0 else ""
    return f"{prefix}{value:.1f} %".replace(".", ",")
