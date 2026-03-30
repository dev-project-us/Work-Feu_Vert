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

**Différence clé vs le skill hebdomadaire** : seul le fichier MTD (période `Du 01/`)
est utilisé pour les chiffres réalisés. Le fichier semaine n'existe pas ou est ignoré.
Le fichier objectifs reste nécessaire pour les objectifs mensuels.

---

## Workflow — Commande `/chiffre-mensuel`

### Étape 1 — Identifier les fichiers CSV

```python
import os, glob, pathlib

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("monthly_recap") / "SUC")
csv_files = glob.glob(os.path.join(folder, "SUC - *.csv"))

fichier_mtd = None
fichier_objectifs = None

for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'libelleJour' in content:
        fichier_objectifs = f
    elif 'Du 01/' in content:
        fichier_mtd = f
    # Fichier semaine ignoré volontairement pour le rapport mensuel
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

### Étape 4 — Extraire les valeurs

Appliquer les mêmes mappings que le skill hebdomadaire (`chiffre.md`) :

- **Bloc Global** → Section 2 (CA, Marge, Fréquentation, Panier) depuis `fichier_mtd`
- **Bloc LS** → Section 3 LS depuis `fichier_mtd`
- **Bloc Atelier** → Section 3 Atelier depuis `fichier_mtd`
- **Objectifs** (`textbox8`, `textbox50`, `textbox42`) → depuis `fichier_objectifs`

Les colonnes CSV, les calculs HT (÷ 1.2), et les formules N-1 sont **identiques**
au skill hebdomadaire. Se référer à `chiffre.md` pour le détail complet des mappings.

### Étape 5 — Mettre à jour l'en-tête et remplir les sections

```python
with open(output_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

# En-tête : remplacer [Mois AAAA]
rapport = rapport.replace('[Mois AAAA]', f'{mois_str.capitalize()} {annee}')

# Section 2 : CA, Marge, Fréquentation, Panier
# Section 3 LS : CA, Marge, Panier
# Section 3 Atelier : CA, Marge, Nb OR, Panier
# → Même logique de remplacement de placeholders que chiffre.md
# → Section 4 du template mensuel inclut colonnes N-1 — renseigner ratioN_1 et écart

with open(output_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)
```

**Note sur le template mensuel** : les tableaux des Sections 3 et 4 ont une colonne
N-1 et Évolution/N-1 supplémentaires vs le template hebdo. Les renseigner depuis
les champs d'évolution du CSV (`textbox4`, `textbox25`, `textbox45`, etc.).

### Étape 6 — Chaîner `/ratios-mensuel`

À la fin de l'exécution, invoquer automatiquement le skill `/ratios-mensuel`
pour remplir la Section 4.

### Étape 7 — Confirmer à l'utilisateur

Indiquer le nom du fichier créé, le mois/année détectés, et un résumé des
valeurs clés (CA mensuel, marge, nb clients).

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
| `SUC - Situation de chiffre*.csv` | Contient `Du 01/` | Réalisé mensuel (S2, S3) |
| `SUC - Objectifs Journaliers*.csv` | Contient `libelleJour` | Objectifs mensuels (S2) |

---

## Règles de formatage

- CA en € HT (diviser TTC par 1.2)
- Séparateur décimal : **virgule**
- Espacement milliers : **espace** (ex. `125 430 €`)
- Évolutions : toujours afficher le signe (`+3,2 %`, `-1,5 pts`)
- Valeur absente : `N/A`
