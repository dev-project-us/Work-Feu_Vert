---
description: suivi vendeur mensuel
---

ALWAYS use this skill when the user types "/suivi-vendeur-mensuel". Fills Section 5
LS (Ratios de Vente par vendeur) of the monthly report from the Suivi Individuel CSV
in resources/monthly_recap/suivi vendeur/.

---

# Skill : Ratios de Vente Individuels — Section 5 LS Rapport Mensuel Feu Vert Annecy

## Vue d'ensemble

Ce skill lit le fichier CSV "Suivi Individuel des ratios atelier" depuis
`resources/monthly_recap/suivi vendeur/` et remplit la **Section 5 — Staff Libre
Service : Ratios de Vente** du rapport mensuel.

**Différence vs le skill hebdomadaire** :
- Dossier source : `monthly_recap/suivi vendeur/` au lieu de `resources/suivi vendeur/`
- Fichier rapport cible : `Rapport mensuel/rapport mensuel {mois} {année}.md`

Le parsing CSV, le mapping des blocs, et la logique d'écriture sont **identiques**
au skill hebdomadaire. Se référer à `suivi_vendeur.md` pour le détail complet.

---

## Workflow — Commande `/suivi-vendeur-mensuel`

### Étape 1 — Scanner le dossier

```python
import pathlib, glob, os

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("monthly_recap") / "suivi vendeur")
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_suivi = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'textbox390' in content:
        fichier_suivi = f
        break
```

### Étape 2 — Extraire le mois et l'année

```python
from datetime import datetime

# Ligne 2 : "ANNECY 2,01/03/2026 - 31/03/2026"
lines = content.splitlines()
date_line = lines[1]
date_part     = date_line.split(',')[1]
date_fin_str  = date_part.split(' - ')[1].strip()
date_fin      = datetime.strptime(date_fin_str, "%d/%m/%Y")
mois_num      = date_fin.month
annee         = date_fin.year

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

### Étape 4 — Extraire les données (Blocs 1, 2 et 4)

Parsing identique au skill hebdomadaire — même positions de colonnes, même logique
de fallback pour Garantie Pneu et Géométrie :

```python
import csv

NOM_MAP = {
    'Sandrine': 'SANDRINE R.',
    'Paul':     'PAUL P.',
    'Kamilia':  'KAMILIA A.',
    'Chouaib':  'CHOUAIB G.',
    'Pauline':  'PAULINE R.',
    'Valentin': 'VALENTIN C.',
}

vendeurs = {nom_csv: {
    'gp_ratio': '', 'geom_ratio': '', 'vcr_ratio': '',
    'vcf_ratio': '', 'plaquette_ratio': '', 'depoll_ratio': '',
} for nom_csv in NOM_MAP.values()}

# ── BLOC 1 : Garantie Pneu & Géométrie (header "textbox3,") ──────────────────
bloc1_idx = next(i for i, l in enumerate(lines) if l.startswith('textbox3,'))
i = bloc1_idx + 1
while i < len(lines) and lines[i].strip():
    row = list(csv.reader([lines[i]]))[0]
    nom = row[8].strip() if len(row) > 8 else ''
    if nom in vendeurs:
        gp   = row[22].strip() if len(row) > 22 else ''
        geom = row[28].strip() if len(row) > 28 else ''
        if '%' not in gp:
            gp = row[23].strip() if len(row) > 23 else ''
        if '%' not in geom:
            geom = row[29].strip() if len(row) > 29 else ''
        vendeurs[nom]['gp_ratio']   = gp
        vendeurs[nom]['geom_ratio'] = geom
    i += 1

# ── BLOC 2 : VCR, Plaquette, VCF (header "textbox590,") ──────────────────────
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

# ── BLOC 4 : Dépollution (header "textbox326,") ───────────────────────────────
bloc4_idx = next(i for i, l in enumerate(lines) if l.startswith('textbox326,'))
i = bloc4_idx + 1
while i < len(lines) and lines[i].strip():
    row = list(csv.reader([lines[i]]))[0]
    nom = row[9].strip() if len(row) > 9 else ''
    if nom in vendeurs:
        vendeurs[nom]['depoll_ratio'] = row[17].strip() if len(row) > 17 else ''
    i += 1
```

### Étape 5 — Écrire dans le rapport

```python
COLS = [
    ('gp_ratio',         'Garantie Pneu'),
    ('geom_ratio',       'Géométrie'),
    ('vcr_ratio',        'VCR'),
    ('vcf_ratio',        'VCF'),
    ('plaquette_ratio',  'Plaquette'),
    ('depoll_ratio',     'Dépoll.'),
]

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

for nom_template, nom_csv in NOM_MAP.items():
    if nom_csv not in vendeurs:
        continue
    data = vendeurs[nom_csv]
    vals = [data.get(key) or '0 %' for key, _ in COLS]
    old = f"| **{nom_template}** |" + " % |" * len(COLS)
    new = f"| **{nom_template}** | " + " | ".join(vals) + " |"
    rapport = rapport.replace(old, new)

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

### Étape 6 — Confirmer à l'utilisateur

Indiquer le fichier mis à jour et les valeurs écrites par vendeur.

---

## Mapping vendeurs CSV → Template

| Nom Template | Nom CSV |
|:--|:--|
| **Sandrine** | `SANDRINE R.` |
| **Paul** | `PAUL P.` |
| **Kamilia** | `KAMILIA A.` |
| **Chouaib** | `CHOUAIB G.` |
| **Pauline** | `PAULINE R.` |
| **Valentin** | `VALENTIN C.` |

> Vendeurs ignorés (absents du template) : Arnaud B., Elyne S., Isabelle P., Sofiane B.

---

## Règles de formatage

- Ratios déjà formatés `"24,2 %"` dans le CSV — conserver tel quel
- Séparateur décimal : **virgule**
- Valeur absente : `0 %`
- Ne jamais afficher les quantités brutes — uniquement le ratio %
