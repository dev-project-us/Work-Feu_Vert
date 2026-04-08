---
description: chiffre mensuel
---

ALWAYS use this skill when the user types "/chiffre-mensuel". When triggered,
automatically create a new rapport mensuel file from the template, name it with
the correct month and year, and fill sections 2, 3 from the SUC CSV files in
resources/monthly_recap/SUC/.
Other triggers: "remplis le rapport mensuel", "mets à jour les chiffres du mois",
"fill the monthly report".

---

# Skill : Analyse des Chiffres — Rapport Mensuel Feu Vert Annecy

## Vue d'ensemble

Ce skill lit les fichiers CSV exportés depuis le système SUC stockés dans
`resources/monthly_recap/SUC/` et remplit les sections 2 et 3 du rapport mensuel.

**Différence clé vs le skill hebdomadaire** : deux fichiers MTD (période `Du 01/`) sont
présents — un pour l'année N, un pour l'année N-1. Ils sont distingués par l'année dans
la date de période. Le fichier objectifs reste nécessaire pour l'objectif CA global TTC.
Les valeurs N-1 sont lues **directement** depuis le fichier N-1, sans dérivation.

---

## Workflow — Commande `/chiffre-mensuel`

### Étape 1 — Identifier les fichiers CSV

```python
import os, glob, pathlib, re
from datetime import datetime

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("monthly_recap") / "SUC")
csv_files = glob.glob(os.path.join(folder, "SUC - *.csv"))

fichier_mtd      = None   # Année N (ex. 2026)
fichier_n1       = None   # Année N-1 (ex. 2025)
fichier_objectifs = None

annee_courante = datetime.today().year

for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'libelleJour' in content:
        fichier_objectifs = f
    elif 'Du 01/' in content:
        # Distinguer N vs N-1 par l'année dans la ligne de période
        m = re.search(r'Du 01/\d{2}/(\d{4})', content)
        if m:
            annee_fichier = int(m.group(1))
            if annee_fichier == annee_courante:
                fichier_mtd = f
            else:
                fichier_n1 = f
```

### Étape 2 — Déterminer le mois et l'année

Lire la date de fin depuis le fichier MTD (`textbox72`) :

```python
from datetime import datetime
import locale

# Ligne période : "Du 01/03/2026,31/03/2026"
# Extraire la date de fin
with open(fichier_mtd, 'r', encoding='utf-8-sig') as fh:
    mtd_content = fh.read()

lines = mtd_content.split('\r\n')
for line in lines:
    if line.startswith('Du 01/'):
        date_fin_str = line.split(',')[1].strip()
        break

date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
mois_num  = date_fin.month
annee     = date_fin.year

MOIS_FR = {
    1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
    5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
    9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
}
mois_str = MOIS_FR[mois_num]
# Ex : "mars 2026"
```

### Étape 3 — Créer le fichier rapport depuis le template

```python
import shutil

template_path = str(find_dir("templates") / "rapport_mensuel_template.md")
output_dir    = str(find_dir("Rapport mensuel"))
output_name   = f"rapport mensuel {mois_str} {annee}.md"
output_path   = os.path.join(output_dir, output_name)

# Créer le dossier si absent
os.makedirs(output_dir, exist_ok=True)
shutil.copy(template_path, output_path)
```

> Si le dossier `Rapport mensuel` n'existe pas, le créer avec `os.makedirs`.

### Étape 4 — Extraire les valeurs (colonnes TTC directes)

Lire `fichier_mtd` et `fichier_n1` en brut (`open(..., encoding='utf-8-sig')`).
Séparer les blocs sur les lignes vides (`\n\n` ou `\r\n\r\n`).

#### Bloc Global (Section 2)

Header : `caht_n, textbox4, textbox74, textbox84, cattc_n, textbox16, marge_n, textbox24, ...`

| Champ CSV       | Signification                          | Source       |
|:----------------|:---------------------------------------|:-------------|
| `cattc_n`       | CA TTC réalisé (N)                     | fichier_mtd  |
| `textbox4`      | Évolution CA vs N-1 (%)               | fichier_mtd  |
| `marge_n`       | Taux de marge global (%)              | fichier_mtd  |
| `textbox24`     | Évolution marge vs N-1 (pts)          | fichier_mtd  |
| `cattc_n_2`     | Panier moyen TTC                      | fichier_mtd  |
| `textbox17`     | Évolution panier vs N-1 (%)           | fichier_mtd  |
| `cattc_n`       | CA TTC N-1                            | fichier_n1   |
| `marge_n`       | Taux de marge N-1 (%)                 | fichier_n1   |
| `cattc_n_2`     | Panier moyen TTC N-1                  | fichier_n1   |

**Objectif CA TTC global** : `textbox8` depuis `fichier_objectifs` — valeur déjà TTC, **ne pas diviser par 1.2**.

#### Bloc LS (Section 3)

Header : `textbox22, textbox25, textbox27, textbox29, textbox31, textbox33, ..., textbox39, textbox41`

| Champ CSV   | Signification                  | Source      |
|:------------|:-------------------------------|:------------|
| `textbox27` | CA TTC LS réalisé (N)          | fichier_mtd |
| `textbox25` | Évolution CA LS vs N-1 (%)    | fichier_mtd |
| `textbox31` | Taux de marge LS (%)           | fichier_mtd |
| `textbox33` | Évolution marge LS (pts)       | fichier_mtd |
| `textbox39` | Panier moyen TTC LS            | fichier_mtd |
| `textbox41` | Évolution panier LS (%)        | fichier_mtd |
| `textbox27` | CA TTC LS N-1                  | fichier_n1  |
| `textbox31` | Taux de marge LS N-1 (%)      | fichier_n1  |
| `textbox39` | Panier moyen TTC LS N-1        | fichier_n1  |

> **Note** : `textbox22` = CA HT LS. `textbox27` = CA TTC LS réalisé. `textbox25` = progression CA TTC LS vs objectif (%).
> **Objectif CA TTC LS** : `objectif_ls_ttc = round(textbox27 × (1 - textbox25/100))`
> Ex : 76 100 × (1 - 0,11) = **67 729 €**
> **Écart / Obj** : utiliser `textbox25` directement (ex: `+11,0 %`)

#### Bloc Atelier (Section 3)

Header : `textbox43, textbox45, textbox47, textbox49, textbox51, textbox53, ..., textbox62, textbox64`

| Champ CSV   | Signification                    | Source      |
|:------------|:---------------------------------|:------------|
| `textbox47` | CA TTC Atelier réalisé (N)       | fichier_mtd |
| `textbox45` | Évolution CA Atelier vs N-1 (%) | fichier_mtd |
| `textbox51` | Taux de marge Atelier (%)        | fichier_mtd |
| `textbox53` | Évolution marge Atelier (pts)    | fichier_mtd |
| `textbox55` | Nombre d'OR                      | fichier_mtd |
| `textbox57` | Évolution Nb OR (%)              | fichier_mtd |
| `textbox62` | Panier moyen TTC Atelier         | fichier_mtd |
| `textbox64` | Évolution panier Atelier (%)     | fichier_mtd |
| `textbox47` | CA TTC Atelier N-1               | fichier_n1  |
| `textbox51` | Taux de marge Atelier N-1 (%)   | fichier_n1  |
| `textbox55` | Nb OR N-1                        | fichier_n1  |
| `textbox62` | Panier moyen TTC Atelier N-1     | fichier_n1  |

> **Note** : `textbox43` = CA HT Atelier. `textbox47` = CA TTC Atelier réalisé. `textbox45` = progression CA TTC Atelier vs objectif (%).
> **Objectif CA TTC Atelier** : `objectif_at_ttc = round(textbox47 × (1 - textbox45/100))`
> Ex : 147 592 × (1 - 0,102) = **132 538 €**
> **Écart / Obj** : utiliser `textbox45` directement (ex: `+10,2 %`)

### Étape 5 — Mettre à jour l'en-tête et remplir les sections

```python
with open(output_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

# En-tête : remplacer [Mois AAAA]
rapport = rapport.replace('[Mois AAAA]', f'{mois_str.capitalize()} {annee}')

# Section 2 : CA, Marge %, Marge €, Panier
# Section 3 LS : CA, Marge, Panier
# Section 3 Atelier : CA, Marge, Nb OR, Panier
# → Même logique de remplacement de placeholders que chiffre.md
# → Section 4 du template mensuel inclut colonnes N-1 — renseigner ratioN_1 et écart

with open(output_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

**Marge Brute (€) — Section 2 :**

La marge en euros est dans le bloc `libelle,marge_n_2,marge_n_1_1,textbox92`
de chaque fichier MTD (dernière section avant la fin du fichier).

```python
import csv, io

def extraire_marge_eur(content):
    """Extrait marge_n_2 (Marge Produit) depuis le fichier MTD."""
    # Chercher le bloc libelle/marge_n_2
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if line.startswith('libelle,marge_n_2'):
            # Ligne suivante : "Marge Produit,46 985,39 275,20 %"
            data_line = lines[i + 1]
            parts = data_line.split(',')
            valeur_raw = parts[1].replace('\xa0', '').replace(' ', '').strip()
            return int(valeur_raw)
    return None

# Réalisé N et N-1 : lire directement depuis fichier_mtd et fichier_n1
marge_eur_n   = extraire_marge_eur(mtd_content)    # ex. 46 985
marge_eur_n1  = extraire_marge_eur(n1_content)     # ex. 40 181

# Objectif € → textbox42 (dernière colonne du fichier_objectifs)
# Attention : la valeur peut être répartie sur deux colonnes CSV à cause de la virgule
# dans "49,0 %" — lire la ligne brute et reconstruire
marge_obj_eur = int(textbox42_eur.replace('\xa0', '').replace(' ', ''))

# Écart vs objectif (%)
marge_eur_ecart = round((marge_eur_n / marge_obj_eur - 1) * 100, 1)

# Évolution N-1 (%)
marge_eur_evo = round((marge_eur_n / marge_eur_n1 - 1) * 100, 1)
```

> **Extraction de textbox42** (objectif Marge €) : c'est la **dernière colonne numérique** du
> fichier objectifs. La ligne type ressemble à `...,textbox50,textbox42` avec valeur
> `...,\"49,0 %\",107 850`. Lire la dernière valeur non-vide de chaque ligne de données.

Format attendu dans le rapport :
```markdown
| **Marge Brute (€)** | {marge_eur_n} € | {marge_obj_eur} € | {marge_eur_ecart:+} % | {marge_eur_n1} € | {marge_eur_evo:+} % |
```

**Colonne Statut — Section 3 :**

Appliquer une icône sur **toutes les lignes** de Section 3, basée sur le signe de l'Évolution / N-1 :

```python
def statut_n1(evo_str):
    """evo_str ex: '+7,8 %' ou '-1,2 pts'"""
    val = float(evo_str.replace(' %', '').replace(' pts', '').replace(',', '.').replace('+', ''))
    if val > 0:    return '🟢'
    elif val == 0: return '🟡'
    else:          return '🔴'

# Appliquer sur chaque ligne de S3 LS et Atelier :
# statut_n1(evo_ca_ls), statut_n1(evo_marge_ls), statut_n1(evo_panier_ls)
# statut_n1(evo_ca_at), statut_n1(evo_marge_at), statut_n1(evo_nb_or), statut_n1(evo_panier_at)
```

**N-1 — Section 3 :**

Les valeurs N-1 sont lues directement depuis `fichier_n1` (mêmes colonnes que `fichier_mtd`) :

| Ligne Section 3       | N-1 depuis fichier_n1     |
|:----------------------|:--------------------------|
| CA TTC LS N-1         | `textbox27`               |
| Marge LS N-1 (%)      | `textbox31`               |
| Panier LS N-1         | `textbox39`               |
| CA TTC Atelier N-1    | `textbox47`               |
| Marge Atelier N-1 (%) | `textbox51`               |
| Nb OR N-1             | `textbox55`               |
| Panier Atelier N-1    | `textbox62`               |

Évolution (%) = `round((val_n / val_n1 - 1) * 100, 1)` sauf marge (en pts).

### Étape 6 — Chaîner `/ratios-mensuel`

À la fin de l'exécution, invoquer automatiquement le skill `/ratios-mensuel`
pour remplir la Section 4.

### Étape 7 — Confirmer à l'utilisateur

Indiquer le nom du fichier créé, le mois/année détectés, et un résumé des
valeurs clés (CA mensuel, marge %, marge €, panier moyen).

---

## Règles spécifiques au mensuel

- **Pas de RAF** : la Section 7 RAF de l'hebdo n'existe pas dans le rapport mensuel.
- **Fichier semaine ignoré** : même s'il est présent dans le dossier, ne pas l'utiliser.
- **Toutes les valeurs sont cumulées sur le mois entier** — ne pas confondre avec
  des valeurs hebdomadaires résiduelles.
- **Dossier de sortie** : `Rapport mensuel/` (distinct de `Rapport hebdomadaire/`).

---

## Identification des fichiers CSV

| Fichier | Identification | Utilisé pour |
|:--|:--|:--|
| `SUC - Situation de chiffre*.csv` | `Du 01/` + **année courante** (ex. 2026) | `fichier_mtd` — Réalisé N (S2, S3) |
| `SUC - Situation de chiffre*.csv` | `Du 01/` + **année N-1** (ex. 2025) | `fichier_n1` — Valeurs N-1 (S2, S3) |
| `SUC - Objectifs Journaliers*.csv` | Contient `libelleJour` | `fichier_objectifs` — Objectif CA global, Marge € obj (S2) |

---

## Règles de formatage

- CA en **€ TTC** — utiliser les colonnes TTC directement, **ne pas diviser par 1.2**
- Panier moyen en **€ TTC** — utiliser `cattc_n_2`, `textbox39`, `textbox62` directement
- Séparateur décimal : **virgule**
- Espacement milliers : **espace** (ex. `125 430 €`)
- Évolutions : toujours afficher le signe (`+3,2 %`, `-1,5 pts`)
- Valeur absente ou non disponible : `N/A`
- Objectif CA LS / Atelier : calculé via `textbox27/47 × (1 - textbox25/45 / 100)` — voir formules Section 3
