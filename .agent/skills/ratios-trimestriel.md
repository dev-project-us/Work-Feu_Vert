---
name: ratios-trimestriel
description: >
  Fill Section 4 (Ratios Prioritaires — Moyenne Trimestrielle) of the Feu Vert Annecy
  quarterly report from the ratios CSV in resources/trimestres/ratios/.
  ALWAYS use when the user types /ratios-trimestriel, or says "remplis les ratios
  trimestriels", "ratios du trimestre", "analyse les ratios trimestriels".
---

# Skill : Ratios Prioritaires — Section 4 Rapport Trimestriel Feu Vert Annecy

## Vue d'ensemble

Ce skill lit le fichier CSV des ratios atelier depuis `resources/trimestres/ratios/`
et remplit la **Section 4 — Ratios Prioritaires (Moyenne Trimestrielle)** du rapport
trimestriel.

**Différences vs le skill hebdomadaire / mensuel** :
- Dossier source : `resources/trimestres/ratios/` (au lieu de `resources/ratios prioritaires/`
  hebdo ou `resources/monthly_recap/ratios prioritaires/` mensuel)
- Fichier rapport cible : `resources/trimestres/rapport trimestriel {T1/T2/T3/T4} {année}.md`
- Le template trimestriel Section 4 a **6 colonnes** : Réalisé (N), Objectif, Écart / Obj, N-1, Statut
- Les données CSV couvrent une **période de 3 mois** (trimestre complet)

Le parsing CSV, les 6 KPIs, et les calculs d'écart sont **identiques** au skill
hebdomadaire. Se référer à `ratios_prioritaires.md` pour le détail complet du format CSV.

---

## Workflow — Commande `/ratios-trimestriel`

### Étape 1 — Scanner le dossier ratios trimestriels

```python
import pathlib, glob, os

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("trimestres") / "ratios")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_ratios = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'libelleUnivers' in content:
        fichier_ratios = f
        break

if not fichier_ratios:
    raise FileNotFoundError("Aucun fichier CSV avec colonne 'libelleUnivers' trouvé dans resources/trimestres/ratios/")
```

### Étape 2 — Extraire la période et déterminer le trimestre

```python
from datetime import datetime

# 2ème ligne : "ANNECY 2,01/01/2026-31/03/2026"
date_fin_str = content.split('\r\n')[1].split(',')[1].split('-')[1]
date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
mois_fin = date_fin.month
annee = date_fin.year

TRIMESTRE_MAP = {3: 'T1', 6: 'T2', 9: 'T3', 12: 'T4'}
trimestre = TRIMESTRE_MAP.get(mois_fin, 'T?')
```

### Étape 3 — Trouver le fichier rapport trimestriel

```python
rapport_dir = str(find_dir("trimestres"))
rapport_path = os.path.join(rapport_dir, f"rapport trimestriel {trimestre} {annee}.md")

if not os.path.exists(rapport_path):
    raise FileNotFoundError(
        f"Rapport trimestriel {trimestre} {annee} introuvable. Lance d'abord /chiffre-trimestriel."
    )
```

### Étape 4 — Extraire les 6 KPIs

Parsing identique au skill hebdomadaire (`ratios_prioritaires.md`) :
- Localiser le bloc `libelleUnivers`
- Extraire `objectif`, `ratioN` (réalisé), `ratioN_1` (N-1)

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

Le template trimestriel Section 4 a 6 colonnes :
`Réalisé (N) | Objectif | Écart / Obj | N-1 | Statut`

```python
def parse_pct(s):
    clean = s.replace(' %','').replace(' pts','').replace(',','.').replace('+','').strip()
    try:
        return float(clean)
    except:
        return None

def fmt_pts(val):
    sign = '+' if val >= 0 else ''
    return f"{sign}{val:.1f} pts".replace('.', ',')

def statut(ecart_val):
    if ecart_val is None:
        return ''
    if ecart_val < 0:
        return '🔴'
    elif ecart_val == 0:
        return '🟡'
    else:
        return '🟢'

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
    n1_val = parse_pct(vals['n1'])

    ecart_obj = round(r - o, 1) if r is not None and o is not None else None

    # Template line to match:
    # | **Garantie Pneu** | % | 50 % | pts | % | |
    old = f"| **{kpi_name}** | % | {obj} | pts | % | |"
    new = (f"| **{kpi_name}** | {vals['realise']} | {obj} | "
           f"{fmt_pts(ecart_obj) if ecart_obj is not None else 'N/A'} | "
           f"{vals['n1']} | {statut(ecart_obj)} |")
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

### Étape 6 — Confirmer à l'utilisateur

Indiquer le fichier mis à jour et les 6 valeurs écrites.
Signaler si un KPI n'a pas pu être trouvé dans le CSV.

---

## Structure du fichier CSV

Identique au skill hebdomadaire (voir `ratios_prioritaires.md`).

### Bloc d'en-tête (2 premières lignes)
```
libelleAbrege,textbox38
ANNECY 2,01/01/2026-31/03/2026
```

> La seule différence est que la plage de dates couvre un **trimestre complet** (3 mois)
> au lieu d'une semaine ou un mois.

### Bloc volume (après première ligne vide)
```
libelleGroupe,qteN,qteN_1,textbox20,textbox50
Nb OR,500,480,20,4 %
Forfaits Vidange,120,130,-10,-8 %
Pose Pneu,300,290,10,3 %
```

### Bloc ratios (bloc principal)
```
libelleUnivers,textbox1,objectif,numN,denomN,ratioN,textbox113,textbox114,ratioN_1,textbox130,prixNum,Potentiel,textbox91
```

Se référer à `ratios_prioritaires.md` pour le mapping complet des champs CSV.

---

## Mapping des 6 KPIs Section 4

| KPI Section 4    | Libellé exact dans le CSV (`textbox1`)          | Objectif |
| :--------------- | :---------------------------------------------- | :------- |
| **Garantie Pneu**| `Garantie Pneu / Pneus vendus`                  | 50 %     |
| **Géométrie**    | `Géométrie / Pose Pneu`                         | 19 %     |
| **VCR (Refroid)**| `Liquide de refroidissement / Nb OR`            | 7 %      |
| **VCF (Frein)**  | `Liquide de frein / Nb OR`                      | 11 %     |
| **Plaquette**    | `Plaquette / Nb OR`                             | 11 %     |
| **Dépollution**  | `Traitements dépollution moteurs / Nb Vidange`  | 35 %     |

---

## Format de remplissage — Section 4 (Trimestriel)

Le template trimestriel Section 4 :
```markdown
| KPI Prioritaire | Réalisé (N) | Objectif | Écart / Obj | N-1 | Statut |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Garantie Pneu** | {ratioN} | {objectif} | {ecart_obj} | {ratioN_1} | {statut} |
| **Géométrie**     | {ratioN} | {objectif} | {ecart_obj} | {ratioN_1} | {statut} |
| **VCR (Refroid)** | {ratioN} | {objectif} | {ecart_obj} | {ratioN_1} | {statut} |
| **VCF (Frein)**   | {ratioN} | {objectif} | {ecart_obj} | {ratioN_1} | {statut} |
| **Plaquette**     | {ratioN} | {objectif} | {ecart_obj} | {ratioN_1} | {statut} |
| **Dépollution**   | {ratioN} | {objectif} | {ecart_obj} | {ratioN_1} | {statut} |
```

La colonne **Statut** est calculée depuis l'écart vs objectif : 🔴 (< 0), 🟡 (= 0), 🟢 (> 0).

---

## Différences clés vs hebdomadaire / mensuel

| Aspect | Hebdomadaire | Mensuel | **Trimestriel** |
|:-------|:-------------|:--------|:----------------|
| Dossier CSV | `resources/ratios prioritaires/` | `resources/monthly_recap/ratios prioritaires/` | **`resources/trimestres/ratios/`** |
| Rapport cible | `rapport hebdomadaire semaine {N}.md` | `rapport mensuel {mois} {année}.md` | **`rapport trimestriel {T1-T4} {année}.md`** |
| Colonnes Section 4 | 4 col. (Réalisé, Obj, Écart, Statut) | 6 col. (+N-1, Évol/N-1) | **6 col. (Réalisé, Obj, Écart/Obj, N-1, Statut)** |
| Période | 1 semaine | 1 mois | **3 mois (trimestre)** |

---

## Règles de formatage

- Les ratios sont déjà en `%` dans le CSV — conserver tel quel
- Séparateur décimal : **virgule** (ex: `48 %`, `13 %`)
- Écart vs objectif : toujours afficher le signe (ex: `-2,0 pts`, `+6,0 pts`)
- Si la valeur est ` - ` dans le CSV, laisser la cellule vide dans le rapport
