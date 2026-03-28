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
a folder named `resources/suivi vendeur/`

Le fichier commence toujours par `Suivi Individuel des ratios atelier` mais son nom exact peut varier.
L'identifier par la présence de la colonne `textbox390` dans son contenu (colonne nom du bloc 1).

---

## Workflow — Commande `/suivi_vendeur`

### Étape 1 — Scanner le dossier

```python
import pathlib, glob, os

def find_dir(name):
    """Locate a directory by name, searching up from the current working directory.
    Works on any machine as long as a folder named `name` exists in the tree."""
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("resources") / "suivi vendeur")
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
lines = content.splitlines()
date_line = lines[1]
# Format : "ANNECY 2,DD/MM/YYYY - DD/MM/YYYY"
date_part = date_line.split(',')[1]               # "16/03/2026 - 22/03/2026"
date_fin_str = date_part.split(' - ')[1].strip()  # "22/03/2026"
date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
semaine = date_fin.isocalendar()[1]
```

### Étape 3 — Trouver le bon fichier rapport

```python
rapport_dir  = str(find_dir("Rapport hebdomadaire"))
rapport_path = os.path.join(rapport_dir, f"rapport hebdomadaire semaine {semaine}.md")

if not os.path.exists(rapport_path):
    raise FileNotFoundError(f"Rapport semaine {semaine} introuvable. Lance d'abord /chiffre.")
```

### Étape 4 — Extraire les données (Blocs 1, 2 et 4)

```python
import csv

# Initialiser le dictionnaire vendeurs
vendeurs = {nom_csv: {
    'gp_ratio':        '',
    'geom_ratio':      '',
    'vcr_ratio':       '',
    'vcf_ratio':       '',
    'plaquette_ratio': '',
    'depoll_ratio':    '',
} for nom_csv in NOM_MAP.values()}

# ── BLOC 1 : Garantie Pneu & Géométrie ────────────────────────────────────────
# Header commence par "textbox3,"
# Note : pour certains vendeurs (peu de ventes pneu), le ratio GP est décalé d'une
# position (pos 23 au lieu de 22) et le ratio Géom d'une position (pos 29 au lieu de 28).
# → Toujours vérifier si la valeur extraite contient '%' ; sinon essayer la position suivante.
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
        vendeurs[nom]['gp_ratio']   = gp    # textbox56 (ou pos 23)
        vendeurs[nom]['geom_ratio'] = geom  # textbox159 (ou pos 29)
    i += 1

# ── BLOC 2 : VCR, Plaquette, VCF ──────────────────────────────────────────────
# Header commence par "textbox590,"
# Nom vendeur : position 11 (textbox144)
bloc2_idx = next(i for i, l in enumerate(lines) if l.startswith('textbox590,'))
i = bloc2_idx + 1
while i < len(lines) and lines[i].strip():
    row = list(csv.reader([lines[i]]))[0]
    nom = row[11].strip() if len(row) > 11 else ''
    if nom in vendeurs:
        vendeurs[nom]['vcr_ratio']       = row[19].strip() if len(row) > 19 else ''  # textbox156
        vendeurs[nom]['plaquette_ratio'] = row[21].strip() if len(row) > 21 else ''  # textbox146
        vendeurs[nom]['vcf_ratio']       = row[23].strip() if len(row) > 23 else ''  # textbox136
    i += 1

# ── BLOC 4 : NCI (Traitement Dépollution) ─────────────────────────────────────
# Header commence par "textbox326,"
# Nom vendeur : position 9 (textbox14)
bloc4_idx = next(i for i, l in enumerate(lines) if l.startswith('textbox326,'))
i = bloc4_idx + 1
while i < len(lines) and lines[i].strip():
    row = list(csv.reader([lines[i]]))[0]
    nom = row[9].strip() if len(row) > 9 else ''
    if nom in vendeurs:
        vendeurs[nom]['depoll_ratio'] = row[17].strip() if len(row) > 17 else ''  # textbox201
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
    ('plaquette_ratio',  'Plaquette'),
    ('depoll_ratio',     'Dépoll.'),
]

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
Toutes les colonnes sont désormais implémentées — aucun stub restant.

---

## Structure du fichier CSV

Le fichier contient **5 blocs** séparés par des lignes vides, correspondant aux 4 pages du PDF.

```
Ligne 1 : libelleAbrege,textbox16           ← en-tête fichier
Ligne 2 : ANNECY 2,16/03/2026 - 22/03/2026  ← période
Ligne 3 : (vide)
Ligne 4 : textbox3,...     ← BLOC 1 — PDF page 1 : Pneumatique (Garantie Pneu, Géométrie)
...
(vide)
           textbox590,...  ← BLOC 2 — PDF page 2 : Ratios sur OR (VCR, Plaquette, VCF)
...
(vide)
           textbox620,...  ← BLOC 3 — PDF page 3 : Ratio sur Vidange (Dépoll. — TODO)
...
(vide)
           textbox326,...  ← BLOC 4 — PDF page 4 : Relais de croissance (NCI)
...
(vide)
           textbox81,...   ← BLOC 5 — PDF page 4 : Suivi vente (données partielles)
```

**Parsing** : utiliser `open(..., encoding='utf-8-sig')` + lecture ligne par ligne.
Ne pas utiliser pandas avec header auto-détecté.

---

## Bloc 1 — PDF page 1 : Pneumatique

Header : `textbox3,textbox52,textbox34,textbox60,textbox21,textbox392,textbox30,textbox88,textbox390,...`

| Position | Colonne CSV  | Label PDF                    | KPI Template       | Statut      |
| :------- | :----------- | :--------------------------- | :----------------- | :---------- |
| 8        | `textbox390` | Nom vendeur                  | —                  | ✅ confirmé |
| 19       | `textbox66`  | TOTAL PNEUS VDUS             | dénominateur GP    | ✅ confirmé |
| 20       | `textbox23`  | TOTAL POSE PNEU              | dénominateur Géom. | ✅ confirmé |
| 21       | `textbox46`  | GARANTIE / PNEUS VENDUS — qty | —                 | ✅ confirmé |
| **22**   | **`textbox56`** | **GARANTIE / PNEUS VENDUS — ratio** | **Garantie Pneu** | ✅ confirmé |
| 23       | `textbox36`  | GARANTIE / POSE PNEU — qty (N-1) | —             | ℹ️ non utilisé |
| 24       | `textbox37`  | GARANTIE / POSE PNEU — ratio (N-1) | —           | ℹ️ non utilisé |
| 27       | `textbox158` | GEOM. / POSE PNEU — qty     | —                  | ✅ confirmé |
| **28**   | **`textbox159`** | **GEOM. / POSE PNEU — ratio** | **Géométrie** | ✅ confirmé |

> **Objectif Garantie Pneu : 50 %** — dénominateur = pneus vendus (`textbox66`)
> **Objectif Géométrie : 19 %** — dénominateur = pneus posés (`textbox23`)
> Ces deux dénominateurs peuvent différer.

---

## Bloc 2 — PDF page 2 : Ratios sur OR

Header : `textbox590,textbox198,textbox108,textbox180,textbox154,textbox142,textbox134,...`

Colonnes PDF dans l'ordre : MULTIDIAG (30%), CLIM (3%), COURROIE DISTRIB (3%),
**LIQ. DE REF. (7%)**, **PLAQUETTE (11%)**, **LIQ. DE FREIN (11%)**, REMPL. FLEX (2%),
REMPL. MACH (1%), RECTIF. TAMBOUR (100%), DISQUES (60%), NB OR

- Nom vendeur : position 11 (`textbox144`)
- Dénominateur : Nb OR par vendeur (`textbox206`, position 32)

| Position | Colonne CSV   | Label PDF          | KPI Template  | Objectif | Statut      |
| :------- | :------------ | :----------------- | :------------ | :------- | :---------- |
| 12       | `textbox208`  | MULTIDIAG — qty    | —             | 30 %     | ℹ️ non utilisé |
| 13       | `textbox209`  | MULTIDIAG — ratio  | —             | 30 %     | ℹ️ non utilisé |
| 18       | `textbox155`  | LIQ. DE REF. — qty | —             | 7 %      | ✅ confirmé |
| **19**   | **`textbox156`** | **LIQ. DE REF. — ratio** | **VCR** | **7 %** | ✅ confirmé |
| 20       | `textbox145`  | PLAQUETTE — qty    | —             | 11 %     | ✅ confirmé |
| **21**   | **`textbox146`** | **PLAQUETTE — ratio** | **Plaquette** | **11 %** | ✅ confirmé |
| 22       | `textbox135`  | LIQ. DE FREIN — qty | —            | 11 %     | ✅ confirmé |
| **23**   | **`textbox136`** | **LIQ. DE FREIN — ratio** | **VCF** | **11 %** | ✅ confirmé |
| 32       | `textbox206`  | NB OR — qty        | —             | —        | ℹ️ dénominateur |

---

## Bloc 4 — PDF page 4 : Relais de croissance

Header : `textbox326,textbox165,textbox171,textbox214,textbox199,textbox100,textbox96,...`

Colonnes PDF dans l'ordre : OBUS (70%), RECH FUITES (40%), BOUT FILT. (5%),
**TRAIT. DEPOLLUTION (35%)**, CT (3%), NB BATT. VENDUES (30%), NB BATT. POSEES (7%),
Colmatage microfuites clim (35%)

- Nom vendeur : position 9 (`textbox14`)

| Position | Colonne CSV   | Label PDF                  | KPI Template | Objectif | Statut      |
| :------- | :------------ | :------------------------- | :----------- | :------- | :---------- |
| 16       | `textbox200`  | TRAIT. DEPOLLUTION — qty   | —            | 35 %     | ✅ confirmé |
| **17**   | **`textbox201`** | **TRAIT. DEPOLLUTION — ratio** | **Dépoll.** | **35 %** | ✅ confirmé |

---

## Bloc 3 — PDF page 3 : Ratio sur Vidange (non utilisé pour Section 5 LS)

Header : `textbox620,...`
Colonnes PDF : REV. 2F (35%), REV. 3F (0,170), REV. 4F (18%), FILTRE HABITACLE (65%),
FILTRE AIR (50%), FILTRE CARBURANT (30%), F. VIDANGE (20%)

Ce bloc n'est pas utilisé pour remplir la Section 5 LS.

---

## Mapping des noms vendeurs CSV → Template

| Nom Template  | Nom CSV        |
| :------------ | :------------- |
| **Sandrine**  | `SANDRINE R.`  |
| **Paul**      | `PAUL P.`      |
| **Kamilia**   | `KAMILIA A.`   |
| **Chouaib**   | `CHOUAIB G.`   |
| **Pauline**   | `PAULINE R.`   |
| **Valentin**  | `VALENTIN C.`  |

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

> Vendeurs présents dans le CSV mais absents du template (ignorés) :
> Arnaud B., Elyne S., Isabelle P., Sofiane B.

---

## Format de remplissage — Section 5 LS

```markdown
### Staff Libre Service : Ratios de Vente

|Collaborateur LS|Garantie Pneu|Géométrie|VCR|VCF|Plaquette|Dépoll.|
|:--|:--|:--|:--|:--|:--|:--|
| **Sandrine** | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {plaq} | {depoll} |
| **Paul**     | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {plaq} | {depoll} |
| **Kamilia**  | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {plaq} | {depoll} |
| **Chouaib**  | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {plaq} | {depoll} |
| **Pauline**  | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {plaq} | {depoll} |
| **Valentin** | {gp_ratio} | {geom_ratio} | {vcr} | {vcf} | {plaq} | {depoll} |
```

---

## Règles de formatage

- Les ratios sont déjà formatés `"24,2 %"` dans le CSV — conserver tel quel
- Séparateur décimal : **virgule** (ex. `16,7 %`)
- Si la valeur est absente dans le CSV pour un vendeur donné, afficher `0 %`
- Ne jamais afficher les quantités brutes (numérateur) — uniquement le ratio %
- Dépoll. = TRAIT. DEPOLLUTION / Nb OR (bloc 4, `textbox201`), objectif 35 %
