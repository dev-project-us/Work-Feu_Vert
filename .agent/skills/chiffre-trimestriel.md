---
description: chiffre trimestriel
---

ALWAYS use this skill when the user types "/chiffre-trimestriel". Execute the Python
script below in full. It reads the single quarterly SUC CSV, extracts all values,
computes all KPIs, creates the report file, and fills Sections 2 and 3.
Do NOT interpret or read the CSV yourself.
Other triggers: "remplis le rapport trimestriel", "mets à jour les chiffres du trimestre",
"fill the quarterly report", "analyse trimestrielle".

---

# Skill : Analyse des Chiffres — Rapport Trimestriel Feu Vert Annecy

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

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
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
```

---

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
