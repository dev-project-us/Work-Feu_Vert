---
description: defectuosite trimestriel
---

ALWAYS use this skill when the user types "/defectuosite-trimestriel". Execute the
Python script below in full. It scans the quarterly CA_Main_d_oeuvre CSV and fills
Section 5 Atelier of the quarterly report. Do NOT interpret or read the CSV yourself.
Other triggers: "remplis les défectuosités trimestrielles", "analyse défectuosité du trimestre".

---

# Skill : Taux de Défectuosité — Section 5 Atelier Rapport Trimestriel Feu Vert Annecy

## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité.**
Python fait tout : scan, extraction du bloc synthèse, remplissage Section 5 Atelier.
L'IA ne lit pas le CSV. L'IA ne mappe pas les colonnes.

---

```python
import os, glob, csv, io, pathlib
from datetime import datetime

# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}'")

TRIMESTRE_MAP = {3: 'T1', 6: 'T2', 9: 'T3', 12: 'T4'}

# ─────────────────────────────────────────────
# STEP 1 — SCAN AND IDENTIFY CSV FILE
# ─────────────────────────────────────────────

folder    = str(find_dir("trimestres") / "defectuosité")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_def = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'technicien3' in content:
        fichier_def = f
        break

assert fichier_def, "ERREUR : fichier défectuosité introuvable dans resources/trimestres/defectuosité/"

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE QUARTER AND YEAR
# ─────────────────────────────────────────────

# Line format: "ANNECY SEYNOD,01/01/2026,31/03/2026"
lines = content.split('\r\n')
for line in lines:
    if 'ANNECY' in line and '/' in line:
        parts        = line.split(',')
        date_fin_str = parts[2].strip()
        date_fin     = datetime.strptime(date_fin_str, "%d/%m/%Y")
        trimestre    = TRIMESTRE_MAP.get(date_fin.month, 'T?')
        annee        = date_fin.year
        break

# ─────────────────────────────────────────────
# STEP 3 — LOCATE REPORT FILE
# ─────────────────────────────────────────────

rapport_dir  = str(find_dir("trimestres"))
rapport_path = os.path.join(rapport_dir, f"rapport trimestriel {trimestre} {annee}.md")

assert os.path.exists(rapport_path), \
    f"ERREUR : Rapport trimestriel {trimestre} {annee} introuvable. Lance d'abord /chiffre-trimestriel."

# ─────────────────────────────────────────────
# STEP 4 — EXTRACT SYNTHESIS BLOCK
# ─────────────────────────────────────────────

blocks        = content.split('\r\n\r\n')
synthese_block = None
for block in blocks:
    if block.strip().startswith('technicien3'):
        synthese_block = block.strip()   # keep last occurrence

assert synthese_block, "ERREUR : bloc synthèse 'technicien3' introuvable dans le CSV."

techniciens = {}
reader = csv.DictReader(io.StringIO(synthese_block))
for row in reader:
    nom = row['technicien3'].strip()
    techniciens[nom] = row

# ─────────────────────────────────────────────
# STEP 5 — FILL SECTION 5 ATELIER (pure str.replace)
# ─────────────────────────────────────────────
# Template column order (9 columns including name — 8 data columns):
# Technicien | Nb OR | Déf. Bat. | Disq. AV | Disq. AR |
# Plaq. AV | Plaq. AR | Déf. VCF | Déf. VCR
#
# Template placeholder: | **Chandrack K.** | | % | % | % | % | % | % | % |
# ← empty Nb OR ────────┘└─── 7 % placeholders ──────────────────────────────┘
#
# NOTE: Quarterly template has 4 technicians only (no Alishan/Viktor).

NOM_MAP = {
    'Chandrack K.':    'CHANDRACK K.',
    'Mohammed Ali M.': 'MOHAMMED ALI M.',
    'Gael R.':         'GAEL R.',
    'Denis D.':        'DENIS D.',
}

# Column order MUST match template header exactly (8 data columns)
COLS = [
    'nb_diag_realises',        # Nb OR
    'taux_def_batterie3',      # Déf. Bat.
    'taux_def_disques_av3',    # Disq. AV
    'taux_def_disques_ar3',    # Disq. AR
    'taux_def_plaquettes_av3', # Plaq. AV
    'taux_def_plaquettes_ar3', # Plaq. AR
    'taux_def_vcf3',           # Déf. VCF
    'taux_def_vcr3',           # Déf. VCR
]

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

written = []
skipped = []

for nom_template, nom_csv in NOM_MAP.items():
    # Exact template placeholder: | **Chandrack K.** | | % | % | % | % | % | % | % |
    old = f"| **{nom_template}** | | " + " | ".join(["%"] * 7) + " |"

    if nom_csv not in techniciens:
        skipped.append(nom_template)
        continue

    data = techniciens[nom_csv]
    vals = [data.get(col, '').strip() or '-' for col in COLS]
    new  = f"| **{nom_template}** | " + " | ".join(vals) + " |"

    rapport = rapport.replace(old, new)
    written.append(nom_template)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 6 — CONFIRM
# ─────────────────────────────────────────────

print(f"✅ Section 5 Atelier mise à jour : {rapport_path}")
print(f"✅ Techniciens écrits  : {', '.join(written)}")
if skipped:
    print(f"⚠️  Absents du CSV     : {', '.join(skipped)} — lignes laissées vides")

print()
print(f"{'Technicien':<20} {'Nb OR':>5}  {'Batterie':>10}  {'VCF':>8}  {'VCR':>8}")
print("-" * 55)
for nom_template, nom_csv in NOM_MAP.items():
    if nom_csv in techniciens:
        d = techniciens[nom_csv]
        print(f"{nom_template:<20} "
              f"{d.get('nb_diag_realises','').strip():>5}  "
              f"{d.get('taux_def_batterie3','').strip():>10}  "
              f"{d.get('taux_def_vcf3','').strip():>8}  "
              f"{d.get('taux_def_vcr3','').strip():>8}")
    else:
        print(f"{nom_template:<20} {'— absent du CSV'}")
```
