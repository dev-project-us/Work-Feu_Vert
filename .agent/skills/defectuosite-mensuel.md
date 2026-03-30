---
description: defectuosite mensuel
---

ALWAYS use this skill when the user types "/defectuosite-mensuel". Fills Section 5
Atelier (Taux de Défectuosité) of the monthly report from the CA_Main_d_oeuvre CSV
in resources/monthly_recap/defectuosite/.

---

# Skill : Taux de Défectuosité — Section 5 Atelier Rapport Mensuel Feu Vert Annecy

## Vue d'ensemble

Ce skill lit le fichier CSV CA Main d'œuvre depuis `resources/monthly_recap/defectuosite/`
et remplit la **Section 5 — Staff Atelier : Taux de Défectuosité** du rapport mensuel.

**Différence vs le skill hebdomadaire** :
- Dossier source : `monthly_recap/defectuosite/` au lieu de `resources/defectuosite/`
- Fichier rapport cible : `Rapport mensuel/rapport mensuel {mois} {année}.md`

Le parsing CSV, le mapping des colonnes, et la logique d'écriture sont **identiques**
au skill hebdomadaire. Se référer à `defectuosite.md` pour le détail complet.

---

## Workflow — Commande `/defectuosite-mensuel`

### Étape 1 — Scanner le dossier

```python
import pathlib, glob, os

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("monthly_recap") / "defectuosite")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_def = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'technicien3' in content:
        fichier_def = f
        break
```

### Étape 2 — Extraire le mois et l'année

```python
from datetime import datetime

# Ligne contenant "ANNECY SEYNOD,01/03/2026,31/03/2026"
lines = content.split('\r\n')
for line in lines:
    if 'ANNECY' in line and '/' in line:
        parts = line.split(',')
        date_fin_str = parts[2].strip()
        date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
        mois_num = date_fin.month
        annee    = date_fin.year
        break

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
        continue
    data = techniciens[nom_csv]
    vals = [data.get(col, '').strip() or '-' for col, _ in COLS]
    old = f"| **{nom_template}** |" + " |" * len(COLS)
    new = f"| **{nom_template}** | " + " | ".join(vals) + " |"
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

### Étape 6 — Confirmer à l'utilisateur

Indiquer le fichier mis à jour et les valeurs écrites par technicien.

---

## Mapping techniciens CSV → Template

| Nom CSV | Nom Template |
|:--|:--|
| `ALISHAN A.` | **Alishan A.** |
| `CHANDRACK K.` | **Chandrack K.** |
| `MOHAMMED ALI M.` | **Mohammed Ali M.** |
| `GAEL R.` | **Gael R.** |
| `DENIS D.` | **Denis D.** |

> Techniciens exclus (ignorer) : Ihsan, Emilie, Nathan, et tout autre nom absent du template.

---

## Règles de formatage

- Taux déjà formatés `"24,0 %"` dans le CSV — conserver tel quel
- `nb_diag_realises` : entier, sans `%`
- Valeur absente : `-`
- Séparateur décimal : **virgule**
