---
name: familles-trimestriel
description: >
  Fill the "Analyse spécifique / Familles" section of the Feu Vert Annecy quarterly report
  from the comparatifCAv2_Famille CSV export. ALWAYS use when the user types /familles-trimestriel,
  or says "remplis les familles trimestrielles", "analyse les familles du trimestre",
  or wants to populate the product-family breakdown table (CA n, CA n-1, Evol. CA,
  Marge n, Marge +/-, Qté n, Statut) in the rapport trimestriel.
---

# Skill : Analyse par Familles — Rapport Trimestriel Feu Vert Annecy

## Vue d'ensemble

Ce skill lit le fichier CSV `comparatifCAv2_Famille*.csv` (export SUC comparatif CA par
famille) et remplit la section **"Analyse spécifique / Familles"** du rapport trimestriel,
incluant le tableau de données et les points clés automatiques.

---

## Workflow — Commande `/familles-trimestriel`

### Étape 1 — Localiser les fichiers

```python
import os, glob, pathlib, csv, re
from datetime import datetime

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

# Fichier CSV familles trimestriel
familles_folder = str(find_dir("Resources trimestrielles") / "Familles")
csv_pattern = os.path.join(familles_folder, "comparatifCAv2_Famille*.csv")
csv_files = glob.glob(csv_pattern)
if not csv_files:
    raise FileNotFoundError("Aucun fichier comparatifCAv2_Famille*.csv trouvé dans Resources trimestrielles/Familles/")
fichier_familles = csv_files[0]

# Rapport trimestriel existant
rapport_dir = str(find_dir("Rapport trimestriel"))
rapports = glob.glob(os.path.join(rapport_dir, "rapport trimestriel *.md"))
if not rapports:
    raise FileNotFoundError("Aucun rapport trimestriel trouvé dans Rapport trimestriel/.")
rapport_path = sorted(rapports)[-1]   # prendre le plus récent
```

> **Note** : Si plusieurs rapports existent, le plus récent (ordre alphabétique) est utilisé.
> Les noms suivent le format `rapport trimestriel T1 2026.md`.

---

### Étape 2 — Parser le CSV et extraire les données par famille

#### Structure du fichier CSV

| Ligne | Contenu |
|:------|:--------|
| 1 | En-tête magasin (`LIBELLEMAGASIN,...`) |
| 2 | Valeurs magasin (`ANNECY SEYNOD, dates...`) |
| 3 | Vide |
| 4 | **Noms de colonnes** (la ligne longue avec `textbox48,...`) |
| 5+ | Données produits (1 ligne par article, données famille répétées) |

#### Mapping des colonnes (0-indexé depuis la ligne 4)

| Index | Nom colonne   | Signification                  |
|:------|:--------------|:-------------------------------|
| 14    | `codeFamille` | Code famille (ex: `A-ENTRETIEN`) |
| 15    | `CAHT_n_4`    | CA HT famille N (ex: `17 301`) |
| 16    | `CAHT_n_1_1`  | CA HT famille N-1 (ex: `14 560`) |
| 18    | `textbox57`   | Évolution CA % (ex: `18,8 %`) |
| 21    | `MARGE_n`     | Taux de marge famille N % (ex: `44,7 %`) |
| 22    | `MARGE_n_1`   | Taux de marge famille N-1 % (ex: `46,5 %`) |
| 26    | `textbox63`   | Quantité vendue famille N (ex: `1 265`) |

> **Principe clé** : le CSV contient une ligne par article (produit). Les données famille
> sont identiques sur toutes les lignes appartenant à la même famille. Il suffit donc de
> prendre la **première occurrence** de chaque `codeFamille`.

```python
seen_families = {}

with open(fichier_familles, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

# Sauter les 4 premières lignes, partir des données
data_lines = lines[4:]
reader = csv.reader(data_lines)

for row in reader:
    if len(row) < 30:
        continue
    fam = row[14].strip()
    if not fam or fam in seen_families:
        continue
    seen_families[fam] = {
        'ca_n':     row[15].strip(),
        'ca_n1':    row[16].strip(),
        'evo_ca':   row[18].strip(),
        'marge_n':  row[21].strip(),
        'marge_n1': row[22].strip(),
        'qty_n':    row[26].strip(),
    }
```

---

### Étape 3 — Calculer `Marge +/- (pts)` et `Statut`

```python
def parse_pct(s):
    """Convertit '44,7 %' ou '-1,8 pts' ou '-' en float, ou None si impossible."""
    try:
        clean = s.replace(' %','').replace(' pts','').replace(',','.').replace('+','').strip()
        return float(clean)
    except:
        return None

def statut(evo_str):
    """Retourne emoji selon signe de l'évolution CA."""
    val = parse_pct(evo_str)
    if val is None:   return '⚪'
    if val > 0:       return '🟢'
    if val == 0:      return '🟡'
    return '🔴'

def marge_delta(marge_n_str, marge_n1_str):
    """Calcule écart en points entre marge N et marge N-1."""
    mn  = parse_pct(marge_n_str)
    mn1 = parse_pct(marge_n1_str)
    if mn is None or mn1 is None:
        return 'N/A'
    delta = mn - mn1
    sign = '+' if delta >= 0 else ''
    return f'{sign}{delta:.1f} pts'.replace('.', ',')
```

---

### Étape 4 — Familles attendues dans le template

Remplir **uniquement** les familles présentes dans le template. Ignorer les familles CSV
absentes du template (ex: `T-FIDELITE`).

| Code famille dans CSV       | Ligne template correspondante     |
|:----------------------------|:----------------------------------|
| `A-ENTRETIEN`               | **A-ENTRETIEN**                   |
| `B-ELECTRICITE`             | **B-ELECTRICITE**                 |
| `C-PIECES TECHNIQUES`       | **C-PIECES TECHNIQUES**           |
| `D-OUTILLAGE`               | **D-OUTILLAGE**                   |
| `E-EQUIPEMENT EXTERIEUR`    | **E-EQUIPEMENT EXTERIEUR**        |
| `F-EQUIPEMENT INTERIEUR`    | **F-EQUIPEMENT INTERIEUR**        |
| `G-AUTO SON`                | **G-AUTO SON**                    |
| `H-LUBRIFIANTS`             | **H-LUBRIFIANTS**                 |
| `I-PNEUMATIQUES`            | **I-PNEUMATIQUES**                |
| `J-2 ROUES`                 | **J-2 ROUES**                     |
| `U-SERVICES`                | **U-SERVICES**                    |
| `W-DIVERS`                  | **W-DIVERS**                      |
| `X-TARIF MAIN D'OEUVRE`     | **X-TARIF MAIN D'OEUVRE**         |

---

### Étape 5 — Générer le tableau Markdown et remplacer dans le rapport

```python
TEMPLATE_FAMILIES = [
    'A-ENTRETIEN', 'B-ELECTRICITE', 'C-PIECES TECHNIQUES', 'D-OUTILLAGE',
    'E-EQUIPEMENT EXTERIEUR', 'F-EQUIPEMENT INTERIEUR', 'G-AUTO SON',
    'H-LUBRIFIANTS', 'I-PNEUMATIQUES', 'J-2 ROUES', 'U-SERVICES',
    'W-DIVERS', "X-TARIF MAIN D'OEUVRE"
]

rows = []
for fam in TEMPLATE_FAMILIES:
    d = seen_families.get(fam)
    if d:
        ca_n   = f"{d['ca_n']} €"     if d['ca_n']  else 'N/A'
        ca_n1  = f"{d['ca_n1']} €"    if d['ca_n1'] else 'N/A'
        evo    = d['evo_ca']           or 'N/A'
        mg_n   = d['marge_n']          or 'N/A'
        mg_d   = marge_delta(d['marge_n'], d['marge_n1'])
        qty    = d['qty_n']            or 'N/A'
        st     = statut(d['evo_ca'])
    else:
        ca_n = ca_n1 = evo = mg_n = mg_d = qty = st = 'N/A'
    rows.append(f'| **{fam}** | {ca_n} | {ca_n1} | {evo} | {mg_n} | {mg_d} | {qty} | {st} |')

new_table = (
    '| Famille | CA n (€) | CA n-1 (€) | Evol. CA (%) | Marge n (%) | Marge +/- (pts) | Qté n | Statut |\n'
    '| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n'
    + '\n'.join(rows)
)
```

#### Remplacer le tableau dans le rapport

Utiliser une regex pour cibler la section familles entre l'en-tête `## Analyse spécifique / Familles`
et la ligne `### Points clés de l'analyse par famille`.

```python
import re

with open(rapport_path, 'r', encoding='utf-8') as f:
    rapport = f.read()

# Remplacer le tableau existant (du header jusqu'avant les Points clés)
pattern = r'(\| Famille \| CA n.*?\n)(\| :---.*?\n)((\|.*?\n)+)'
replacement = new_table + '\n'
rapport = re.sub(pattern, replacement, rapport, flags=re.DOTALL)

with open(rapport_path, 'w', encoding='utf-8') as f:
    f.write(rapport)
```

---

### Étape 6 — Générer les points clés automatiques

Après avoir rempli le tableau, générer 3 à 5 points d'analyse pertinents dans la section
`### Points clés de l'analyse par famille`. Chercher les éléments suivants :

1. **Famille moteur** : la famille avec la plus forte croissance CA en valeur absolue (€) sur le trimestre
2. **Famille en déclin** : la famille avec la plus forte baisse CA en %
3. **Alerte marge** : famille avec la pire dégradation de marge (pts négatifs)
4. **Anomalie notable** : CA négatif, quantité très faible (<20), ou écart marge > ±10 pts
5. **Synthèse trimestrielle** : tendance globale du trimestre (est-ce que la majorité des familles progressent ?)

```python
# Exemple de logique de classement
families_data = []
for fam in TEMPLATE_FAMILIES:
    d = seen_families.get(fam)
    if not d:
        continue
    ca_n_val  = parse_int(d['ca_n'])      # voir helper ci-dessous
    ca_n1_val = parse_int(d['ca_n1'])
    evo_val   = parse_pct(d['evo_ca'])
    mg_delta  = parse_pct(d['marge_n']) - parse_pct(d['marge_n1']) \
                if parse_pct(d['marge_n']) and parse_pct(d['marge_n1']) else None
    families_data.append({
        'fam': fam, 'ca_n': ca_n_val, 'ca_n1': ca_n1_val,
        'evo': evo_val, 'mg_delta': mg_delta
    })

def parse_int(s):
    """Convertit '17 301' → 17301, gère None et vides."""
    try:
        return int(s.replace('\xa0','').replace(' ','').replace('€','').strip())
    except:
        return None
```

Rédiger les points clés en **français**, de manière factuelle et orientée management, avec une
perspective trimestrielle (tendances sur 3 mois, non hebdomadaires).

---

### Étape 7 — Confirmer à l'utilisateur

Afficher un résumé :
- Nom du rapport modifié
- Nombre de familles remplies
- Top 3 familles en croissance CA
- Top 3 familles en déclin CA
- Familles avec alerte marge (dégradation > 5 pts)

---

## Règles de formatage

- CA en **€ HT** (les colonnes CAHT_ sont hors taxes) — noter HT dans la colonne si besoin
- Séparateur milliers : **espace** (ex: `17 301 €`) — conserver tel quel depuis le CSV
- Séparateur décimal : **virgule** (ex: `18,8 %`)
- Évolutions : toujours afficher le signe (`+18,8 %`, `-11,6 %`, `+4,3 pts`)
- Valeur absente ou `-` dans le CSV : afficher `N/A`
- Ne pas recalculer l'évolution CA — utiliser `textbox57` directement depuis le CSV
- La colonne `Marge +/- (pts)` est **calculée** : `round(MARGE_n - MARGE_n_1, 1)` en pts

---

## Identification du fichier CSV

| Fichier | Pattern | Contenu |
|:--------|:--------|:--------|
| `comparatifCAv2_Famille*.csv` | Ligne 2 : `ANNECY SEYNOD, date_début, date_fin` | CA et marge par famille, sous-famille, gamme, article |

Le fichier est placé dans `resources/Resources trimestrielles/Familles/`.
