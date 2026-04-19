---
description: chiffre
---

  ALWAYS use this skill when the user types "/chiffre". When triggered, automatically
  create a new rapport hebdomadaire file from the template, name it with the correct
  week number, and fill sections 2, 3 and 7 from the 3 SUC CSV files.
  Also triggers when the user wants to fill, update, or analyse sections 2, 3, or 7
  of the rapport hebdomadaire for Feu Vert Annecy Seynod using the SUC CSV exports.
  Other triggers: "remplis le rapport", "mets à jour les chiffres", "analyse les CSV",
  "fill the weekly report".
---

# Skill : Analyse des Chiffres — Rapport Hebdomadaire Feu Vert Annecy

## Vue d'ensemble

Ce skill décrit comment lire les 3 fichiers CSV exportés depuis le système SUC
et en extraire les valeurs nécessaires pour remplir les sections 2, 3 et 7 du
rapport hebdomadaire.

Les 3 fichiers source sont stockés dans un dossier dédié :
a folder named `resources/SUC/`

> Ce dossier contient désormais **4 fichiers** — un par type de rapport.
> À chaque nouvelle semaine, remplacer les anciens fichiers par les nouveaux exports.

---

## Workflow — Commande `/chiffre`

Quand l'utilisateur tape `/chiffre`, exécuter **dans cet ordre** :

### Étape 1 — Déterminer le numéro de semaine

Lire la date de fin de période dans le fichier semaine (`textbox72`) et en
déduire le numéro de semaine ISO :

```python
from datetime import datetime

# Extraire la date de fin depuis le fichier semaine
# Ex : "22/03/2026" → semaine 12
date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
semaine = date_fin.isocalendar()[1]
annee = date_fin.year
```

### Étape 2 — Créer le fichier rapport depuis le template

```python
import shutil, os

template_path = str(find_dir("templates") / "rapport_hebdomadaire_template.md")
output_dir    = str(find_dir("Rapport hebdomadaire"))
output_name   = f"rapport hebdomadaire semaine {semaine}.md"
output_path   = os.path.join(output_dir, output_name)

shutil.copy(template_path, output_path)
```

> Si le dossier `Rapport hebdomadaire` n'existe pas, le créer avec `os.makedirs`.

### Étape 3 — Lire les 3 fichiers CSV

Appliquer le protocole de scan du dossier `Resources\SUC\` décrit plus bas
pour identifier `fichier_semaine`, `fichier_mtd` et `fichier_objectifs`.

### Étape 4 — Extraire et calculer les valeurs

Appliquer les mappings et calculs décrits dans les sections
**Extraction des données** et **Calculs à effectuer** plus bas.

### Étape 5 — Remplir les sections

Ouvrir le fichier créé à l'étape 2 et remplacer les placeholders :

- **Section 2** : remplacer les cellules `€`, `%`, `clts` avec les vraies valeurs
- **Section 3** : même principe pour LS et Atelier
- **En-tête du rapport** : mettre à jour la période `[JJ/MM/AAAA] au [JJ/MM/AAAA]`
  avec les dates de début et fin de la semaine
- **Section 7** : remplir le tableau RAF avec les valeurs mensuelles

### Étape 6 — Confirmer à l'utilisateur

Indiquer le nom du fichier créé et un résumé des valeurs clés remplies
(CA semaine, marge, nb clients). Signaler les champs laissés vides car
non disponibles dans les CSV (voir section **Valeurs non disponibles**).

---



Tous les fichiers commencent par `SUC - ` (avec espaces autour du tiret).
**Ne pas identifier les fichiers par leur nom complet** — les identifier par leur **contenu**.

### Comment identifier chaque fichier

Lire la ligne de période dans chaque fichier `SUC - Situation de chiffre*.csv` :

```
textbox1,textbox72
Du 16/03/2026,22/03/2026   ← semaine N (année courante)
Du 16/03/2025,22/03/2025   ← semaine N-1 (année précédente)
Du 01/03/2026,22/03/2026   ← période depuis le 1er = fichier MOIS (MTD)
```

Le fichier objectifs se reconnaît à la présence de la colonne `libelleJour`.
Les fichiers semaine N et N-1 se distinguent par **l'année dans la date de période**.

### Résumé des 4 fichiers

| Fichier                              | Identification                                      | Utilisé pour            |
| :----------------------------------- | :-------------------------------------------------- | :---------------------- |
| `SUC - Situation de chiffre*.csv`    | Période commence le **1er du mois**, année N        | S7 (réalisé MTD)        |
| `SUC - Situation de chiffre*.csv`    | Période en milieu de mois, **année courante**       | S2 et S3 (semaine N)    |
| `SUC - Situation de chiffre*.csv`    | Période en milieu de mois, **année N-1**            | S3 (valeurs N-1 LS/At.) |
| `SUC - Objectifs Journaliers*.csv`   | Contient la colonne `libelleJour`                   | S7 (objectifs)          |

### Protocole de scan du dossier

```python
import os, glob, re
from datetime import datetime

folder = str(find_dir("resources") / "SUC")
csv_files = glob.glob(os.path.join(folder, "SUC - *.csv"))

annee_courante    = datetime.today().year
fichier_semaine   = None
fichier_mtd       = None
fichier_objectifs = None
fichier_n1        = None   # même semaine, année N-1 (optionnel)

for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'libelleJour' in content:
        fichier_objectifs = f
    elif 'Du 01/' in content:
        fichier_mtd = f
    else:
        m = re.search(r'Du \d{2}/\d{2}/(\d{4})', content)
        if m and int(m.group(1)) == annee_courante:
            fichier_semaine = f
        else:
            fichier_n1 = f  # semaine N-1 (année précédente)
```

---

## Les 3 fichiers source

Les fichiers ne sont pas des tableaux propres — ils contiennent des blocs
de données séparés par des lignes vides. Utiliser `cat` ou lecture brute ligne
par ligne, **ne pas utiliser pandas avec header auto-détecté**.

```python
# Méthode recommandée : lecture brute
with open('fichier.csv', 'r', encoding='utf-8-sig') as f:
    content = f.read()
```

---

## Extraction des données — Fichiers 2 & 3 (Situation de chiffre)

Les deux fichiers ont la **même structure**. Voici le mapping des blocs :

### Bloc Global (Section 2 & intro Section 3)
```
Ligne header : caht_n, textbox4, textbox74, textbox84, cattc_n, textbox16,
               marge_n, textbox24, textbox78, textbox86, textbox11,
               nbPassage_n, textbox14, cattc_n_2, textbox17
Ligne valeur  : [valeurs correspondantes]
```

| Champ CSV        | Signification              | Section utilisée |
| :--------------- | :------------------------- | :--------------- |
| `cattc_n`        | CA TTC réalisé (N)         | S2, S7 MTD       |
| `textbox4`       | Évolution CA vs N-1 (%)    | S2               |
| `textbox74`      | CA TTC N-1                 | S2               |
| `textbox84`      | % réalisation vs objectif  | S2               |
| `marge_n`        | Taux de marge (%)          | S2               |
| `textbox24`      | Évolution marge vs N-1 (pts)| S2              |
| `nbPassage_n`    | Label "Nb. client"         | S2 (ignorer)     |
| `textbox14`      | Nb clients (fréquentation) | S2               |
| `textbox17`      | Évolution fréquentation    | S2               |
| `cattc_n_2`      | Panier moyen TTC (€)       | S2               |

> **Note** : Le panier moyen dans le CSV est TTC — utiliser directement, ne pas diviser par 1.2.
> **Section 2** : les valeurs N-1 sont dérivées depuis le réalisé et l'évolution : `N-1 = réalisé_N / (1 + evo/100)`.
> **Section 3 LS et Atelier** : si `fichier_n1` est présent, lire les valeurs N-1 directement (mêmes colonnes que `fichier_semaine`). Si absent, dériver depuis l'évolution.

### Bloc LS N-1 (fichier_n1 — Section 3 LS)

Mêmes colonnes que dans `fichier_semaine` :

| Champ CSV     | Valeur N-1 extraite         |
| :------------ | :--------------------------- |
| `textbox27`   | CA TTC LS N-1               |
| `textbox31`   | Taux de marge LS N-1 (%)    |
| `textbox39`   | Panier moyen LS N-1 (€ TTC) |

### Bloc Atelier N-1 (fichier_n1 — Section 3 Atelier)

| Champ CSV     | Valeur N-1 extraite              |
| :------------ | :-------------------------------- |
| `textbox47`   | CA TTC Atelier N-1               |
| `textbox51`   | Taux de marge Atelier N-1 (%)    |
| `textbox55`   | Nombre d'OR N-1                  |
| `textbox62`   | Panier moyen Atelier N-1 (€ TTC) |

### Bloc Libre Service (Section 3 LS)
```
Ligne header : textbox22, textbox25, textbox27, textbox29, textbox31,
               textbox33, textbox34, textbox35, textbox37, textbox39, textbox41
```

| Champ CSV     | Signification              |
| :------------ | :------------------------- |
| `textbox27`   | CA TTC LS réalisé (N)      |
| `textbox25`   | Évolution CA LS vs N-1 (%) |
| `textbox31`   | Taux de marge LS (%)       |
| `textbox33`   | Évolution marge LS (pts)   |
| `textbox35`   | Nb clients LS              |
| `textbox37`   | Évolution fréq LS (%)      |
| `textbox39`   | Panier moyen LS (€ TTC)    |
| `textbox41`   | Évolution panier LS (%)    |

> **Note** : `textbox22` = CA HT LS (ignoré). `textbox27` = CA TTC LS réalisé. Objectif CA TTC LS : `round(textbox27 × (1 - textbox25/100))`.

### Bloc Atelier (Section 3 Atelier)
```
Ligne header : textbox43, textbox45, textbox47, textbox49, textbox51,
               textbox53, textbox54, textbox55, textbox57, textbox62, textbox64
```

| Champ CSV     | Signification                |
| :------------ | :--------------------------- |
| `textbox47`   | CA TTC Atelier réalisé (N)   |
| `textbox45`   | Évolution CA Atelier vs N-1  |
| `textbox51`   | Taux de marge Atelier (%)    |
| `textbox53`   | Évolution marge Atelier (pts)|
| `textbox55`   | Nb OR (nombre d'ordres)      |
| `textbox57`   | Évolution Nb OR (%)          |
| `textbox62`   | Panier moyen Atelier (€ TTC) |
| `textbox64`   | Évolution panier Atelier (%) |

> **Note** : `textbox43` = CA HT Atelier (ignoré). `textbox47` = CA TTC Atelier réalisé. Objectif CA TTC Atelier : `round(textbox47 × (1 - textbox45/100))`.

### Contrats entretien (Section 7)
```
Ligne header (tout en haut du fichier) : nbContratEntretien_DECI, nbCE_G6K
Ligne valeur : [nb contrats DECI], [nb contrats G6K]
```
Le nombre total de contrats MTD = somme des deux valeurs.

---

## Extraction des données — Fichier 3 (Objectifs Journaliers)

Ce fichier contient les **objectifs mensuels** et les réalisations **jour par jour**.

### Ligne d'en-tête des colonnes (2ème bloc après la ligne vide)
```
dateDatetime, libelleJour, CATTC, ..., marge, marge_1, textbox8, textbox22,
..., textbox49, textbox57, textbox50, textbox42
```

### Objectifs mensuels (colonnes fixes, répétées sur chaque ligne)

| Champ CSV     | Signification                          |
| :------------ | :------------------------------------- |
| `textbox8`    | Objectif CA TTC mensuel                |
| `textbox50`   | Objectif Taux de Marge % mensuel       |
| `textbox42`   | **Objectif Marge € mensuel** — **dernière colonne** du fichier |

Ces valeurs sont **identiques sur toutes les lignes** — lire depuis n'importe quelle ligne non-dimanche (CATTC ≠ 0).

> **Note** : L'objectif de marge pour la Section 2 est `textbox42` (dernière colonne).
> Pour obtenir le taux % : `round(textbox42 / (textbox8 / 1.2) * 100, 1)`

---

## Calculs à effectuer

### Section 2

```python
# CA
cattc_n       = int(cattc_n_raw.replace(' ', ''))
ca_obj_ttc    = int(textbox8.replace(' ', ''))
caht_evo      = float(textbox4.replace(' %', '').replace(',', '.'))
ca_n1         = round(cattc_n / (1 + caht_evo / 100))
ca_ecart      = round((cattc_n / ca_obj_ttc - 1) * 100, 1)

# Marge
marge_n       = float(marge_n_raw.replace(' %', '').replace(',', '.'))
marge_obj     = float(textbox50.replace(' %', '').replace(',', '.'))
marge_evo     = float(textbox24.replace(' %', '').replace(',', '.'))
marge_n1      = round(marge_n - marge_evo, 1)
marge_ecart   = round(marge_n - marge_obj, 1)

# Fréquentation
freq_n        = int(textbox14_value)
freq_evo      = float(textbox17.replace(' %', '').replace(',', '.'))
freq_n1       = round(freq_n / (1 + freq_evo / 100))

# Panier moyen TTC — utiliser cattc_n_2 directement, ne pas diviser par 1.2
panier_n      = float(cattc_n_2.replace(' €', '').replace(',', '.'))
panier_evo    = float(textbox17_panier.replace(' %', '').replace(',', '.'))
panier_n1     = round(panier_n / (1 + panier_evo / 100), 1)
```

### Section 7 (RAF)

```python
ca_obj_ttc    = int(textbox8.replace(' ', ''))
ca_mtd        = int(cattc_n_from_mtd.replace(' ', ''))
ca_pct        = round(ca_mtd / ca_obj_ttc * 100, 1)
ca_raf        = ca_obj_ttc - ca_mtd

marge_obj_eur = int(textbox42.replace(' ', ''))
marge_mtd_eur_raw = # ligne "Marge Produit" dans le bloc libelle/marge_n_2 du fichier 3
marge_mtd_eur = int(marge_mtd_eur_raw.replace(' ', ''))
marge_pct     = round(marge_mtd_eur / marge_obj_eur * 100, 1)
marge_raf     = marge_obj_eur - marge_mtd_eur

contrat_mtd   = int(nbContratEntretien_DECI) + int(nbCE_G6K)
```

---

## Remplissage du rapport

### Section 2 — Format attendu

```markdown
| **CA TTC Total**  | {cattc_n} €  | {ca_obj_ttc} €  | {ca_ecart} %   | {ca_n1} €   | {caht_evo:+} % |
| **Marge Brute**   | {marge_n} %  | {marge_obj} %   | {marge_ecart:+} pts | {marge_n1} % | {marge_evo:+} pts |
| **Fréquentation** | {freq_n} clts | -              | -              | {freq_n1} clts | {freq_evo:+} % |
| **Panier Moyen**  | {panier_n} € | -               | -              | {panier_n1} € | {panier_evo:+} % |
```

### Colonne Statut — Section 3

Appliquer une icône sur **toutes les lignes** de Section 3, basée sur le signe de l'Évolution / N-1 :

```python
def statut_n1(evo_str):
    """evo_str ex: '+17,3 %' ou '-5,5 %' ou '+7,0 pts'"""
    val = float(evo_str.replace(' %', '').replace(' pts', '').replace(',', '.').replace('+', ''))
    if val > 0:    return '🟢'
    elif val == 0: return '🟡'
    else:          return '🔴'
```

### Section 3 LS — Format attendu

```markdown
| **CA TTC Magasin** | {ls_ca} €     | {ls_obj} € | {ls_n1} €        | {ls_evo:+} %        | {statut_n1(ls_evo)} |
| **Marge Magasin**  | {ls_marge} %  | -          | {ls_marge_n1} %  | {ls_marge_evo:+} pts | {statut_n1(ls_marge_evo)} |
| **Panier Moyen LS**| {ls_panier} € | -          | {ls_panier_n1} € | {ls_panier_evo:+} % | {statut_n1(ls_panier_evo)} |
```

### Section 3 Atelier — Format attendu

```markdown
| **CA TTC Atelier**    | {at_ca} €    | {at_obj} €  | {at_n1} €         | {at_evo:+} %         | {statut_n1(at_evo)} |
| **Marge Atelier**     | {at_marge} % | -           | {at_marge_n1} %   | {at_marge_evo:+} pts | {statut_n1(at_marge_evo)} |
| **Nombre d'OR**       | {at_nb_or}   | -           | {at_nb_or_n1}     | {at_nb_or_evo:+} %  | {statut_n1(at_nb_or_evo)} |
| **Panier Moyen Atel.**| {at_panier} €| -           | {at_panier_n1} €  | {at_panier_evo:+} % | {statut_n1(at_panier_evo)} |
```         