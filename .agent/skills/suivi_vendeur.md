---
description: suivi vendeur
---

---
name: suivi_vendeur
description: suivi vendeur
---

# Skill : Ratios de Vente Individuels — Section 5 LS Rapport Hebdomadaire Feu Vert Annecy

## Vue d'ensemble

Ce skill décrit comment lire le fichier CSV "Suivi Individuel des ratios atelier" et remplir
la **Section 5 — Staff Libre Service : Ratios de Vente** du rapport hebdomadaire.

Fichier source :
`C:\Users\mendo\Documents\Work\resources\suivi vendeur\`

Le fichier commence toujours par `Suivi Individuel des ratios atelier` mais son nom exact peut varier.
L'identifier par la présence de la colonne `textbox390` dans son contenu (colonne nom du bloc 1).

---

## Workflow — Commande `/suivi_vendeur`

### Étape 1 — Scanner le dossier

```python
import glob, os

folder = r"C:\Users\mendo\Documents\Work\resources\suivi vendeur"
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_suivi = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'textbox390' in content:
        fichier_suivi = f
        break
```

### Étape 2 — Extraire la période et déterminer la semaine

```python
from datetime import datetime

# Ligne 2 du fichier : "ANNECY 2,16/03/2026 - 22/03/2026"
lines = content.split('\r\n')
date_line = lines[1]  # 2ème ligne (index 1)
# Format : "ANNECY 2,DD/MM/YYYY - DD/MM/YYYY"
date_part = date_line.split(',')[1]           # "16/03/2026 - 22/03/2026"
date_fin_str = date_part.split(' - ')[1].strip()  # "22/03/2026"
date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
semaine = date_fin.isocalendar()[1]
```

### Étape 3 — Trouver le bon fichier rapport

```python
rapport_dir  = r"C:\Users\mendo\Documents\Work\Rapport hebdomadaire"
rapport_path = os.path.join(rapport_dir, f"rapport hebdomadaire semaine {semaine}.md")

if not os.path.exists(rapport_path):
    raise FileNotFoundError(f"Rapport semaine {semaine} introuvable. Lance d'abord /chiffre.")
```

### Étape 4 — Extraire le Bloc 1 (Garantie Pneu & Géométrie)

```python
import csv, io

# Trouver le bloc 1 : sa ligne header commence par "textbox3,"
bloc1_header_idx = None
for i, line in enumerate(lines):
    if line.startswith('textbox3,'):
        bloc1_header_idx = i
        break

# Parser les lignes du bloc 1 (jusqu'à la ligne vide suivante)
vendeurs = {}
i = bloc1_header_idx + 1
while i < len(lines) and lines[i].strip():
    row = list(csv.reader([lines[i]]))[0]
    nom_csv = row[8].strip() if len(row) > 8 else ''
    if nom_csv in NOM_MAP:
        vendeurs[nom_csv] = {
            # Garantie Pneu
            'gp_qty':   row[21].strip() if len(row) > 21 else '',
            'gp_ratio': row[22].strip() if len(row) > 22 else '',
            # Géométrie / Pose Pneu
            'geom_qty':   row[27].strip() if len(row) > 27 else '',
            'geom_ratio': row[28].strip() if len(row) > 28 else '',
            # TODO — Blocs 2, 3, 4 : VCR, VCF, NCI, Plaquette, Dépoll.
            # Voir section "Stubs à implémenter" plus bas
            'vcr_ratio':    None,
            'vcf_ratio':    None,
            'nci_ratio':    None,
            'plaquette_ratio': None,
            'depoll_ratio': None,
        }
    i += 1
```

### Étape 5 — Écrire dans le rapport

```python
with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

COLS = [
    ('gp_ratio',         'Garantie Pneu'),
    ('geom_ratio',       'Géométrie'),
    ('vcr_ratio',        'VCR'),
    ('vcf_ratio',        'VCF'),
    ('nci_ratio',        'NCI'),
    ('plaquette_ratio',  'Plaquette'),
    ('depoll_ratio',     'Dépoll.'),
]

for nom_template, nom_csv in NOM_MAP.items():
    if nom_csv not in vendeurs:
        continue
    data = vendeurs[nom_csv]
    vals = []
    for key, _ in COLS:
        v = data.get(key) or ''
        vals.append(v if v else 'N/A')
    old = f"| **{nom_template}** |" + " % |" * len(COLS)
    new = f"| **{nom_template}** | " + " | ".join(vals) + " |"
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

### Étape 6 — Confirmer à l'utilisateur

Indiquer le fichier mis à jour et les valeurs écrites par vendeur.
Signaler les colonnes encore à `N/A` (stubs non implémentés).

---

## Structure du fichier CSV

Le fichier contient **5 blocs** séparés par des lignes vides.
Chaque bloc a sa propre ligne header (`textbox...`) et ses propres données par vendeur.

```
Ligne 1 : libelleAbrege,textbox16          ← en-tête fichier
Ligne 2 : ANNECY 2,16/03/2026 - 22/03/2026 ← période (date fin = semaine)
Ligne 3 : (vide)
Ligne 4 : textbox3,textbox52,...            ← BLOC 1 header (Garantie Pneu, Géométrie)
Lignes  : données par vendeur
...
(ligne vide)
Ligne   : textbox590,...                    ← BLOC 2 header (VCR, VCF, Plaquette — TODO)
...
(ligne vide)
Ligne   : textbox620,...                    ← BLOC 3 header (Dépollution — TODO)
...
(ligne vide)
Ligne   : textbox326,...                    ← BLOC 4 header (TODO)
...
(ligne vide)
Ligne   : textbox81,...                     ← BLOC 5 header (données partielles)
```

**Parsing** : utiliser `open(..., encoding='utf-8-sig')` + lecture ligne par ligne.
Ne pas utiliser pandas avec header auto-détecté.

---

## Bloc 1 — Colonnes confirmées

Header : `textbox3,textbox52,textbox34,textbox60,textbox21,textbox392,textbox30,textbox88,textbox390,...`

| Position | Colonne CSV   | Signification                  | Statut    |
| :------- | :------------ | :----------------------------- | :-------- |
| 8        | `textbox390`  | Nom du vendeur (CSV)           | ✅ confirmé |
| 19       | `textbox66`   | Nb pneus vendus (N)            | ✅ confirmé |
| 20       | `textbox23`   | Nb pneus posés — dénominateur Géom. | ✅ confirmé |
| 21       | `textbox46`   | Garantie Pneu — quantité (N)   | ✅ confirmé |
| 22       | `textbox56`   | Garantie Pneu — ratio % (N)    | ✅ confirmé |
| 23       | `textbox36`   | Garantie Pneu — quantité (N-1) | ℹ️ non utilisé |
| 24       | `textbox37`   | Garantie Pneu — ratio % (N-1) | ℹ️ non utilisé |
| 27       | `textbox158`  | Géométrie / Pose Pneu — quantité (N) | ✅ confirmé |
| 28       | `textbox159`  | Géométrie / Pose Pneu — ratio % (N) | ✅ confirmé |

> **Note dénominateur** : Garantie Pneu utilise `textbox66` (pneus vendus).
> Géométrie utilise `textbox23` (pneus posés). Ces deux valeurs peuvent différer.

---

## Stubs à implémenter — Blocs 2, 3, 4

Les 5 ratios suivants sont en attente de mapping confirmé.

### Bloc 2 — Header : `textbox590,...`

Objectifs affichés : 30 %, 3 %, 3 %, **7 %**, **11 %**, **11 %**, 2 %, 1 %, 100 %, 60 %

- Nom du vendeur : position 11 (`textbox144`)
- Données individuelles : positions 12+ (paires qty/ratio)
- Dénominateur probable : Nb OR par vendeur (`textbox206`, position 32)

| KPI         | Objectif | Colonnes CSV (à confirmer) |
| :---------- | :------- | :------------------------- |
| **VCR**     | 7 %      | TODO                       |
| **VCF**     | 11 %     | TODO                       |
| **NCI**     | ?        | TODO                       |
| **Plaquette** | 11 %   | TODO                       |

### Bloc 3 — Header : `textbox620,...`

Objectifs affichés : **35 %**, 0,170, 18 %, 65 %, 50 %, 30 %

- Nom du vendeur : position 7 (`textbox493`)
- Données individuelles : positions 8+

| KPI           | Objectif | Colonnes CSV (à confirmer) |
| :------------ | :------- | :------------------------- |
| **Dépollution** | 35 %   | TODO                       |

---

## Mapping des noms vendeurs CSV → Template

| Nom Template | Nom CSV        |
| :----------- | :------------- |
| **Sandrine** | `SANDRINE R.`  |
| **Paul**     | `PAUL P.`      |
| **Kamilia**  | `KAMILIA A.`   |
| **Chouaib**  | `CHOUAIB G.`   |
| **Pauline**  | `PAULINE R.`   |
| **Valentin** | `VALENTIN C.`  |

```python
NOM_MAP = {
    'Sandrine': 'SANDRINE R.',
    'Paul':     'PAUL P.',
    'Kamilia':  'KAMILIA A.',
    'Chouaib':  'CHOUAIB G.',
    'Pauline':  'PAULINE R.',
    'Valentin': 'VALENTIN C.',
}
```

> Les vendeurs présents dans le CSV mais absents du template (Arnaud B., Elyne S.,
> Isabelle P., Sofiane B.) sont ignorés.

---

## Format de remplissage — Section 5 LS

```markdown
### Staff Libre Service : Ratios de Vente

|Collaborateur LS|Garantie Pneu|Géométrie|VCR|VCF|NCI|Plaquette|Dépoll.|
|:--|:--|:--|:--|:--|:--|:--|:--|
| **Sandrine** | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {nci} | {plaq} | {depoll} |
| **Paul**     | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {nci} | {plaq} | {depoll} |
| **Kamilia**  | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {nci} | {plaq} | {depoll} |
| **Chouaib**  | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {nci} | {plaq} | {depoll} |
| **Pauline**  | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {nci} | {plaq} | {depoll} |
| **Valentin** | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {nci} | {plaq} | {depoll} |
```

---

## Règles de formatage

- Les ratios sont déjà formatés `"24,2 %"` dans le CSV — conserver tel quel
- Séparateur décimal : **virgule** (ex. `16,7 %`)
- Si la valeur est absente dans le CSV pour un vendeur donné, afficher `N/A`
- Ne jamais afficher les quantités brutes (numérateur) — uniquement le ratio %
- Les colonnes TODO doivent être laissées à `N/A` jusqu'à mapping confirmé
