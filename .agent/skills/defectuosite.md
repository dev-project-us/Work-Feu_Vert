---
description: defectuosite
---

ALWAYS use this skill when the user types "/defectuosite". Execute the Python
script below in full. It scans the CA_Main_d_oeuvre CSV, extracts the synthesis
block, and fills Section 5 Atelier of the weekly report. Do NOT interpret or
read the CSV yourself. Python does everything.

---

# Skill : Taux de Défectuosité — Section 5 Atelier Rapport Hebdomadaire Feu Vert Annecy

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

# ─────────────────────────────────────────────
# STEP 1 — SCAN AND IDENTIFY CSV FILE
# ─────────────────────────────────────────────

folder    = str(find_dir("resources") / "defectuosite")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_def = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'technicien3' in content:
        fichier_def = f
        break

assert fichier_def, "ERREUR : fichier défectuosité introuvable dans resources/defectuosite/"

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE WEEK NUMBER
# ─────────────────────────────────────────────

# Line format: "ANNECY SEYNOD,16/03/2026,22/03/2026"
lines = content.split('\r\n')
semaine = None
for line in lines:
    if 'ANNECY' in line and '/' in line:
        parts        = line.split(',')
        date_fin_str = parts[2].strip()
        date_fin     = datetime.strptime(date_fin_str, "%d/%m/%Y")
        semaine      = date_fin.isocalendar()[1]
        break

assert semaine, "ERREUR : date de fin introuvable dans le fichier défectuosité."

# ─────────────────────────────────────────────
# STEP 3 — LOCATE REPORT FILE
# ─────────────────────────────────────────────

rapport_dir  = str(find_dir("Rapport hebdomadaire"))
rapport_path = os.path.join(rapport_dir, f"rapport hebdomadaire semaine {semaine}.md")

assert os.path.exists(rapport_path), \
    f"ERREUR : Rapport semaine {semaine} introuvable. Lance d'abord /chiffre."

# ─────────────────────────────────────────────
# STEP 4 — EXTRACT SYNTHESIS BLOCK
# ─────────────────────────────────────────────
# The synthesis block is the LAST block starting with "technicien3".
# Split on double CRLF, keep the last matching block.

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
# Template column order (12 columns including name):
# Technicien | Nb OR | Déf. Batterie | Disq AV | Disq AR |
# Plaq Av | Plaq Ar | Def BEG | Déf. VCF (Frein) | Déf. VCR |
# Déf. Amort | Déf. Pare-brise
#
# Template placeholder row (exact):
# |**Chandrack K.**||%|%|%|%|%|%|%|%|%|%|
# ← empty Nb OR ──┘└─── 10 % placeholders ───────────────┘

NOM_MAP = {
    'Chandrack K.':    'CHANDRACK K.',
    'Mohammed Ali M.': 'MOHAMMED ALI M.',
    'Alishan A.':      'ALISHAN A.',
    'Gael R.':         'GAEL R.',
    'Denis D.':        'DENIS D.',
}

# Column order MUST match template header exactly.
# Excluded from template: taux_def_nci3, taux_def_geometrie3
COLS = [
    'nb_diag_realises',        # Nb OR
    'taux_def_batterie3',      # Déf. Batterie
    'taux_def_disques_av3',    # Disq AV
    'taux_def_disques_ar3',    # Disq AR
    'taux_def_plaquettes_av3', # Plaq Av
    'taux_def_plaquettes_ar3', # Plaq Ar
    'taux_def_beg3',           # Def BEG       ← position 7 in template
    'taux_def_vcf3',           # Déf. VCF (Frein)
    'taux_def_vcr3',           # Déf. VCR
    'taux_def_amortisseurs3',  # Déf. Amort
    'taux_def_pare_brise',     # Déf. Pare-brise
]
# 11 data columns = 1 Nb OR (integer) + 10 percentage columns

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

written = []
skipped = []

for nom_template, nom_csv in NOM_MAP.items():
    # Exact template placeholder: |**Chandrack K.**||%|%|%|%|%|%|%|%|%|%|
    old = f"|**{nom_template}**||" + "%|" * 10

    if nom_csv not in techniciens:
        skipped.append(nom_template)
        continue

    data = techniciens[nom_csv]
    vals = [data.get(col, '').strip() or '-' for col in COLS]
    new  = f"|**{nom_template}**|" + "|".join(vals) + "|"

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
print(f"{'Technicien':<20} {'Nb OR':>5}  {'Batterie':>10}  {'VCF':>8}  {'VCR':>8}  {'BEG':>8}")
print("-" * 65)
for nom_template, nom_csv in NOM_MAP.items():
    if nom_csv in techniciens:
        d = techniciens[nom_csv]
        print(f"{nom_template:<20} "
              f"{d.get('nb_diag_realises','').strip():>5}  "
              f"{d.get('taux_def_batterie3','').strip():>10}  "
              f"{d.get('taux_def_vcf3','').strip():>8}  "
              f"{d.get('taux_def_vcr3','').strip():>8}  "
              f"{d.get('taux_def_beg3','').strip():>8}")
    else:
        print(f"{nom_template:<20} {'— absent du CSV'}")
```
