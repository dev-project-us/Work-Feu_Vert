---
description: suivi vendeur
---

ALWAYS use this skill when the user types "/suivi_vendeur" or "/suivi-vendeur".
Execute the Python script below in full. It scans the Suivi Individuel CSV,
extracts ratios from Blocs 1, 2 and 4, and fills Section 5 LS of the weekly
report. Do NOT interpret or read the CSV yourself. Python does everything.

---

# Skill : Ratios de Vente Individuels — Section 5 LS Rapport Hebdomadaire Feu Vert Annecy

## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité.**
Python fait tout : scan, extraction des 3 blocs CSV, remplissage Section 5 LS.
L'IA ne lit pas le CSV. L'IA ne mappe pas les colonnes.

---

```python
import os, glob, csv, pathlib
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

folder    = str(find_dir("resources") / "suivi vendeur")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_suivi = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'textbox390' in content:
        fichier_suivi = f
        break

assert fichier_suivi, "ERREUR : fichier suivi vendeur introuvable dans resources/suivi vendeur/"

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE WEEK NUMBER
# ─────────────────────────────────────────────

# Line 2 format: "ANNECY 2,16/03/2026 - 22/03/2026"
lines        = content.splitlines()
date_part    = lines[1].split(',')[1]
date_fin_str = date_part.split(' - ')[1].strip()
date_fin     = datetime.strptime(date_fin_str, "%d/%m/%Y")
semaine      = date_fin.isocalendar()[1]

# ─────────────────────────────────────────────
# STEP 3 — LOCATE REPORT FILE
# ─────────────────────────────────────────────

rapport_dir  = str(find_dir("Rapport hebdomadaire"))
rapport_path = os.path.join(rapport_dir, f"rapport hebdomadaire semaine {semaine}.md")

assert os.path.exists(rapport_path), \
    f"ERREUR : Rapport semaine {semaine} introuvable. Lance d'abord /chiffre."

# ─────────────────────────────────────────────
# STEP 4 — EXTRACT RATIOS FROM BLOCS 1, 2 AND 4
# ─────────────────────────────────────────────

NOM_MAP = {
    'Sandrine': 'SANDRINE R.',
    'Paul':     'PAUL P.',
    'Kamilia':  'KAMILIA A.',
    'Chouaib':  'CHOUAIB G.',
    'Pauline':  'PAULINE R.',
    'Valentin': 'VALENTIN C.',
}

# Initialise all ratios to empty string
vendeurs = {nom_csv: {
    'gp_ratio':        '',
    'geom_ratio':      '',
    'vcr_ratio':       '',
    'vcf_ratio':       '',
    'plaquette_ratio': '',
    'depoll_ratio':    '',
} for nom_csv in NOM_MAP.values()}

# ── BLOC 1 : Garantie Pneu & Géométrie ───────────────────────────────────────
# Header starts with "textbox3,"
# Vendeur name : position 8 (textbox390)
# Garantie Pneu ratio : position 22 (textbox56) — fallback pos 23 if no '%'
# Géométrie ratio     : position 28 (textbox159) — fallback pos 29 if no '%'

bloc1_idx = next(i for i, l in enumerate(lines) if l.startswith('textbox3,'))
i = bloc1_idx + 1
while i < len(lines) and lines[i].strip():
    row = list(csv.reader([lines[i]]))[0]
    nom = row[8].strip() if len(row) > 8 else ''
    if nom in vendeurs:
        gp   = row[22].strip() if len(row) > 22 else ''
        geom = row[28].strip() if len(row) > 28 else ''
        # Position shifts for vendors with few tyre sales
        if '%' not in gp:
            gp = row[23].strip() if len(row) > 23 else ''
        if '%' not in geom:
            geom = row[29].strip() if len(row) > 29 else ''
        vendeurs[nom]['gp_ratio']   = gp
        vendeurs[nom]['geom_ratio'] = geom
    i += 1

# ── BLOC 2 : VCR, Plaquette, VCF ─────────────────────────────────────────────
# Header starts with "textbox590,"
# Vendeur name : position 11 (textbox144)
# VCR ratio       : position 19 (textbox156)
# Plaquette ratio : position 21 (textbox146)
# VCF ratio       : position 23 (textbox136)

bloc2_idx = next(i for i, l in enumerate(lines) if l.startswith('textbox590,'))
i = bloc2_idx + 1
while i < len(lines) and lines[i].strip():
    row = list(csv.reader([lines[i]]))[0]
    nom = row[11].strip() if len(row) > 11 else ''
    if nom in vendeurs:
        vendeurs[nom]['vcr_ratio']       = row[19].strip() if len(row) > 19 else ''
        vendeurs[nom]['plaquette_ratio'] = row[21].strip() if len(row) > 21 else ''
        vendeurs[nom]['vcf_ratio']       = row[23].strip() if len(row) > 23 else ''
    i += 1

# ── BLOC 4 : Dépollution ──────────────────────────────────────────────────────
# Header starts with "textbox326,"
# Vendeur name    : position 9  (textbox14)
# Dépoll. ratio   : position 17 (textbox201)

bloc4_idx = next(i for i, l in enumerate(lines) if l.startswith('textbox326,'))
i = bloc4_idx + 1
while i < len(lines) and lines[i].strip():
    row = list(csv.reader([lines[i]]))[0]
    nom = row[9].strip() if len(row) > 9 else ''
    if nom in vendeurs:
        vendeurs[nom]['depoll_ratio'] = row[17].strip() if len(row) > 17 else ''
    i += 1

# ─────────────────────────────────────────────
# STEP 5 — FILL SECTION 5 LS (pure str.replace)
# ─────────────────────────────────────────────
# Template column order (7 columns including name):
# Collaborateur LS | Garantie Pneu | Géométrie | VCR | VCF | Plaquette | Dépoll.
#
# Template placeholder row (exact):
# |**Sandrine**|%|%|%|%|%|%|
# ──────────────────└── 6 % placeholders ──────────────────────────────────────┘

# COLS order must match template header exactly
COLS = [
    'gp_ratio',        # Garantie Pneu
    'geom_ratio',      # Géométrie
    'vcr_ratio',       # VCR
    'vcf_ratio',       # VCF
    'plaquette_ratio', # Plaquette
    'depoll_ratio',    # Dépoll.
]

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

written = []
for nom_template, nom_csv in NOM_MAP.items():
    # Exact template placeholder: |**Sandrine**|%|%|%|%|%|%|
    old = f"|**{nom_template}**|" + "%|" * 6

    data = vendeurs.get(nom_csv, {})
    vals = [data.get(key) or '0 %' for key in COLS]
    new  = f"|**{nom_template}**|" + "|".join(vals) + "|"

    rapport = rapport.replace(old, new)
    written.append(nom_template)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 6 — CONFIRM
# ─────────────────────────────────────────────

print(f"✅ Section 5 LS mise à jour : {rapport_path}")
print()
print(f"{'Vendeur':<12} {'GP':>8}  {'Géom':>8}  {'VCR':>8}  {'VCF':>8}  {'Plaq':>8}  {'Dépoll':>8}")
print("-" * 70)
for nom_template, nom_csv in NOM_MAP.items():
    d = vendeurs.get(nom_csv, {})
    print(f"{nom_template:<12} "
          f"{d.get('gp_ratio','0 %'):>8}  "
          f"{d.get('geom_ratio','0 %'):>8}  "
          f"{d.get('vcr_ratio','0 %'):>8}  "
          f"{d.get('vcf_ratio','0 %'):>8}  "
          f"{d.get('plaquette_ratio','0 %'):>8}  "
          f"{d.get('depoll_ratio','0 %'):>8}")
```
