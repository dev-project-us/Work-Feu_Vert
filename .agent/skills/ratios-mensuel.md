---
description: ratios mensuel
---

ALWAYS use this skill when the user types "/ratios-mensuel", or when /chiffre-mensuel
completes. Fills Section 4 (Ratios Prioritaires) of the monthly report from the
ratios CSV in resources/monthly_recap/ratios prioritaires/.

---

# Skill : Ratios Prioritaires — Section 4 Rapport Mensuel Feu Vert Annecy

## Vue d'ensemble

Ce skill lit le fichier CSV des ratios atelier depuis `resources/monthly_recap/ratios prioritaires/`
et remplit la **Section 4 — Ratios Prioritaires** du rapport mensuel.

**Différence vs le skill hebdomadaire** :
- Dossier source : `monthly_recap/ratios prioritaires/` au lieu de `resources/ratios prioritaires/`
- Fichier rapport cible : `Rapport mensuel/rapport mensuel {mois} {année}.md`
- Le template mensuel a 2 colonnes supplémentaires : N-1 et Évolution/N-1 → les renseigner

Le parsing CSV, les 6 KPIs, et les calculs d'écart sont **identiques** au skill hebdomadaire.
Se référer à `ratios_prioritaires.md` pour le détail complet.

---

## Workflow — Commande `/ratios-mensuel`

### Étape 1 — Scanner le dossier

```python
import pathlib, glob, os

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("monthly_recap") / "ratios prioritaires")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_ratios = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'libelleUnivers' in content:
        fichier_ratios = f
        break
```

### Étape 2 — Extraire le mois et l'année

```python
from datetime import datetime

# 2ème ligne : "ANNECY 2,01/03/2026-31/03/2026"
date_fin_str = content.split('\r\n')[1].split(',')[1].split('-')[1]
date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
mois_num = date_fin.month
annee    = date_fin.year

MOIS_FR = {
    1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
    5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
    9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
}
mois_str = MOIS_FR[mois_num]
```

### Étape 3 — Trouver le fichier rapport mensuel

```python
rapport_dir  = str(find_dir("Rapport mensuel"))
rapport_path = os.path.join(rapport_dir, f"rapport mensuel {mois_str} {annee}.md")

if not os.path.exists(rapport_path):
    raise FileNotFoundError(f"Rapport mensuel {mois_str} {annee} introuvable. Lance d'abord /chiffre-mensuel.")
```

### Étape 4 — Extraire les 6 KPIs

Parsing identique au skill hebdomadaire (`ratios_prioritaires.md`) :
- Localiser le bloc `libelleUnivers`
- Extraire `objectif`, `ratioN` (réalisé), `ratioN_1` (N-1)
- Évolution / N-1 = `ratioN - ratioN_1` (calculé, non lu depuis le CSV)

```python
import csv

KPI_MAP = {
    'Garantie Pneu / Pneus vendus':                 'Garantie Pneu',
    'Géométrie / Pose Pneu':                        'Géométrie',
    'Liquide de refroidissement / Nb OR':           'VCR (Refroid)',
    'Liquide de frein / Nb OR':                     'VCF (Frein)',
    'Plaquette / Nb OR':                            'Plaquette',
    'Traitements dépollution moteurs / Nb Vidange': 'Dépollution',
}

lines = content.split('\n')
in_ratios_block = False
ratios = {}

for line in lines:
    if line.startswith('libelleUnivers'):
        in_ratios_block = True
        continue
    if in_ratios_block and line.strip() == '':
        break
    if in_ratios_block:
        parts = next(csv.reader([line]))
        if len(parts) > 8:
            libelle = parts[1]
            if libelle in KPI_MAP:
                ratios[KPI_MAP[libelle]] = {
                    'objectif': parts[2],
                    'realise':  parts[5],  # ratioN
                    'n1':       parts[8],  # ratioN_1
                }
```

### Étape 5 — Écrire dans le rapport

Le template mensuel Section 4 a 6 colonnes : Réalisé, Objectif, Écart/Obj, N-1, Évolution/N-1, Statut.

```python
def parse_pct(s):
    return float(s.replace(' %','').replace(',','.'))

def fmt_pts(val):
    sign = '+' if val >= 0 else ''
    return f"{sign}{val:.1f} pts".replace('.', ',')

def statut(ecart_val):
    if ecart_val is None:
        return ''
    if ecart_val < 0:
        return 'En retard'
    elif ecart_val == 0:
        return 'Atteint'
    else:
        return 'Dépassé'

OBJECTIFS = {
    'Garantie Pneu': '50 %',
    'Géométrie':     '19 %',
    'VCR (Refroid)': '7 %',
    'VCF (Frein)':   '11 %',
    'Plaquette':     '11 %',
    'Dépollution':   '35 %',
}

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

for kpi_name, vals in ratios.items():
    obj = OBJECTIFS.get(kpi_name, vals['objectif'])
    r   = parse_pct(vals['realise'])
    o   = parse_pct(obj)
    n1  = parse_pct(vals['n1'])
    ecart_obj = round(r - o, 1)
    ecart_n1  = round(r - n1, 1)  # delta Réalisé - N-1
    old = f"|**{kpi_name}**|%|{obj}|pts|%|pts||"
    new = (f"|**{kpi_name}**|{vals['realise']}|{obj}|"
           f"{fmt_pts(ecart_obj)}|{vals['n1']}|{fmt_pts(ecart_n1)}|{statut(ecart_obj)}|")
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

### Étape 6 — Confirmer à l'utilisateur

Indiquer le fichier mis à jour et les 6 valeurs écrites.
Signaler si un KPI n'a pas pu être trouvé dans le CSV.

---

## Règles de formatage

- Ratios déjà en `%` dans le CSV — conserver tel quel
- Séparateur décimal : **virgule**
- Écart vs objectif : toujours signé (`-2,0 pts`, `+6,0 pts`)
- Valeur absente (` - ` dans le CSV) : laisser la cellule vide
