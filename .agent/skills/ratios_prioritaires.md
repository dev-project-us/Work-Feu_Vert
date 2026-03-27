---
description: ratios prioritaires
---

---
name: ratios_prioritaires
description: ratios prioritaires
---

# Skill : Ratios Prioritaires — Section 4 Rapport Hebdomadaire Feu Vert Annecy

## Vue d'ensemble

Ce skill décrit comment lire le fichier CSV des ratios atelier et remplir
la **Section 4 — Ratios Prioritaires (Performance Atelier)** du rapport hebdomadaire.

Fichier source :
`C:\Users\utilisateur203\Documents\Personnal\Second Brain\Resources\ratios prioritaires\`

Le fichier commence toujours par `Ratios_Atelier` mais son nom exact peut varier.
L'identifier par la présence de la colonne `libelleUnivers` dans son contenu.

---

## Workflow — Commande `/ratios`

Quand l'utilisateur tape `/ratios` ou `/chiffre`, exécuter :

### Étape 1 — Scanner le dossier ratios

```python
import glob, os

folder = r"C:\Users\utilisateur203\Documents\Personnal\Second Brain\Resources\ratios prioritaires"
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_ratios = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'libelleUnivers' in content:
        fichier_ratios = f
        break
```

### Étape 2 — Extraire la période et déterminer la semaine

```python
from datetime import datetime

# 2ème ligne : "ANNECY 2,16/03/2026-22/03/2026"
# Extraire la date de fin pour déterminer le numéro de semaine
date_fin_str = content.split('\r\n')[1].split(',')[1].split('-')[1]
date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
semaine = date_fin.isocalendar()[1]
```

### Étape 3 — Trouver le bon fichier rapport

```python
rapport_dir  = r"C:\Users\utilisateur203\Documents\Personnal\Second Brain\Rapport hebdomadaire"
rapport_path = os.path.join(rapport_dir, f"rapport hebdomadaire semaine {semaine}.md")

if not os.path.exists(rapport_path):
    # Le fichier n'existe pas encore — le créer depuis le template d'abord
    # (voir skill chiffre pour la procédure de création)
    raise FileNotFoundError(f"Rapport semaine {semaine} introuvable. Lance d'abord /chiffre.")
```

### Étape 4 — Extraire les valeurs des 6 KPIs

Appliquer le mapping et l'extraction décrits dans les sections
**Mapping des 6 KPIs** et **Extraction des valeurs** plus bas.

### Étape 5 — Écrire dans le rapport

```python
with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

# Remplacer chaque ligne de la Section 4
for kpi_name, vals in ratios.items():
    ecart = calc_ecart(vals['realise'], vals['objectif'])
    old = f"| **{kpi_name}** | % | "
    new = f"| **{kpi_name}** | {vals['realise']} | {vals['objectif']} | {ecart} | "
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

### Étape 6 — Confirmer à l'utilisateur

Indiquer le fichier mis à jour et les 6 valeurs écrites.
Signaler si un KPI n'a pas pu être trouvé dans le CSV.

---

## Structure du fichier CSV

### Bloc d'en-tête (2 premières lignes)
```
libelleAbrege,textbox38
ANNECY 2,16/03/2026-22/03/2026
```

### Bloc volume (après première ligne vide)
```
libelleGroupe,qteN,qteN_1,textbox20,textbox50
Nb OR,161,170,-9,-5 %
Forfaits Vidange,38,49,-11,-22 %
Pose Pneu,96,93,3,3 %
```

| Champ         | Signification          |
| :------------ | :--------------------- |
| `libelleGroupe` | Nom du groupe        |
| `qteN`        | Quantité semaine N     |
| `qteN_1`      | Quantité semaine N-1   |

### Bloc ratios (bloc principal)
```
libelleUnivers,textbox1,objectif,numN,denomN,ratioN,textbox113,textbox114,ratioN_1,textbox130,prixNum,Potentiel,textbox91
```

| Champ CSV      | Signification                    |
| :------------- | :------------------------------- |
| `libelleUnivers` | Catégorie du ratio             |
| `textbox1`     | Libellé complet du ratio         |
| `objectif`     | Objectif cible (%)               |
| `numN`         | Numérateur semaine N             |
| `denomN`       | Dénominateur semaine N           |
| `ratioN`       | Taux réalisé semaine N (%)       |
| `textbox113`   | Numérateur N-1                   |
| `textbox114`   | Dénominateur N-1                 |
| `ratioN_1`     | Taux réalisé N-1 (%)             |
| `textbox130`   | Écart N vs N-1 (pts)             |
| `Potentiel`    | Potentiel CA non réalisé (€)     |

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

## Extraction des valeurs

```python
import csv, io

# Parser le bloc ratios
lines = content.split('\r\n')
in_ratios_block = False
ratios = {}

KPI_MAP = {
    'Garantie Pneu / Pneus vendus':                 'Garantie Pneu',
    'Géométrie / Pose Pneu':                        'Géométrie',
    'Liquide de refroidissement / Nb OR':           'VCR (Refroid)',
    'Liquide de frein / Nb OR':                     'VCF (Frein)',
    'Plaquette / Nb OR':                            'Plaquette',
    'Traitements dépollution moteurs / Nb Vidange': 'Dépollution',
}

for line in lines:
    if line.startswith('libelleUnivers'):
        in_ratios_block = True
        continue
    if in_ratios_block and line.strip() == '':
        break
    if in_ratios_block:
        parts = next(csv.reader([line]))
        libelle = parts[1]
        if libelle in KPI_MAP:
            ratios[KPI_MAP[libelle]] = {
                'objectif': parts[2],
                'realise':  parts[5],   # ratioN
                'n1':       parts[8],   # ratioN_1
                'ecart':    parts[9],   # textbox130 (écart pts)
            }
```

---

## Calcul de l'écart vs objectif

```python
def calc_ecart(realise_str, objectif_str):
    try:
        r = float(realise_str.replace(' %','').replace(',','.'))
        o = float(objectif_str.replace(' %','').replace(',','.'))
        ecart = round(r - o, 1)
        return f"{ecart:+.1f} pts"
    except:
        return '-'
```

---

## Format de remplissage — Section 4

```markdown
| **Garantie Pneu** | {ratioN} | {objectif} | {ecart_obj} | |
| **Géométrie**     | {ratioN} | {objectif} | {ecart_obj} | |
| **VCR (Refroid)** | {ratioN} | {objectif} | {ecart_obj} | |
| **VCF (Frein)**   | {ratioN} | {objectif} | {ecart_obj} | |
| **Plaquette**     | {ratioN} | {objectif} | {ecart_obj} | |
| **Dépollution**   | {ratioN} | {objectif} | {ecart_obj} | |
```

La colonne **Statut** n'est pas dans le CSV — laisser vide.

---

## Règles de formatage

- Les ratios sont déjà en `%` dans le CSV — conserver tel quel
- Séparateur décimal : **virgule** (ex. `48 %`, `13 %`)
- Écart vs objectif : toujours afficher le signe (ex. `-2,0 pts`, `+6,0 pts`)
- Si la valeur est ` - ` dans le CSV, laisser la cellule vide dans le rapport
