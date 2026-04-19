---
description: chiffre trimestriel
---

<<<<<<< HEAD
ALWAYS use this skill when the user types "/chiffre-trimestriel". Execute the Python
script below in full. It reads the single quarterly SUC CSV, extracts all values,
computes all KPIs, creates the report file, and fills Sections 2 and 3.
Do NOT interpret or read the CSV yourself.
=======
ALWAYS use this skill when the user types "/chiffre-trimestriel". When triggered,
automatically create a new rapport trimestriel file from the template, name it with the
correct quarter and year, and fill sections 2 and 3 from the SUC CSV file in
resources/trimestres/SUC/.
>>>>>>> origin/main
Other triggers: "remplis le rapport trimestriel", "mets à jour les chiffres du trimestre",
"fill the quarterly report", "analyse trimestrielle".

---

# Skill : Analyse des Chiffres — Rapport Trimestriel Feu Vert Annecy

<<<<<<< HEAD
## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité.**
Python fait tout : scan, extraction, calculs, création du fichier, remplissage S2 et S3.
L'IA ne lit pas le CSV. À la fin, l'IA reçoit uniquement le dict `kpis`
pour rédiger la Section 1, puis invoque `/familles-trimestriel`.

---

```python
import os, glob, re, shutil, csv, pathlib
from datetime import datetime

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
=======
## Vue d'ensemble

Ce skill lit le fichier CSV exporté depuis le système SUC stocké dans
`resources/trimestres/SUC/` et remplit les sections 2 et 3 du rapport trimestriel.

**Différence clé vs le skill hebdomadaire / mensuel** : un **seul fichier SUC** est
présent — il couvre la période complète du trimestre (`Du 01/MM/AAAA` au dernier jour
du trimestre). Ce fichier contient les données globales, LS, Atelier, familles et marge
en euros. Les valeurs N-1 sont **dérivées** depuis le réalisé N et les évolutions %,
comme pour le skill hebdomadaire. Il n'y a **pas de fichier objectifs** trimestriel
dédié — la colonne `textbox84` (% réalisation vs objectif) est utilisée pour retrouver
l'objectif.

---

## Workflow — Commande `/chiffre-trimestriel`

### Étape 1 — Identifier le fichier CSV

```python
import os, glob, pathlib, re
from datetime import datetime
>>>>>>> origin/main

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
<<<<<<< HEAD
    raise FileNotFoundError(f"Cannot find directory '{name}'")

TRIMESTRE_MAP = {3: 'T1', 6: 'T2', 9: 'T3', 12: 'T4'}

def clean_num(s):
    return float(s.replace('\xa0','').replace(' ','').replace('€','')
                  .replace('%','').replace(',','.').replace('+','').strip())

def fmt_eur(val):
    return f"{int(round(val)):,}".replace(',', ' ') + ' €'

def fmt_pct(val, sign=True):
    s = f"{val:+.1f}" if sign else f"{val:.1f}"
    return s.replace('.', ',') + ' %'

def fmt_pts(val):
    return f"{val:+.1f}".replace('.', ',') + ' pts'

def statut(evo_val):
    if evo_val > 0:    return '🟢'
    elif evo_val == 0: return '🟡'
    else:              return '🔴'

def read_raw(path):
    with open(path, 'r', encoding='utf-8-sig') as fh:
        return fh.read()

def parse_global_block(content):
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if line.startswith('caht_n,') or line.startswith('cattc_n,'):
            headers = next(csv.reader([line]))
            data    = next(csv.reader([lines[i + 1]]))
            return dict(zip(headers, data))
    return {}

def parse_ls_block(content):
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if line.startswith('textbox22,'):
            headers = next(csv.reader([line]))
            data    = next(csv.reader([lines[i + 1]]))
            return dict(zip(headers, data))
    return {}

def parse_atelier_block(content):
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if line.startswith('textbox43,'):
            headers = next(csv.reader([line]))
            data    = next(csv.reader([lines[i + 1]]))
            return dict(zip(headers, data))
    return {}

def extraire_marge_eur(content):
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if line.startswith('libelle,marge_n_2'):
            parts    = lines[i + 1].split(',')
            marge_n  = int(parts[1].replace('\xa0','').replace(' ','').strip())
            marge_n1 = int(parts[2].replace('\xa0','').replace(' ','').strip())
            evo_raw  = parts[3].strip() if len(parts) > 3 else '0 %'
            try:
                evo = clean_num(evo_raw)
            except:
                evo = round((marge_n / marge_n1 - 1) * 100, 1) if marge_n1 else 0
            return marge_n, marge_n1, evo
    return None, None, None

# ─────────────────────────────────────────────
# STEP 1 — SCAN AND IDENTIFY CSV FILE
# ─────────────────────────────────────────────

folder    = str(find_dir("trimestres") / "SUC")
csv_files = glob.glob(os.path.join(folder, "SUC - *.csv"))

assert csv_files, "ERREUR : aucun fichier SUC - *.csv trouvé dans resources/trimestres/SUC/"
fichier_trimestre = csv_files[0]
content = read_raw(fichier_trimestre)

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE QUARTER AND YEAR
# ─────────────────────────────────────────────

# Line format: "Du 01/01/2026,31/03/2026"
lines = content.replace('\r\n', '\n').split('\n')
date_debut_str = date_fin_str = None
for line in lines:
    if line.startswith('Du '):
        parts          = line.split(',')
        date_debut_str = parts[0].replace('Du ', '').strip()
        date_fin_str   = parts[1].strip()
        break

assert date_fin_str, "ERREUR : ligne de période 'Du ...' introuvable dans le CSV."
date_fin  = datetime.strptime(date_fin_str, "%d/%m/%Y")
trimestre = TRIMESTRE_MAP.get(date_fin.month, 'T?')
annee     = date_fin.year

# ─────────────────────────────────────────────
# STEP 3 — CREATE REPORT FILE FROM TEMPLATE
# ─────────────────────────────────────────────

template_path = str(find_dir("templates") / "rapport_trimestriel_template.md")
output_dir    = str(find_dir("trimestres"))
os.makedirs(output_dir, exist_ok=True)
output_name   = f"rapport trimestriel {trimestre} {annee}.md"
output_path   = os.path.join(output_dir, output_name)

if not os.path.exists(output_path):
    shutil.copy(template_path, output_path)

# ─────────────────────────────────────────────
# STEP 4 — EXTRACT ALL VALUES
# ─────────────────────────────────────────────

# — Global block —
g = parse_global_block(content)

cattc_n    = clean_num(g.get('cattc_n', '0'))
ca_evo     = clean_num(g.get('textbox4', '0'))
ca_real_pct = clean_num(g.get('textbox84', '100'))   # % réalisation vs objectif
marge_n    = clean_num(g.get('marge_n', '0'))
marge_evo  = clean_num(g.get('textbox24', '0'))
panier_n   = clean_num(g.get('cattc_n_2', '0'))
panier_evo = clean_num(g.get('textbox17', '0'))

# Derived N-1 values (no N-1 file — must derive)
ca_n1      = round(cattc_n / (1 + ca_evo / 100)) if ca_evo != -100 else 0
ca_obj     = round(cattc_n / (ca_real_pct / 100)) if ca_real_pct else 0
ca_ecart   = round(ca_real_pct - 100, 1)
marge_n1   = round(marge_n - marge_evo, 1)
panier_n1  = round(panier_n / (1 + panier_evo / 100), 1) if panier_evo != -100 else 0

# Marge € — read from marge bloc
marge_eur_n, marge_eur_n1, marge_eur_evo = extraire_marge_eur(content)
marge_eur_n  = marge_eur_n  or 0
marge_eur_n1 = marge_eur_n1 or 0
marge_eur_evo = marge_eur_evo or 0

# No explicit marge obj in quarterly CSV
marge_obj_pct = 'N/A'
marge_obj_eur = 'N/A'

# — LS block —
ls = parse_ls_block(content)
ls_ca       = clean_num(ls.get('textbox27', '0'))
ls_evo      = clean_num(ls.get('textbox25', '0'))
ls_marge    = clean_num(ls.get('textbox31', '0'))
ls_marge_evo = clean_num(ls.get('textbox33', '0'))
ls_panier   = clean_num(ls.get('textbox39', '0'))
ls_panier_evo = clean_num(ls.get('textbox41', '0'))

ls_n1        = round(ls_ca / (1 + ls_evo / 100))       if ls_evo != -100 else 0
ls_marge_n1  = round(ls_marge - ls_marge_evo, 1)
ls_panier_n1 = round(ls_panier / (1 + ls_panier_evo / 100), 1) if ls_panier_evo != -100 else 0

# — Atelier block —
at = parse_atelier_block(content)
at_ca       = clean_num(at.get('textbox47', '0'))
at_evo      = clean_num(at.get('textbox45', '0'))
at_marge    = clean_num(at.get('textbox51', '0'))
at_marge_evo = clean_num(at.get('textbox53', '0'))
at_nb_or    = int(clean_num(at.get('textbox55', '0')))
at_nb_or_evo = clean_num(at.get('textbox57', '0'))
at_panier   = clean_num(at.get('textbox62', '0'))
at_panier_evo = clean_num(at.get('textbox64', '0'))

at_n1        = round(at_ca / (1 + at_evo / 100))         if at_evo != -100 else 0
at_marge_n1  = round(at_marge - at_marge_evo, 1)
at_nb_or_n1  = round(at_nb_or / (1 + at_nb_or_evo / 100)) if at_nb_or_evo != -100 else 0
at_panier_n1 = round(at_panier / (1 + at_panier_evo / 100), 1) if at_panier_evo != -100 else 0

# ─────────────────────────────────────────────
# STEP 5 — FILL THE REPORT (pure str.replace)
# ─────────────────────────────────────────────

with open(output_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

# Header
rapport = rapport.replace('[T1/T2/T3/T4] [AAAA]', f'{trimestre} {annee}')

# — Section 2 —
rapport = rapport.replace(
    "| **CA TTC Total** | € | € | % | € | % |",
    f"| **CA TTC Total** | {fmt_eur(cattc_n)} | {fmt_eur(ca_obj)} | {fmt_pct(ca_ecart)} | {fmt_eur(ca_n1)} | {fmt_pct(ca_evo)} |"
)
rapport = rapport.replace(
    "| **Marge Brute %** | % | % | pts | % | pts |",
    f"| **Marge Brute %** | {fmt_pct(marge_n, sign=False)} | {marge_obj_pct} | N/A | {fmt_pct(marge_n1, sign=False)} | {fmt_pts(marge_evo)} |"
)
rapport = rapport.replace(
    "| **Marge Brute (€)** | € | € | % | € | % |",
    f"| **Marge Brute (€)** | {fmt_eur(marge_eur_n)} | {marge_obj_eur} | N/A | {fmt_eur(marge_eur_n1)} | {fmt_pct(marge_eur_evo)} |"
)
rapport = rapport.replace(
    "| **Panier Moyen** | € | - | - | € | % |",
    f"| **Panier Moyen** | {fmt_eur(panier_n)} | - | - | {fmt_eur(panier_n1)} | {fmt_pct(panier_evo)} |"
)

# — Section 3 LS —
rapport = rapport.replace(
    "| **CA TTC Magasin** | € | € | % | |",
    f"| **CA TTC Magasin** | {fmt_eur(ls_ca)} | {fmt_eur(ls_n1)} | {fmt_pct(ls_evo)} | {statut(ls_evo)} |"
)
rapport = rapport.replace(
    "| **Marge Magasin %** | % | % | pts | |",
    f"| **Marge Magasin %** | {fmt_pct(ls_marge, sign=False)} | {fmt_pct(ls_marge_n1, sign=False)} | {fmt_pts(ls_marge_evo)} | {statut(ls_marge_evo)} |"
)
rapport = rapport.replace(
    "| **Panier Moyen LS** | € | € | % | |",
    f"| **Panier Moyen LS** | {fmt_eur(ls_panier)} | {fmt_eur(ls_panier_n1)} | {fmt_pct(ls_panier_evo)} | {statut(ls_panier_evo)} |"
)

# — Section 3 Atelier —
rapport = rapport.replace(
    "| **CA TTC Atelier** | € | € | % | |",
    f"| **CA TTC Atelier** | {fmt_eur(at_ca)} | {fmt_eur(at_n1)} | {fmt_pct(at_evo)} | {statut(at_evo)} |"
)
rapport = rapport.replace(
    "| **Marge Atelier %** | % | % | pts | |",
    f"| **Marge Atelier %** | {fmt_pct(at_marge, sign=False)} | {fmt_pct(at_marge_n1, sign=False)} | {fmt_pts(at_marge_evo)} | {statut(at_marge_evo)} |"
)
rapport = rapport.replace(
    "| **Nombre d'OR** | | | % | |",
    f"| **Nombre d'OR** | {at_nb_or} | {at_nb_or_n1} | {fmt_pct(at_nb_or_evo)} | {statut(at_nb_or_evo)} |"
)
rapport = rapport.replace(
    "| **Panier Moyen Atel.** | € | € | % | |",
    f"| **Panier Moyen Atel.** | {fmt_eur(at_panier)} | {fmt_eur(at_panier_n1)} | {fmt_pct(at_panier_evo)} | {statut(at_panier_evo)} |"
)

with open(output_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 6 — EXPOSE KPIs FOR SECTION 1 NARRATIVE
# ─────────────────────────────────────────────

kpis = {
    "trimestre":      f"{trimestre} {annee}",
    "ca_ttc":         int(cattc_n),
    "ca_obj":         ca_obj,
    "ca_ecart_pct":   ca_ecart,
    "ca_evo_pct":     ca_evo,
    "marge_pct":      marge_n,
    "marge_evo_pts":  marge_evo,
    "marge_eur":      marge_eur_n,
    "marge_eur_evo":  marge_eur_evo,
    "ls_ca":          int(ls_ca),
    "ls_evo_pct":     ls_evo,
    "ls_marge_pct":   ls_marge,
    "at_ca":          int(at_ca),
    "at_evo_pct":     at_evo,
    "at_marge_pct":   at_marge,
    "at_nb_or":       at_nb_or,
    "rapport_path":   output_path,
}

print(f"✅ Rapport créé      : {output_path}")
print(f"✅ Trimestre         : {trimestre} {annee}")
print(f"✅ CA TTC            : {fmt_eur(cattc_n)} | Obj : {fmt_eur(ca_obj)} | Écart : {fmt_pct(ca_ecart)}")
print(f"✅ Marge %           : {fmt_pct(marge_n, sign=False)} | Évo N-1 : {fmt_pts(marge_evo)}")
print(f"✅ Marge €           : {fmt_eur(marge_eur_n)} | Évo N-1 : {fmt_pct(marge_eur_evo)}")
print(f"✅ LS CA             : {fmt_eur(ls_ca)} ({fmt_pct(ls_evo)})")
print(f"✅ Atelier CA        : {fmt_eur(at_ca)} ({fmt_pct(at_evo)})")
=======
    raise FileNotFoundError(f"Cannot find directory '{name}' in any parent of {pathlib.Path.cwd()}")

folder = str(find_dir("trimestres") / "SUC")
csv_files = glob.glob(os.path.join(folder, "SUC - *.csv"))

if not csv_files:
    raise FileNotFoundError("Aucun fichier SUC - *.csv trouvé dans resources/trimestres/SUC/")

# Prendre le premier (ou le seul) fichier
fichier_trimestre = csv_files[0]

with open(fichier_trimestre, 'r', encoding='utf-8-sig') as fh:
    content = fh.read()
```

### Étape 2 — Déterminer le trimestre et l'année

Lire la date de fin depuis la ligne de période (`textbox72`) :

```python
lines = content.replace('\r\n', '\n').split('\n')

# Ligne type : "Du 01/01/2026,31/03/2026"
date_debut_str = None
date_fin_str = None
for line in lines:
    if line.startswith('Du '):
        parts = line.split(',')
        date_debut_str = parts[0].replace('Du ', '').strip()
        date_fin_str = parts[1].strip()
        break

date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
mois_fin = date_fin.month
annee = date_fin.year

# Déduire le trimestre depuis le mois de fin
TRIMESTRE_MAP = {3: 'T1', 6: 'T2', 9: 'T3', 12: 'T4'}
trimestre = TRIMESTRE_MAP.get(mois_fin, f'T?')
# Ex : "T1 2026"
```

### Étape 3 — Créer ou localiser le fichier rapport

```python
import shutil

template_path = str(find_dir("templates") / "rapport_trimestriel_template.md")
output_dir = str(find_dir("trimestres"))
output_name = f"rapport trimestriel {trimestre} {annee}.md"
output_path = os.path.join(output_dir, output_name)

# Créer le dossier si absent
os.makedirs(output_dir, exist_ok=True)

# Créer depuis le template si le fichier n'existe pas déjà
if not os.path.exists(output_path):
    shutil.copy(template_path, output_path)
```

> Si le rapport existe déjà (ex: déjà créé par `/familles-trimestriel`), le réutiliser
> et ne remplacer que les sections 2 et 3.

### Étape 4 — Extraire les valeurs depuis le CSV

Le fichier est structuré en **blocs séparés par des lignes vides**. Lire en brut
(`open(..., encoding='utf-8-sig')`), séparer les blocs, identifier chaque bloc
par sa ligne d'en-tête.

#### Structure du fichier CSV trimestriel

| Bloc | Ligne header | Contenu |
|:-----|:-------------|:--------|
| 1 | `nbContratEntretien_DECI,nbCE_G6K` | Contrats entretien (non utilisé ici) |
| 2 | `textbox1,textbox72` | Période (`Du 01/01/2026,31/03/2026`) |
| 3 | `LIBELLEMAGASIN` | Nom du magasin |
| 4 | `textbox250,textbox256` | Plage de dates N et N-1 |
| 5 | `caht_n,textbox4,...` | **Bloc Global** (Section 2) |
| 6 | `textbox22,textbox25,...` | **Bloc LS** (Section 3 LS) |
| 7 | `textbox43,textbox45,...` | **Bloc Atelier** (Section 3 Atelier) |
| 8 | `textbox76,textbox19,...` | Détail familles (utilisé par /familles-trimestriel) |
| 9 | `libelle,marge_n_2,...` | **Marge en euros** (Section 2 Marge €) |

#### Bloc Global (Section 2)

```
Header : caht_n, textbox4, textbox74, textbox84, cattc_n, textbox16,
         marge_n, textbox24, textbox78, textbox86, textbox11,
         nbPassage_n, textbox14, cattc_n_2, textbox17
```

| Champ CSV     | Signification                          | Section |
|:--------------|:---------------------------------------|:--------|
| `cattc_n`     | CA TTC réalisé (N)                     | S2      |
| `textbox4`    | Évolution CA vs N-1 (%)               | S2      |
| `textbox84`   | % réalisation vs objectif (%)         | S2 (pour retrouver l'objectif) |
| `marge_n`     | Taux de marge global (%)              | S2      |
| `textbox24`   | Évolution marge vs N-1 (pts)          | S2      |
| `textbox14`   | Nb clients (fréquentation)            | S2 (info)     |
| `textbox17`   | Évolution fréquentation / panier (%)  | S2      |
| `cattc_n_2`   | Panier moyen TTC (€)                  | S2      |

#### Bloc LS (Section 3)

```
Header : textbox22, textbox25, textbox27, textbox29, textbox31,
         textbox33, textbox34, textbox35, textbox37, textbox39, textbox41
```

| Champ CSV     | Signification                  |
|:--------------|:-------------------------------|
| `textbox27`   | CA TTC LS réalisé (N)          |
| `textbox25`   | Évolution CA LS vs N-1 (%)    |
| `textbox31`   | Taux de marge LS (%)           |
| `textbox33`   | Évolution marge LS (pts)       |
| `textbox35`   | Nb clients LS                  |
| `textbox37`   | Évolution fréq LS (%)          |
| `textbox39`   | Panier moyen TTC LS (€)        |
| `textbox41`   | Évolution panier LS (%)        |

#### Bloc Atelier (Section 3)

```
Header : textbox43, textbox45, textbox47, textbox49, textbox51,
         textbox53, textbox54, textbox55, textbox57, textbox62, textbox64
```

| Champ CSV     | Signification                    |
|:--------------|:---------------------------------|
| `textbox47`   | CA TTC Atelier réalisé (N)       |
| `textbox45`   | Évolution CA Atelier vs N-1 (%) |
| `textbox51`   | Taux de marge Atelier (%)        |
| `textbox53`   | Évolution marge Atelier (pts)    |
| `textbox55`   | Nb OR (ordres de réparation)     |
| `textbox57`   | Évolution Nb OR (%)              |
| `textbox62`   | Panier moyen Atelier TTC (€)     |
| `textbox64`   | Évolution panier Atelier (%)     |

#### Bloc Marge en Euros (Section 2 — Marge Brute €)

```
Header : libelle, marge_n_2, marge_n_1_1, textbox92
Valeur : Marge Produit, 149 800, 135 222, 11 %
```

| Champ CSV     | Signification                  |
|:--------------|:-------------------------------|
| `marge_n_2`   | Marge produit N (€)            |
| `marge_n_1_1` | Marge produit N-1 (€)          |
| `textbox92`   | Évolution marge € (%)          |

---

## Calculs à effectuer

### Section 2

```python
def parse_val(s):
    """Convertit '730 667' ou '75,0 €' en float/int."""
    clean = s.replace('\xa0','').replace(' ','').replace('€','').replace('%','').replace(',','.').replace('+','').strip()
    try:
        return float(clean)
    except:
        return None

def parse_pct(s):
    """Convertit '11,4 %' ou '+7,7 %' ou '-5,5 pts' en float."""
    clean = s.replace(' %','').replace(' pts','').replace(',','.').replace('+','').strip()
    try:
        return float(clean)
    except:
        return None

# --- CA TTC ---
cattc_n = parse_val(cattc_n_raw)                # ex: 730667
ca_evo  = parse_pct(textbox4_raw)               # ex: 11.4
ca_n1   = round(cattc_n / (1 + ca_evo / 100))   # N-1 dérivé
ca_real_pct = parse_pct(textbox84_raw)           # ex: 103.9
ca_obj  = round(cattc_n / (ca_real_pct / 100))   # Objectif retrouvé
ca_ecart = round(ca_real_pct - 100, 1)           # Écart vs objectif en %

# --- Marge % ---
marge_n   = parse_pct(marge_n_raw)               # ex: 51.0
marge_evo = parse_pct(textbox24_raw)             # ex: 7.7
marge_n1  = round(marge_n - marge_evo, 1)        # N-1 = N - évolution pts

# --- Marge € ---
marge_eur_n  = parse_val(marge_n_2_raw)          # ex: 149800
marge_eur_n1 = parse_val(marge_n_1_1_raw)        # ex: 135222
marge_eur_evo = parse_pct(textbox92_raw)         # ex: 11
# Objectif marge € : dériver depuis textbox84 (% réalisation globale)
# ou indiquer N/A si pas d'objectif marge explicite dans le fichier
marge_obj_eur = 'N/A'   # Pas d'objectif marge € dans le CSV trimestriel

# --- Panier Moyen TTC ---
panier_n   = parse_val(cattc_n_2_raw)            # ex: 75.0
panier_evo = parse_pct(textbox17_raw)            # ex: 5.8
panier_n1  = round(panier_n / (1 + panier_evo / 100), 1)
```

> **Note importante** : Le panier moyen dans le CSV est déjà TTC — utiliser directement,
> ne pas diviser par 1.2.

> **Objectif CA TTC** : retrouvé via `cattc_n / (textbox84 / 100)`.
> Par exemple : 730 667 / 1.039 = **703 240 €** (arrondi).

> **Objectif Marge %** : non disponible directement. Indiquer `N/A` ou, si un fichier
> objectifs trimestriel est fourni, le lire depuis ce fichier.

### Section 3 — LS

```python
# CA TTC LS
ls_ca    = parse_val(textbox27_raw)              # ex: 269590
ls_evo   = parse_pct(textbox25_raw)              # ex: 17.1
ls_n1    = round(ls_ca / (1 + ls_evo / 100))     # N-1 dérivé

# Marge LS
ls_marge     = parse_pct(textbox31_raw)          # ex: 40.2
ls_marge_evo = parse_pct(textbox33_raw)          # ex: 15.4
ls_marge_n1  = round(ls_marge - ls_marge_evo, 1)

# Panier LS
ls_panier     = parse_val(textbox39_raw)         # ex: 34.7
ls_panier_evo = parse_pct(textbox41_raw)         # ex: 12.3
ls_panier_n1  = round(ls_panier / (1 + ls_panier_evo / 100), 1)
```

### Section 3 — Atelier

```python
# CA TTC Atelier
at_ca    = parse_val(textbox47_raw)              # ex: 461077
at_evo   = parse_pct(textbox45_raw)              # ex: 8.3
at_n1    = round(at_ca / (1 + at_evo / 100))     # N-1 dérivé

# Marge Atelier
at_marge     = parse_pct(textbox51_raw)          # ex: 57.3
at_marge_evo = parse_pct(textbox53_raw)          # ex: 4.9
at_marge_n1  = round(at_marge - at_marge_evo, 1)

# Nb OR
at_nb_or     = int(parse_val(textbox55_raw))     # ex: 2117
at_nb_or_evo = parse_pct(textbox57_raw)          # ex: 8.5
at_nb_or_n1  = round(at_nb_or / (1 + at_nb_or_evo / 100))

# Panier Atelier
at_panier     = parse_val(textbox62_raw)         # ex: 217.8
at_panier_evo = parse_pct(textbox64_raw)         # ex: -0.2
at_panier_n1  = round(at_panier / (1 + at_panier_evo / 100), 1)
>>>>>>> origin/main
```

---

<<<<<<< HEAD
## Après exécution du script

Sections 2 et 3 remplies sans intervention de l'IA.

**L'IA rédige uniquement la Section 1** depuis le dict `kpis` :

> "Rédige la Section 1 (Revue Stratégique) du rapport trimestriel Feu Vert Annecy {kpis['trimestre']}.
> CA TTC : {kpis['ca_ttc']} € | Obj : {kpis['ca_obj']} € | Écart : {kpis['ca_ecart_pct']} %
> Marge % : {kpis['marge_pct']} % ({kpis['marge_evo_pts']:+} pts vs N-1)
> Marge € : {kpis['marge_eur']} € ({kpis['marge_eur_evo']:+} % vs N-1)
> LS : {kpis['ls_ca']} € ({kpis['ls_evo_pct']:+} % vs N-1) | Atelier : {kpis['at_ca']} € ({kpis['at_evo_pct']:+} % vs N-1)
> Ton : senior business analyst, perspective trimestrielle, 3-4 phrases, en français."

Ensuite invoquer automatiquement `/familles-trimestriel`.
=======
## Remplissage du rapport

### En-tête du rapport

Remplacer `[T1/T2/T3/T4] [AAAA]` par le trimestre et l'année :

```python
rapport = rapport.replace('[T1/T2/T3/T4] [AAAA]', f'{trimestre} {annee}')
```

### Section 2 — Format attendu

```markdown
| **CA TTC Total** | {cattc_n:,.0f} € | {ca_obj:,.0f} € | {ca_ecart:+.1f} % | {ca_n1:,.0f} € | {ca_evo:+.1f} % |
| **Marge Brute %** | {marge_n:.1f} % | N/A | N/A | {marge_n1:.1f} % | {marge_evo:+.1f} pts |
| **Marge Brute (€)** | {marge_eur_n:,.0f} € | N/A | N/A | {marge_eur_n1:,.0f} € | {marge_eur_evo:+.1f} % |
| **Panier Moyen** | {panier_n:.1f} € | - | - | {panier_n1:.1f} € | {panier_evo:+.1f} % |
```

> **Formatage** : utiliser l'espace comme séparateur milliers et la virgule comme
> séparateur décimal (format français). Ex: `730 667 €`, `51,0 %`.

### Colonne Statut — Section 3

Appliquer une icône basée sur le signe de l'Évolution / N-1 :

```python
def statut_n1(evo_str):
    """evo_str ex: '+17,1 %' ou '-0,2 %' ou '+4,9 pts'"""
    val = parse_pct(evo_str)
    if val is None:  return '⚪'
    if val > 0:      return '🟢'
    if val == 0:     return '🟡'
    return '🔴'
```

### Section 3 LS — Format attendu

```markdown
| **CA TTC Magasin** | {ls_ca:,.0f} € | {ls_n1:,.0f} € | {ls_evo:+.1f} % | {statut_n1(ls_evo)} |
| **Marge Magasin %** | {ls_marge:.1f} % | {ls_marge_n1:.1f} % | {ls_marge_evo:+.1f} pts | {statut_n1(ls_marge_evo)} |
| **Panier Moyen LS** | {ls_panier:.1f} € | {ls_panier_n1:.1f} € | {ls_panier_evo:+.1f} % | {statut_n1(ls_panier_evo)} |
```

### Section 3 Atelier — Format attendu

```markdown
| **CA TTC Atelier** | {at_ca:,.0f} € | {at_n1:,.0f} € | {at_evo:+.1f} % | {statut_n1(at_evo)} |
| **Marge Atelier %** | {at_marge:.1f} % | {at_marge_n1:.1f} % | {at_marge_evo:+.1f} pts | {statut_n1(at_marge_evo)} |
| **Nombre d'OR** | {at_nb_or} | {at_nb_or_n1} | {at_nb_or_evo:+.1f} % | {statut_n1(at_nb_or_evo)} |
| **Panier Moyen Atel.** | {at_panier:.1f} € | {at_panier_n1:.1f} € | {at_panier_evo:+.1f} % | {statut_n1(at_panier_evo)} |
```

---

## Étape 5 — Chaîner `/familles-trimestriel`

À la fin de l'exécution, invoquer automatiquement le skill `/familles-trimestriel`
pour remplir la section **Analyse spécifique / Familles** du même rapport.

> **Note** : Le skill `/familles-trimestriel` utilisera le fichier
> `comparatifCAv2_Famille*.csv` dans `Resources trimestrielles/Familles/` si disponible.
> Si ce fichier n'est pas présent mais que des données familles existent dans le fichier
> SUC trimestriel (bloc `textbox76,textbox19,...`), le skill peut utiliser ces données
> comme source alternative.

---

## Étape 6 — Confirmer à l'utilisateur

Indiquer :
- Nom du fichier créé ou mis à jour
- Trimestre et année détectés
- Résumé des valeurs clés :
  - CA TTC trimestriel, évolution vs N-1
  - Marge % et marge €
  - Panier moyen
  - CA LS et CA Atelier avec évolutions

---

## Règles spécifiques au trimestriel

- **Un seul fichier CSV** : pas de distinction semaine/MTD/objectifs — tout est dans un seul fichier.
- **Valeurs N-1 dérivées** : calculées via `réalisé_N / (1 + evo/100)`, sauf marge % (en pts : `marge_n - evo_pts`).
- **Pas de Section 7 RAF** : la section RAF n'existe pas dans le rapport trimestriel.
- **Pas d'objectif marge explicite** : le CSV ne contient pas d'objectif marge % ni marge €. Indiquer `N/A`.
- **Objectif CA TTC** : retrouvé via `cattc_n / (textbox84 / 100)` (% réalisation vs objectif).
- **Dossier source** : `resources/trimestres/SUC/` (distinct de `resources/SUC/` hebdo et `resources/Resources mensuelles/SUC/` mensuel).
- **Dossier de sortie** : `resources/trimestres/` ou `Rapport trimestriel/` selon l'organisation existante.

---

## Identification du fichier CSV

| Fichier | Identification | Utilisé pour |
|:--------|:---------------|:-------------|
| `SUC - Situation de chiffre*.csv` | `Du 01/` + date couvrant un trimestre complet (3 mois) | `fichier_trimestre` — Réalisé N, N-1 dérivé (S2, S3) |

---

## Règles de formatage

- CA en **€ TTC** — utiliser les colonnes TTC directement, **ne pas diviser par 1.2**
- Panier moyen en **€ TTC** — utiliser `cattc_n_2`, `textbox39`, `textbox62` directement
- Séparateur décimal : **virgule** (ex: `51,0 %`)
- Espacement milliers : **espace** (ex: `730 667 €`)
- Évolutions : toujours afficher le signe (`+11,4 %`, `-0,2 pts`)
- Valeur absente ou non disponible : `N/A`
- Marge en pts : toujours `+X,X pts` ou `-X,X pts`
>>>>>>> origin/main
