---
name: defectuosite-trimestriel
description: >
  Fill the "Staff Atelier : Taux de Défectuosité" section of the Feu Vert Annecy
  quarterly report from the CA_Main_d_oeuvre CSV in resources/trimestres/defectuosité/.
  ALWAYS use when the user types /defectuosite-trimestriel, or says "remplis les
  défectuosités trimestrielles", "analyse défectuosité du trimestre".
---

# Skill : Taux de Défectuosité — Section 5 Atelier Rapport Trimestriel Feu Vert Annecy

## Vue d'ensemble

Ce skill lit le fichier CSV CA Main d'œuvre depuis `resources/trimestres/defectuosité/`
et remplit la **Section 5 — Staff Atelier : Taux de Défectuosité** du rapport trimestriel.

**Différences vs le skill hebdomadaire / mensuel** :
- Dossier source : `resources/trimestres/defectuosité/` (au lieu de `resources/defectuosite/` ou `Resources mensuelles/defectuosite/`)
- Fichier rapport cible : `resources/trimestres/rapport trimestriel T{n} {année}.md`
- Colonnes réduites : le template trimestriel utilise **8 colonnes** (Nb OR, Déf. Bat., Disq. AV, Disq. AR, Plaq. AV, Plaq. AR, Déf. VCF, Déf. VCR) au lieu des 13 du template hebdomadaire
- Techniciens : **4 techniciens** (Chandrack K., Mohammed Ali M., Gael R., Denis D.) — Alishan A. n'est pas dans le template trimestriel

Le parsing CSV et les règles de formatage sont **identiques** au skill hebdomadaire.
Se référer à `defectuosite.md` pour le détail complet du parsing.

---

## Workflow — Commande `/defectuosite-trimestriel`

### Étape 1 — Scanner le dossier

```python
import pathlib, glob, os

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("trimestres") / "defectuosité")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_def = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'technicien3' in content:
        fichier_def = f
        break
```

### Étape 2 — Extraire le trimestre et l'année

```python
from datetime import datetime

# Ligne contenant "ANNECY SEYNOD,01/01/2026,31/03/2026"
lines = content.split('\r\n')
for line in lines:
    if 'ANNECY' in line and '/' in line:
        parts = line.split(',')
        date_fin_str = parts[2].strip()
        date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
        mois_fin = date_fin.month
        annee    = date_fin.year
        break

# Déterminer le trimestre depuis le mois de fin
TRIM_MAP = {3: 1, 6: 2, 9: 3, 12: 4}
trimestre = TRIM_MAP.get(mois_fin, (mois_fin - 1) // 3 + 1)
```

### Étape 3 — Trouver le fichier rapport trimestriel

```python
rapport_dir = str(find_dir("trimestres"))
rapport_path = os.path.join(rapport_dir, f"rapport trimestriel T{trimestre} {annee}.md")

if not os.path.exists(rapport_path):
    raise FileNotFoundError(f"Rapport trimestriel T{trimestre} {annee} introuvable. Lance d'abord /chiffre-trimestriel.")
```

### Étape 4 — Extraire le bloc synthèse par technicien

Parsing identique au skill hebdomadaire :

```python
import csv, io

# Dernier bloc commençant par "technicien3"
blocks = content.split('\r\n\r\n')
synthese_block = None
for block in blocks:
    if block.startswith('technicien3'):
        synthese_block = block

reader = csv.DictReader(io.StringIO(synthese_block))
techniciens = {}
for row in reader:
    nom = row['technicien3'].strip()
    techniciens[nom] = row
```

### Étape 5 — Écrire dans le rapport

```python
# Mapping nom template → clé CSV (4 techniciens pour le trimestriel)
NOM_MAP = {
    'Chandrack K.':    'CHANDRACK K.',
    'Mohammed Ali M.': 'MOHAMMED ALI M.',
    'Gael R.':         'GAEL R.',
    'Denis D.':        'DENIS D.',
}

# 8 colonnes du template trimestriel (sous-ensemble du template hebdo)
COLS = [
    ('nb_diag_realises',        'Nb OR'),
    ('taux_def_batterie3',      'Déf. Bat.'),
    ('taux_def_disques_av3',    'Disq. AV'),
    ('taux_def_disques_ar3',    'Disq. AR'),
    ('taux_def_plaquettes_av3', 'Plaq. AV'),
    ('taux_def_plaquettes_ar3', 'Plaq. AR'),
    ('taux_def_vcf3',           'Déf. VCF'),
    ('taux_def_vcr3',           'Déf. VCR'),
]

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

for nom_template, nom_csv in NOM_MAP.items():
    if nom_csv not in techniciens:
        continue
    data = techniciens[nom_csv]
    vals = [data.get(col, '').strip() or '-' for col, _ in COLS]
    # Reconstruire la ligne markdown
    old = f"| **{nom_template}** |" + " |" * len(COLS)
    new = f"| **{nom_template}** | " + " | ".join(vals) + " |"
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

### Étape 6 — Confirmer à l'utilisateur

Indiquer le fichier mis à jour et les valeurs écrites par technicien.

---

## Mapping des colonnes CSV → Template Trimestriel

| Colonne CSV               | Colonne Template       |
| :------------------------ | :--------------------- |
| `technicien3`             | **Technicien**         |
| `nb_diag_realises`        | **Nb OR**              |
| `taux_def_batterie3`      | **Déf. Bat.**          |
| `taux_def_disques_av3`    | **Disq. AV**           |
| `taux_def_disques_ar3`    | **Disq. AR**           |
| `taux_def_plaquettes_av3` | **Plaq. AV**           |
| `taux_def_plaquettes_ar3` | **Plaq. AR**           |
| `taux_def_vcf3`           | **Déf. VCF**           |
| `taux_def_vcr3`           | **Déf. VCR**           |

> **Note** : Le template trimestriel n'inclut pas les colonnes NCI, Géométrie, BEG,
> Amortisseurs et Pare-brise présentes dans le template hebdomadaire.

---

## Mapping techniciens CSV → Template

| Nom CSV | Nom Template |
|:--|:--|
| `CHANDRACK K.` | **Chandrack K.** |
| `MOHAMMED ALI M.` | **Mohammed Ali M.** |
| `GAEL R.` | **Gael R.** |
| `DENIS D.` | **Denis D.** |

> Techniciens exclus (ignorer) : Alishan, Ihsan, Emilie, Nathan, Ewan,
> et tout autre nom absent du template trimestriel.

---

## Règles de formatage

- Taux déjà formatés `"24,0 %"` dans le CSV — conserver tel quel
- `nb_diag_realises` : entier, sans `%`
- Valeur absente : `-`
- Séparateur décimal : **virgule**

---

## Identification du fichier CSV

| Fichier | Pattern | Contenu |
|:--------|:--------|:--------|
| `CA Main d'oeuvre par TMS*.csv` | Contient `technicien3` | Taux de défectuosité par technicien sur le trimestre |

Le fichier est placé dans `resources/trimestres/defectuosité/`.
