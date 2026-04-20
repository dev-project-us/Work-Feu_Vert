---
description: defectuosite mensuel
---

ALWAYS use this skill when the user types "/defectuosite-mensuel". Execute the
Python script below in full. It scans the monthly CA_Main_d_oeuvre CSV and fills
Section 5 Atelier of the monthly report. Do NOT interpret or read the CSV yourself.

---

# Skill : Taux de Défectuosité — Section 5 Atelier Rapport Mensuel Feu Vert Annecy

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

MOIS_FR = {
    1:'janvier', 2:'février', 3:'mars', 4:'avril',
    5:'mai', 6:'juin', 7:'juillet', 8:'août',
    9:'septembre', 10:'octobre', 11:'novembre', 12:'décembre'
}

# ─────────────────────────────────────────────
# STEP 1 — SCAN AND IDENTIFY CSV FILE
# ─────────────────────────────────────────────

folder    = str(find_dir("monthly_recap") / "defectuosite")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_def = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'technicien3' in content:
        fichier_def = f
        break

assert fichier_def, "ERREUR : fichier défectuosité introuvable dans monthly_recap/defectuosite/"

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE MONTH AND YEAR
# ─────────────────────────────────────────────

# Line format: "ANNECY SEYNOD,01/03/2026,31/03/2026"
lines = content.split('\r\n')
for line in lines:
    if 'ANNECY' in line and '/' in line:
        parts        = line.split(',')
        date_fin_str = parts[2].strip()
        date_fin     = datetime.strptime(date_fin_str, "%d/%m/%Y")
        mois_str     = MOIS_FR[date_fin.month]
        annee        = date_fin.year
        break

# ─────────────────────────────────────────────
# STEP 3 — LOCATE REPORT FILE
# ─────────────────────────────────────────────

rapport_dir  = str(find_dir("Rapport mensuel"))
rapport_path = os.path.join(rapport_dir, f"rapport mensuel {mois_str} {annee}.md")

assert os.path.exists(rapport_path), \
    f"ERREUR : Rapport mensuel {mois_str} {annee} introuvable. Lance d'abord /chiffre-mensuel."

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
# Template column order (12 columns including name):
# Technicien | Nb OR | Déf. Batterie | Disq AV | Disq AR |
# Plaq Av | Plaq Ar | Def BEG | Déf. VCF (Frein) | Déf. VCR |
# Déf. Amort | Déf. Pare-brise
#
# Template placeholder: |**Chandrack K.**||%|%|%|%|%|%|%|%|%|%|
#
NOM_MAP = {
    'Chandrack K.':    'CHANDRACK K.',
    'Mohammed Ali M.': 'MOHAMMED ALI M.',
    'Victor B.':       'VICTOR B.',
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

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

written = []
skipped = []

for nom_template, nom_csv in NOM_MAP.items():
    # Exact template placeholder: |**Chandrack K.**||%|%|%|%|%|%|%|%|%|%|
    old = f"|**{nom_template}**||" + "%|" * 10

    if nom_csv not in techniciens:
        skipped.append(f"{nom_template} (CSV: {nom_csv})")
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
