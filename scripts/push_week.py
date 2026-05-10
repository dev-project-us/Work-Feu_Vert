#!/usr/bin/env python3
"""
scripts/push_week.py
────────────────────────────────────────────────────────────────────────────
Weekly CSV drop + classify + push to GitHub.

HOW IT WORKS:
  1. You drop all raw CSV exports into the  inbox/  folder at the repo root
  2. This script reads each file, identifies it by content (same logic as
     the engine parsers), and copies it to the right subfolder
  3. Files are archived under  data/weeks/YYYY-WXX/
  4. The  data/current/  folder is updated to always hold the latest week
  5. A git commit + push is made automatically

USAGE:
  # From the repo root:
  python scripts/push_week.py              ← uses inbox/ by default
  python scripts/push_week.py /other/path  ← use a custom drop folder
  python scripts/push_week.py --dry-run    ← preview without committing

WHAT GETS CLASSIFIED:
  ┌─────────────────────────────────────────┬──────────────────────────────┐
  │ Detection signal (in file content)      │ Destination subfolder        │
  ├─────────────────────────────────────────┼──────────────────────────────┤
  │ "libelleJour"                           │ SUC/   (objectifs)           │
  │ "Du 01/" + "caht_n"                     │ SUC/   (MTD)                 │
  │ "Du " + "caht_n" (not 1st)             │ SUC/   (semaine)             │
  │ "libelleUnivers"                        │ ratios_prioritaires/         │
  │ "textbox390"                            │ suivi_vendeur/               │
  │ "technicien3"                           │ defectuosite/                │
  │ "comparatifCAv2" in filename            │ familles/                    │
  │ "marque4" in content                    │ Pneus/                       │
  └─────────────────────────────────────────┴──────────────────────────────┘
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── Colour helpers (terminal output) ────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"{GREEN}  ✅ {msg}{RESET}")
def warn(msg):  print(f"{YELLOW}  ⚠️  {msg}{RESET}")
def err(msg):   print(f"{RED}  ❌ {msg}{RESET}")
def info(msg):  print(f"  ℹ️  {msg}")
def title(msg): print(f"\n{BOLD}{msg}{RESET}")


# ── Repo root detection ──────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return ""


# ── Content-based classifier ─────────────────────────────────────────────────

def classify(path: Path) -> str | None:
    """
    Identify which resource subfolder a CSV belongs to.
    Returns the subfolder name, or None if unrecognised.

    Teaching note:
      This uses the exact same detection logic as the engine parsers.
      If you add a new CSV type to the engine, add its detection here too.
    """
    content  = _read(path)
    filename = path.name.lower()

    if not content.strip():
        return None

    # SUC files — all share "caht_n" or "libelleJour"
    if "libelleJour" in content:
        return "SUC"           # Objectifs Journaliers

    if "caht_n" in content:
        return "SUC"           # Situation de chiffre (semaine or MTD)

    # Other resource types
    if "libelleUnivers" in content:
        return "ratios_prioritaires"

    if "textbox390" in content:
        return "suivi_vendeur"

    if "technicien3" in content:
        return "defectuosite"

    if "marque4" in content or "marque," in content[:500]:
        return "Pneus"

    if "comparatifcav2" in filename or "codeFamille" in content:
        return "familles"

    return None


# ── Week number extraction ────────────────────────────────────────────────────

def extract_week(path: Path) -> tuple[int, int] | None:
    """
    Try to read a date from the CSV content and return (year, week_number).
    Tries several known date patterns used across the SUC CSVs.
    """
    content = _read(path)

    # Pattern 1: "Du 16/03/2026,22/03/2026"  (SUC files)
    m = re.search(r"Du \d{2}/\d{2}/\d{4},(\d{2}/\d{2}/\d{4})", content)
    if m:
        d = datetime.strptime(m.group(1), "%d/%m/%Y")
        return d.isocalendar()[:2]  # (year, week)

    # Pattern 2: "ANNECY 2,16/03/2026-22/03/2026"  (ratios)
    m = re.search(r"ANNECY[^,]*,\d{2}/\d{2}/\d{4}-(\d{2}/\d{2}/\d{4})", content)
    if m:
        d = datetime.strptime(m.group(1), "%d/%m/%Y")
        return d.isocalendar()[:2]

    # Pattern 3: "ANNECY 2,16/03/2026 - 22/03/2026"  (suivi vendeur)
    m = re.search(r"ANNECY[^,]*,\d{2}/\d{2}/\d{4} - (\d{2}/\d{2}/\d{4})", content)
    if m:
        d = datetime.strptime(m.group(1), "%d/%m/%Y")
        return d.isocalendar()[:2]

    # Pattern 4: "ANNECY SEYNOD,16/03/2026,22/03/2026"  (defectuosite)
    m = re.search(r"ANNECY[^,]*,\d{2}/\d{2}/\d{4},(\d{2}/\d{2}/\d{4})", content)
    if m:
        d = datetime.strptime(m.group(1), "%d/%m/%Y")
        return d.isocalendar()[:2]

    # Pattern 5: period string "20/04/2026 - 26/04/2026"  (pneus)
    m = re.search(r"\d{2}/\d{2}/\d{4} - (\d{2}/\d{2}/\d{4})", content)
    if m:
        d = datetime.strptime(m.group(1), "%d/%m/%Y")
        return d.isocalendar()[:2]

    return None


# ── Git helpers ──────────────────────────────────────────────────────────────

def run_git(args: list[str], cwd: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Classify CSVs, archive by week, and push to GitHub."
    )
    parser.add_argument(
        "inbox",
        nargs="?",
        default=str(REPO_ROOT / "inbox"),
        help="Folder containing the raw CSV exports (default: inbox/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without actually copying or committing",
    )
    args = parser.parse_args()

    inbox_dir = Path(args.inbox)
    dry_run   = args.dry_run

    title("═══  Feu Vert — Push Semaine  ═══")

    # ── 1. Find CSVs ──────────────────────────────────────────────────────────
    csv_files = list(inbox_dir.glob("*.csv")) + list(inbox_dir.glob("*.CSV"))
    if not csv_files:
        err(f"Aucun fichier CSV trouvé dans : {inbox_dir}")
        err("Dépose tes exports CSV dans le dossier inbox/ puis relance.")
        sys.exit(1)

    info(f"{len(csv_files)} fichier(s) CSV détecté(s) dans {inbox_dir.name}/")

    # ── 2. Classify + extract week ────────────────────────────────────────────
    title("Étape 1 — Classification des fichiers")

    classified: dict[str, Path]       = {}   # subfolder → file path
    week_candidates: list[tuple[int, int]] = []
    unrecognised: list[Path]           = []

    for csv_path in csv_files:
        subfolder = classify(csv_path)
        week_info  = extract_week(csv_path)

        if subfolder:
            classified[subfolder] = csv_path   # last one wins per subfolder
            ok(f"{csv_path.name}  →  {subfolder}/")
        else:
            warn(f"{csv_path.name}  →  non reconnu, ignoré")
            unrecognised.append(csv_path)

        if week_info:
            week_candidates.append(week_info)

    if not classified:
        err("Aucun fichier classifié — vérifier le contenu des CSV.")
        sys.exit(1)

    # Determine the week from the most common (year, week) tuple
    if not week_candidates:
        err("Impossible de détecter le numéro de semaine depuis les CSV.")
        sys.exit(1)

    year, week_num = max(set(week_candidates), key=week_candidates.count)
    week_label = f"{year}-W{week_num:02d}"
    info(f"Semaine détectée : {week_label}")

    # ── 3. Copy files ─────────────────────────────────────────────────────────
    title(f"Étape 2 — Archivage dans data/weeks/{week_label}/")

    archive_dir = REPO_ROOT / "data" / "weeks" / week_label
    current_dir = REPO_ROOT / "data" / "current"

    for subfolder, src_path in classified.items():
        dest_archive = archive_dir / subfolder / src_path.name
        dest_current = current_dir / subfolder / src_path.name

        if not dry_run:
            dest_archive.parent.mkdir(parents=True, exist_ok=True)
            dest_current.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_archive)
            shutil.copy2(src_path, dest_current)
            ok(f"Copié → data/weeks/{week_label}/{subfolder}/{src_path.name}")
            ok(f"Copié → data/current/{subfolder}/{src_path.name}")
        else:
            info(f"[DRY-RUN] Copierait → data/weeks/{week_label}/{subfolder}/")
            info(f"[DRY-RUN] Copierait → data/current/{subfolder}/")

    # ── 4. Clear old files from current/ (only the same subfolders) ──────────
    if not dry_run:
        title("Étape 3 — Nettoyage de data/current/")
        for subfolder in classified.keys():
            current_sub = current_dir / subfolder
            for old_file in current_sub.glob("*.csv"):
                # Keep only the newly copied file
                newly_copied = current_sub / classified[subfolder].name
                if old_file != newly_copied:
                    old_file.unlink()
                    info(f"Supprimé ancien fichier : {old_file.name}")

    # ── 5. Git commit + push ──────────────────────────────────────────────────
    title("Étape 4 — Commit & Push GitHub")

    if dry_run:
        info(f"[DRY-RUN] Commiterait : 'data: semaine {week_label}'")
        info("[DRY-RUN] Pousserait vers origin/main")
        title("Dry-run terminé — aucune modification effectuée.")
        return

    # Stage the new files
    ok_add, msg_add = run_git(["add", "data/weeks/", "data/current/"], REPO_ROOT)
    if not ok_add:
        err(f"git add échoué : {msg_add}")
        sys.exit(1)

    # Check if there's anything to commit
    ok_status, status_out = run_git(["status", "--porcelain"], REPO_ROOT)
    if not status_out.strip():
        warn("Aucun changement à commiter — les fichiers sont déjà à jour.")
        sys.exit(0)

    commit_msg = f"data: semaine {week_label} — {len(classified)} fichier(s)"
    ok_commit, msg_commit = run_git(["commit", "-m", commit_msg], REPO_ROOT)
    if not ok_commit:
        err(f"git commit échoué : {msg_commit}")
        sys.exit(1)
    ok(f"Commit : {commit_msg}")

    ok_push, msg_push = run_git(["push", "origin", "main"], REPO_ROOT)
    if not ok_push:
        err(f"git push échoué : {msg_push}")
        err("Vérifier la connexion ou le token GitHub (voir README).")
        sys.exit(1)
    ok("Push vers GitHub réussi ✓")

    # ── 6. Optional: empty the inbox ─────────────────────────────────────────
    title("Étape 5 — Nettoyage de inbox/")
    for f in classified.values():
        f.unlink()
        info(f"Supprimé de inbox/ : {f.name}")
    for f in unrecognised:
        warn(f"Laissé dans inbox/ (non reconnu) : {f.name}")

    title(f"✅  Semaine {week_label} poussée sur GitHub avec succès !")
    print(
        f"\n  Accès dashboard : http://<ip-proxmox>:8501\n"
        f"  Données dans   : data/weeks/{week_label}/\n"
        f"  Données live   : data/current/\n"
    )


if __name__ == "__main__":
    main()
