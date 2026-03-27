---
description: defectuosite
---

---
name: defectuosite
description: defectuosite
---

# Skill : Taux de Défectuosité — Section 5 Atelier Rapport Hebdomadaire Feu Vert Annecy

## Vue d'ensemble

Ce skill décrit comment lire le fichier CSV CA Main d'œuvre par TMS et remplir
la **Section 5 — Staff Atelier : Taux de Défectuosité** du rapport hebdomadaire.

Fichier source :
`C:\Users\utilisateur203\Documents\Personnal\Second Brain\Resources\defectuosite\`

Le fichier commence toujours par `CA_Main_d_oeuvre` mais son nom exact peut varier.
L'identifier par la présence de la colonne `technicien3` dans son contenu.

---

## Workflow — Commande `/defectuosite` ou `/chiffre`

### Étape 1 — Scanner le dossier

```python
import glob, os

folder = r"C:\Users\utilisateur203\Documents\Personnal\Second Brain\Resources\defectuosite"
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_def = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'technicien3' in content:
        fichier_def = f
        break
```

### Étape 2 — Extraire la période et déterminer la semaine

```python
from datetime import datetime

# Ligne 5 du fichier : "ANNECY SEYNOD,16/03/2026,22/03/2026"
lines = content.split('\r\n')
for line in lines:
    if 'ANNECY' in line and '/' in line:
        parts = line.split(',')
        date_fin_str = parts[2].strip()
        date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
        semaine = date_fin.isocalendar()[1]
        break
```

### Étape 3 — Trouver le bon fichier rapport

```python
rapport_dir  = r"C:\Users\utilisateur203\Documents\Personnal\Second Brain\Rapport hebdomadaire"
rapport_path = os.path.join(rapport_dir, f"rapport hebdomadaire semaine {semaine}.md")

if not os.path.exists(rapport_path):
    raise FileNotFoundError(f"Rapport semaine {semaine} introuvable. Lance d'abord /chiffre.")
```

### Étape 4 — Extraire le bloc de synthèse par technicien

### Étape 5 — Écrire dans le rapport

### Étape 6 — Confirmer à l'utilisateur

---

## Structure du fichier CSV

Le fichier contient plusieurs blocs séparés par des lignes vides.
**Seul le dernier bloc est utile** pour la section 5.

### Bloc synthèse (dernier bloc du fichier)

```
technicien3,nb_diag_realises,taux_def_batterie3,taux_def_disques_av3,
taux_def_disques_ar3,taux_def_plaquettes_av3,taux_def_plaquettes_ar3,
taux_def_nci3,taux_def_vcf3,taux_def_geometrie3,taux_def_beg3,
taux_def_vcr3,taux_def_amortisseurs3,taux_def_pare_brise
```

C'est une table propre — utiliser `csv.reader` directement sur ce bloc.

---

## Mapping des colonnes CSV → Template Section 5

| Colonne CSV               | Colonne Template          |
| :------------------------ | :------------------------ |
| `technicien3`             | **Technicien**            |
| `nb_diag_realises`        | **Nb OR**                 |
| `taux_def_batterie3`      | **Déf. Batterie**         |
| `taux_def_disques_av3`    | **Disq AV**               |
| `taux_def_disques_ar3`    | **Disq AR**               |
| `taux_def_plaquettes_av3` | **Plaq Av**               |
| `taux_def_plaquettes_ar3` | **Plaq Ar**               |
| `taux_def_nci3`           | **Déf. NCI**              |
| `taux_def_vcf3`           | **Déf. VCF (Frein)**      |
| `taux_def_geometrie3`     | **Déf. Géo**              |
| `taux_def_beg3`           | **Def BEG**               |
| `taux_def_vcr3`           | **Déf. VCR**              |
| `taux_def_amortisseurs3`  | **Déf. Amort**            |
| `taux_def_pare_brise`     | **Déf. Pare-brise**       |

---

## Extraction du bloc synthèse

```python
import csv, io

# Trouver le bloc commençant par "technicien3"
blocks = content.split('\r\n\r\n')
synthese_block = None
for block in blocks:
    if block.startswith('technicien3'):
        synthese_block = block
        break

# Parser le bloc
techniciens = {}
reader = csv.DictReader(io.StringIO(synthese_block))
for row in reader:
    nom = row['technicien3'].strip()
    techniciens[nom] = row
```

---

## Mapping des noms techniciens CSV → Template

Les noms dans le CSV sont en MAJUSCULES. Le template utilise une capitalisation mixte.

| Nom CSV            | Nom Template          |
| :----------------- | :-------------------- |
| `ALISHAN A.`       | **Alishan A.**        |
| `CHANDRACK K.`     | **Chandrack K.**      |
| `MOHAMMED ALI M.`  | **Mohammed Ali M.**   |
| `GAEL R.`          | **Gael R.**           |
| `DENIS D.`         | **Denis D.**          |

> Si un technicien du CSV n'est pas dans le template (ex. EMILIE R., EWAN B.,
> IHSAN M., NATHAN D.), ignorer sa ligne.
> Si un technicien du template est absent du CSV (ex. Denis D.), laisser
> sa ligne vide dans le rapport.

---

## Écriture dans le rapport

```python
# Mapping nom template → clé CSV
NOM_MAP = {
    'Alishan A.':      'ALISHAN A.',
    'Chandrack K.':    'CHANDRACK K.',
    'Mohammed Ali M.': 'MOHAMMED ALI M.',
    'Gael R.':         'GAEL R.',
    'Denis D.':        'DENIS D.',
}

COLS = [
    ('nb_diag_realises',        'Nb OR'),
    ('taux_def_batterie3',      'Déf. Batterie'),
    ('taux_def_disques_av3',    'Disq AV'),
    ('taux_def_disques_ar3',    'Disq AR'),
    ('taux_def_plaquettes_av3', 'Plaq Av'),
    ('taux_def_plaquettes_ar3', 'Plaq Ar'),
    ('taux_def_nci3',           'Déf. NCI'),
    ('taux_def_vcf3',           'Déf. VCF (Frein)'),
    ('taux_def_geometrie3',     'Déf. Géo'),
    ('taux_def_beg3',           'Def BEG'),
    ('taux_def_vcr3',           'Déf. VCR'),
    ('taux_def_amortisseurs3',  'Déf. Amort'),
    ('taux_def_pare_brise',     'Déf. Pare-brise'),
]

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

for nom_template, nom_csv in NOM_MAP.items():
    if nom_csv not in techniciens:
        continue  # Laisser la ligne vide
    data = techniciens[nom_csv]
    vals = [data.get(col, '').strip() or '-' for col, _ in COLS]
    # Reconstruire la ligne markdown
    old = f"| **{nom_template}** |" + " |" * len(COLS)
    new = f"| **{nom_template}** | " + " | ".join(vals) + " |"
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

---

## Règles de formatage

- Les taux sont déjà formatés `"24,0 %"` dans le CSV — conserver tel quel
- `nb_diag_realises` est un entier — afficher sans `%`
- Si la valeur est vide dans le CSV, afficher `-`
- Séparateur décimal : **virgule** (ex. `24,0 %`)
