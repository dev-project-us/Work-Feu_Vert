---
description: ratios trimestriel
---

ALWAYS use this skill when the user types "/ratios-trimestriel". Execute the Python
script below in full. It scans the quarterly ratios CSV and fills Section 4 of the
quarterly report. Do NOT interpret or read the CSV yourself.
Other triggers: "remplis les ratios trimestriels", "ratios du trimestre".

---

# Skill : Ratios Prioritaires — Section 4 Rapport Trimestriel Feu Vert Annecy

## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité.**
Python fait tout : scan, extraction des 6 KPIs, calculs, remplissage Section 4.
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

TRIMESTRE_MAP = {3: 'T1', 6: 'T2', 9: 'T3', 12: 'T4'}

def parse_pct(s):
    return float(s.replace(' %','').replace(',','.').strip())

def fmt_pts(val):
    return f"{val:+.1f}".replace('.', ',') + ' pts'

def statut(ecart_val):
    if ecart_val > 0:    return '🟢'
    elif ecart_val == 0: return '🟡'
    else:                return '🔴'

# ─────────────────────────────────────────────
# STEP 1 — SCAN AND IDENTIFY CSV FILE
# ─────────────────────────────────────────────

folder    = str(find_dir("trimestres") / "ratios")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_ratios = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'libelleUnivers' in content:
        fichier_ratios = f
        break

assert fichier_ratios, "ERREUR : fichier ratios introuvable dans resources/trimestres/ratios/"

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE QUARTER AND YEAR
# ─────────────────────────────────────────────

# Line 2 format: "ANNECY 2,01/01/2026-31/03/2026"
lines        = content.replace('\r\n', '\n').split('\n')
date_fin_str = lines[1].split(',')[1].split('-')[1].strip()
date_fin     = datetime.strptime(date_fin_str, "%d/%m/%Y")
trimestre    = TRIMESTRE_MAP.get(date_fin.month, 'T?')
annee        = date_fin.year

# ─────────────────────────────────────────────
# STEP 3 — LOCATE REPORT FILE
# ─────────────────────────────────────────────

rapport_dir  = str(find_dir("trimestres"))
rapport_path = os.path.join(rapport_dir, f"rapport trimestriel {trimestre} {annee}.md")

assert os.path.exists(rapport_path), \
    f"ERREUR : Rapport trimestriel {trimestre} {annee} introuvable. Lance d'abord /chiffre-trimestriel."

# ─────────────────────────────────────────────
# STEP 4 — EXTRACT ALL 6 KPIs
# ─────────────────────────────────────────────

KPI_MAP = {
    'Garantie Pneu / Pneus vendus':                 'Garantie Pneu',
    'Géométrie / Pose Pneu':                        'Géométrie',
    'Liquide de refroidissement / Nb OR':           'VCR (Refroid)',
    'Liquide de frein / Nb OR':                     'VCF (Frein)',
    'Plaquette / Nb OR':                            'Plaquette',
    'Traitements dépollution moteurs / Nb Vidange': 'Dépollution',
}

OBJECTIFS = {
    'Garantie Pneu': '50 %',
    'Géométrie':     '19 %',
    'VCR (Refroid)': '7 %',
    'VCF (Frein)':   '11 %',
    'Plaquette':     '11 %',
    'Dépollution':   '35 %',
}

ratios   = {}
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
                    'realise': parts[5].strip(),   # ratioN
                    'n1':      parts[8].strip(),   # ratioN_1
                }

# ─────────────────────────────────────────────
# STEP 5 — FILL SECTION 4 (pure str.replace)
# ─────────────────────────────────────────────
# Template exact format (5 data columns — no Évolution/N-1 in quarterly):
# | **Garantie Pneu** | % | 50 % | pts | % | |
# Replace with:
# | **Garantie Pneu** | {realise} | 50 % | {ecart_obj} | {n1} | {statut} |

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

for kpi_name, obj_str in OBJECTIFS.items():
    if kpi_name not in ratios:
        print(f"⚠️  KPI non trouvé dans le CSV : {kpi_name}")
        continue

    vals      = ratios[kpi_name]
    realise   = vals['realise']
    n1        = vals['n1']
    ecart_obj = round(parse_pct(realise) - parse_pct(obj_str), 1)

    old = f"| **{kpi_name}** | % | {obj_str} | pts | % | |"
    new = f"| **{kpi_name}** | {realise} | {obj_str} | {fmt_pts(ecart_obj)} | {n1} | {statut(ecart_obj)} |"
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 6 — CONFIRM
# ─────────────────────────────────────────────

print(f"✅ Section 4 mise à jour : {rapport_path}")
print(f"{'KPI':<20} {'Réalisé':>8}  {'Obj':>6}  {'Écart':>10}  {'N-1':>8}  Statut")
print("-" * 65)
for kpi_name, obj_str in OBJECTIFS.items():
    if kpi_name in ratios:
        r  = ratios[kpi_name]['realise']
        n1 = ratios[kpi_name]['n1']
        e  = fmt_pts(round(parse_pct(r) - parse_pct(obj_str), 1))
        print(f"{kpi_name:<20} {r:>8}  {obj_str:>6}  {e:>10}  {n1:>8}  {statut(round(parse_pct(r)-parse_pct(obj_str),1))}")
    else:
        print(f"{kpi_name:<20} {'N/A':>8}")
```
