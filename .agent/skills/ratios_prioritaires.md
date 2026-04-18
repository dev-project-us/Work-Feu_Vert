---
description: ratios prioritaires
---

ALWAYS use this skill when the user types "/ratios" or when /chiffre completes.
Execute the Python script below in full. It scans the ratios CSV, extracts the
6 KPIs, computes ecart vs objective, and fills Section 4 of the weekly report.
Do NOT interpret or read the CSV yourself. Python does everything.

---

# Skill : Ratios Prioritaires — Section 4 Rapport Hebdomadaire Feu Vert Annecy

## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité.**
Python fait tout : scan, extraction, calculs, remplissage de la Section 4.
L'IA ne lit pas le CSV. L'IA ne calcule pas les écarts.

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

def calc_ecart(realise_str, objectif_str):
    try:
        r = float(realise_str.replace(' %', '').replace(',', '.').strip())
        o = float(objectif_str.replace(' %', '').replace(',', '.').strip())
        ecart = round(r - o, 1)
        s = f"{ecart:+.1f}".replace('.', ',')
        return s + ' pts'
    except:
        return '-'

def statut(ecart_str):
    try:
        val = float(ecart_str.replace(' pts', '').replace(',', '.').replace('+', '').strip())
        if val > 0:    return '🟢'
        elif val == 0: return '🟡'
        else:          return '🔴'
    except:
        return ''

# ─────────────────────────────────────────────
# STEP 1 — SCAN AND IDENTIFY CSV FILE
# ─────────────────────────────────────────────

folder    = str(find_dir("resources") / "ratios prioritaires")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_ratios = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'libelleUnivers' in content:
        fichier_ratios = f
        break

assert fichier_ratios, "ERREUR : fichier ratios introuvable dans resources/ratios prioritaires/"

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE WEEK NUMBER
# ─────────────────────────────────────────────

# Line 2 format: "ANNECY 2,16/03/2026-22/03/2026"
lines = content.replace('\r\n', '\n').split('\n')
date_fin_str = lines[1].split(',')[1].split('-')[1].strip()
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
# STEP 4 — EXTRACT ALL 6 KPIs FROM CSV
# ─────────────────────────────────────────────

KPI_MAP = {
    'Garantie Pneu / Pneus vendus':                 'Garantie Pneu',
    'Géométrie / Pose Pneu':                        'Géométrie',
    'Liquide de refroidissement / Nb OR':           'VCR (Refroid)',
    'Liquide de frein / Nb OR':                     'VCF (Frein)',
    'Plaquette / Nb OR':                            'Plaquette',
    'Traitements dépollution moteurs / Nb Vidange': 'Dépollution',
}

# Fixed objectives matching the template exactly
OBJECTIFS = {
    'Garantie Pneu': '50 %',
    'Géométrie':     '19 %',
    'VCR (Refroid)': '7 %',
    'VCF (Frein)':   '11 %',
    'Plaquette':     '11 %',
    'Dépollution':   '35 %',
}

ratios = {}
in_block = False

for line in lines:
    if line.startswith('libelleUnivers'):
        in_block = True
        continue
    if in_block and line.strip() == '':
        break
    if in_block:
        parts = next(csv.reader([line]))
        if len(parts) > 8:
            libelle = parts[1]
            if libelle in KPI_MAP:
                kpi_name = KPI_MAP[libelle]
                ratios[kpi_name] = {
                    'realise':  parts[5].strip(),   # ratioN
                    'objectif': parts[2].strip(),   # objectif from CSV
                    'n1':       parts[8].strip(),   # ratioN_1
                }

# ─────────────────────────────────────────────
# STEP 5 — FILL SECTION 4 (pure str.replace)
# ─────────────────────────────────────────────
# Template exact format per row:
# |**Garantie Pneu**|%|50 %|%||
# Replace with:
# |**Garantie Pneu**|{realise}|50 %|{ecart}|{statut}|

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

for kpi_name, obj_str in OBJECTIFS.items():
    if kpi_name not in ratios:
        print(f"⚠️  KPI non trouvé dans le CSV : {kpi_name}")
        continue

    vals    = ratios[kpi_name]
    realise = vals['realise']
    ecart   = calc_ecart(realise, obj_str)
    icon    = statut(ecart)

    old = f"|**{kpi_name}**|%|{obj_str}|%||"
    new = f"|**{kpi_name}**|{realise}|{obj_str}|{ecart}|{icon}|"
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 6 — CONFIRM
# ─────────────────────────────────────────────

print(f"✅ Section 4 mise à jour : {rapport_path}")
print(f"{'KPI':<20} {'Réalisé':>8}  {'Objectif':>8}  {'Écart':>10}  Statut")
print("-" * 60)
for kpi_name, obj_str in OBJECTIFS.items():
    if kpi_name in ratios:
        r = ratios[kpi_name]['realise']
        e = calc_ecart(r, obj_str)
        print(f"{kpi_name:<20} {r:>8}  {obj_str:>8}  {e:>10}  {statut(e)}")
    else:
        print(f"{kpi_name:<20} {'N/A':>8}")
```
