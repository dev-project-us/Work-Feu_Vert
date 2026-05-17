---
description: chiffre mensuel
---

ALWAYS use this skill when the user types "/chiffre-mensuel". Execute the Python
script below in full. It scans the monthly SUC CSV files, extracts all values,
computes all KPIs, fills Sections 2 and 3 of the monthly report, then chains
/ratios-mensuel. Do NOT interpret or read the CSV files yourself.
Other triggers: "remplis le rapport mensuel", "mets à jour les chiffres du mois",
"fill the monthly report".

---

# Skill : Analyse des Chiffres — Rapport Mensuel Feu Vert Annecy

## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité.**
Python fait tout : scan, extraction, calculs, création du fichier, remplissage.
L'IA ne lit pas les CSV. À la fin, l'IA reçoit uniquement le dict `kpis`
pour rédiger la Section 1, puis invoque `/ratios-mensuel`.

---

```python
import os, glob, re, shutil, csv, io, pathlib
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

MOIS_FR = {
    1:'janvier', 2:'février', 3:'mars', 4:'avril',
    5:'mai', 6:'juin', 7:'juillet', 8:'août',
    9:'septembre', 10:'octobre', 11:'novembre', 12:'décembre'
}

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

def parse_objectifs_block(content):
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if 'libelleJour' in line:
            headers = next(csv.reader([line]))
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == '':
                    continue
                row = next(csv.reader([lines[j]]))
                d = dict(zip(headers, row))
                try:
                    if clean_num(d.get('CATTC', '0')) != 0:
                        return d
                except:
                    continue
    return {}

def extraire_marge_eur(content):
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if line.startswith('libelle,marge_n_2'):
            parts = lines[i + 1].split(',')
            return int(parts[1].replace('\xa0','').replace(' ','').strip())
    return None

def extraire_marge_obj_eur(obj_content):
    """Last large numeric value from a data row in the objectifs file."""
    lines = obj_content.replace('\r\n', '\n').split('\n')
    headers = []
    for i, line in enumerate(lines):
        if 'libelleJour' in line:
            headers = next(csv.reader([line]))
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == '':
                    continue
                row = next(csv.reader([lines[j]]))
                # Last non-empty value in the row
                candidates = [v.replace('\xa0','').replace(' ','').strip()
                              for v in reversed(row) if v.strip()]
                for c in candidates:
                    try:
                        val = int(c)
                        if val > 10000:
                            return val
                    except:
                        continue
    return None

# ─────────────────────────────────────────────
# STEP 1 — SCAN AND IDENTIFY CSV FILES
# ─────────────────────────────────────────────

folder    = str(find_dir("monthly_recap") / "SUC")
csv_files = glob.glob(os.path.join(folder, "SUC - *.csv"))

annee_courante    = datetime.today().year
fichier_mtd       = None
fichier_n1        = None
fichier_objectifs = None

for f in csv_files:
    content = read_raw(f)
    if 'libelleJour' in content:
        fichier_objectifs = f
    elif 'Du 01/' in content:
        m = re.search(r'Du 01/\d{2}/(\d{4})', content)
        if m:
            if int(m.group(1)) == annee_courante:
                fichier_mtd = f
            else:
                fichier_n1  = f

assert fichier_mtd,       "ERREUR : fichier MTD (année N) introuvable dans monthly_recap/SUC/"
assert fichier_n1,        "ERREUR : fichier N-1 introuvable dans monthly_recap/SUC/"
assert fichier_objectifs, "ERREUR : fichier objectifs introuvable dans monthly_recap/SUC/"

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE MONTH AND YEAR
# ─────────────────────────────────────────────

mtd_content = read_raw(fichier_mtd)
n1_content  = read_raw(fichier_n1)
obj_content = read_raw(fichier_objectifs)

for line in mtd_content.replace('\r\n', '\n').split('\n'):
    if line.startswith('Du 01/'):
        date_fin_str = line.split(',')[1].strip()
        break

date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
mois_num = date_fin.month
annee    = date_fin.year
mois_str = MOIS_FR[mois_num]

# ─────────────────────────────────────────────
# STEP 3 — CREATE REPORT FILE FROM TEMPLATE
# ─────────────────────────────────────────────

template_path = str(find_dir("templates") / "rapport_mensuel_template.md")
output_dir    = str(find_dir("Rapport mensuel"))
os.makedirs(output_dir, exist_ok=True)
output_name   = f"rapport mensuel {mois_str} {annee}.md"
output_path   = os.path.join(output_dir, output_name)
shutil.copy(template_path, output_path)

# ─────────────────────────────────────────────
# STEP 4 — EXTRACT ALL VALUES
# ─────────────────────────────────────────────

# — Global block —
g   = parse_global_block(mtd_content)
g1  = parse_global_block(n1_content)
go  = parse_objectifs_block(obj_content)

cattc_n    = clean_num(g.get('cattc_n', '0'))
marge_n    = clean_num(g.get('marge_n', '0'))
marge_evo  = clean_num(g.get('textbox24', '0'))
panier_n   = clean_num(g.get('cattc_n_2', '0'))
caht_evo   = clean_num(g.get('textbox4', '0'))

cattc_n1   = clean_num(g1.get('cattc_n', '0'))
marge_n1   = clean_num(g1.get('marge_n', '0'))
panier_n1  = clean_num(g1.get('cattc_n_2', '0'))

ca_obj_ttc = int(clean_num(go.get('textbox8', '0')))
marge_obj  = clean_num(go.get('textbox50', '0'))

# Derived Section 2
ca_ecart   = round((cattc_n / ca_obj_ttc - 1) * 100, 1) if ca_obj_ttc else 0
ca_evo     = round((cattc_n / cattc_n1 - 1) * 100, 1)   if cattc_n1 else 0
marge_ecart = round(marge_n - marge_obj, 1)
panier_evo = round((panier_n / panier_n1 - 1) * 100, 1) if panier_n1 else 0

# Marge €
marge_eur_n   = extraire_marge_eur(mtd_content) or 0
marge_eur_n1  = extraire_marge_eur(n1_content)  or 0
marge_obj_eur = extraire_marge_obj_eur(obj_content) or 0
marge_eur_ecart = round((marge_eur_n / marge_obj_eur - 1) * 100, 1) if marge_obj_eur else 0
marge_eur_evo   = round((marge_eur_n / marge_eur_n1 - 1) * 100, 1)  if marge_eur_n1 else 0

# — LS block —
ls  = parse_ls_block(mtd_content)
ls1 = parse_ls_block(n1_content)

ls_ca       = clean_num(ls.get('textbox27', '0'))
ls_evo_obj  = clean_num(ls.get('textbox25', '0'))   # écart vs objectif
ls_marge    = clean_num(ls.get('textbox31', '0'))
ls_marge_evo = clean_num(ls.get('textbox33', '0'))
ls_panier   = clean_num(ls.get('textbox39', '0'))
ls_panier_evo = clean_num(ls.get('textbox41', '0'))

ls_ca_n1    = clean_num(ls1.get('textbox27', '0'))
ls_marge_n1 = clean_num(ls1.get('textbox31', '0'))
ls_panier_n1 = clean_num(ls1.get('textbox39', '0'))

ls_ca_evo   = round((ls_ca / ls_ca_n1 - 1) * 100, 1)       if ls_ca_n1 else 0
ls_marge_delta = round(ls_marge - ls_marge_n1, 1)
ls_panier_evo_n1 = round((ls_panier / ls_panier_n1 - 1) * 100, 1) if ls_panier_n1 else 0

# — Atelier block —
at  = parse_atelier_block(mtd_content)
at1 = parse_atelier_block(n1_content)

at_ca       = clean_num(at.get('textbox47', '0'))
at_evo_obj  = clean_num(at.get('textbox45', '0'))   # écart vs objectif
at_marge    = clean_num(at.get('textbox51', '0'))
at_marge_evo = clean_num(at.get('textbox53', '0'))
at_nb_or    = int(clean_num(at.get('textbox55', '0')))
at_nb_or_evo = clean_num(at.get('textbox57', '0'))
at_panier   = clean_num(at.get('textbox62', '0'))
at_panier_evo = clean_num(at.get('textbox64', '0'))

at_ca_n1     = clean_num(at1.get('textbox47', '0'))
at_marge_n1  = clean_num(at1.get('textbox51', '0'))
at_nb_or_n1  = int(clean_num(at1.get('textbox55', '0')))
at_panier_n1 = clean_num(at1.get('textbox62', '0'))

at_ca_evo    = round((at_ca / at_ca_n1 - 1) * 100, 1)       if at_ca_n1 else 0
at_marge_delta = round(at_marge - at_marge_n1, 1)
at_nb_or_evo_n1 = round((at_nb_or / at_nb_or_n1 - 1) * 100, 1) if at_nb_or_n1 else 0
at_panier_evo_n1 = round((at_panier / at_panier_n1 - 1) * 100, 1) if at_panier_n1 else 0

# ─────────────────────────────────────────────
# STEP 5 — FILL THE REPORT (pure str.replace)
# ─────────────────────────────────────────────

with open(output_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

# Header
rapport = rapport.replace('[Mois AAAA]', f'{mois_str.capitalize()} {annee}')

# — Section 2 (spaced alignment rows — match exactly) —
rapport = rapport.replace(
    "| **CA TTC Total**    | €           | €        | %           | €   | %               |",
    f"| **CA TTC Total**    | {fmt_eur(cattc_n)} | {fmt_eur(ca_obj_ttc)} | {fmt_pct(ca_ecart)} | {fmt_eur(cattc_n1)} | {fmt_pct(ca_evo)} |"
)
rapport = rapport.replace(
    "| **Marge Brute**     | %           | %        | pts         | %   | pts             |",
    f"| **Marge Brute**     | {fmt_pct(marge_n, sign=False)} | {fmt_pct(marge_obj, sign=False)} | {fmt_pts(marge_ecart)} | {fmt_pct(marge_n1, sign=False)} | {fmt_pts(marge_evo)} |"
)
rapport = rapport.replace(
    "| **Marge Brute (€)** | €           | €        | %           | €   | %               |",
    f"| **Marge Brute (€)** | {fmt_eur(marge_eur_n)} | {fmt_eur(marge_obj_eur)} | {fmt_pct(marge_eur_ecart)} | {fmt_eur(marge_eur_n1)} | {fmt_pct(marge_eur_evo)} |"
)
rapport = rapport.replace(
    "| **Panier Moyen**    | €           | -        | -           | €   | %               |",
    f"| **Panier Moyen**    | {fmt_eur(panier_n)} | - | - | {fmt_eur(panier_n1)} | {fmt_pct(panier_evo)} |"
)

# — Section 3 LS —
rapport = rapport.replace(
    "|**CA TTC Magasin**|€|-|-|€|%||",
    f"|**CA TTC Magasin**|{fmt_eur(ls_ca)}|-|-|{fmt_eur(ls_ca_n1)}|{fmt_pct(ls_ca_evo)}|{statut(ls_ca_evo)}|"
)
rapport = rapport.replace(
    "|**Marge Magasin**|%|-|-|%|pts||",
    f"|**Marge Magasin**|{fmt_pct(ls_marge, sign=False)}|-|-|{fmt_pct(ls_marge_n1, sign=False)}|{fmt_pts(ls_marge_delta)}|{statut(ls_marge_delta)}|"
)
rapport = rapport.replace(
    "|**Panier Moyen LS**|€|-|-|€|%||",
    f"|**Panier Moyen LS**|{fmt_eur(ls_panier)}|-|-|{fmt_eur(ls_panier_n1)}|{fmt_pct(ls_panier_evo_n1)}|{statut(ls_panier_evo_n1)}|"
)

# — Section 3 Atelier —
rapport = rapport.replace(
    "|**CA TTC Atelier**|€|-|-|€|%||",
    f"|**CA TTC Atelier**|{fmt_eur(at_ca)}|-|-|{fmt_eur(at_ca_n1)}|{fmt_pct(at_ca_evo)}|{statut(at_ca_evo)}|"
)
rapport = rapport.replace(
    "|**Marge Atelier**|%|-|-|%|pts||",
    f"|**Marge Atelier**|{fmt_pct(at_marge, sign=False)}|-|-|{fmt_pct(at_marge_n1, sign=False)}|{fmt_pts(at_marge_delta)}|{statut(at_marge_delta)}|"
)
rapport = rapport.replace(
    "|**Nombre d'OR**|||-||%||",
    f"|**Nombre d'OR**|{at_nb_or}|-|-|{at_nb_or_n1}|{fmt_pct(at_nb_or_evo_n1)}|{statut(at_nb_or_evo_n1)}|"
)
rapport = rapport.replace(
    "|**Panier Moyen Atel.**|€|-|-|€|%||",
    f"|**Panier Moyen Atel.**|{fmt_eur(at_panier)}|-|-|{fmt_eur(at_panier_n1)}|{fmt_pct(at_panier_evo_n1)}|{statut(at_panier_evo_n1)}|"
)

with open(output_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 6 — EXPOSE KPIs FOR SECTION 1 NARRATIVE
# ─────────────────────────────────────────────
# The AI receives ONLY this dictionary — not the raw CSV.
# Use it to write the Section 1 strategic narrative in French.

kpis = {
    "mois":           f"{mois_str.capitalize()} {annee}",
    "ca_ttc":         int(cattc_n),
    "ca_obj":         ca_obj_ttc,
    "ca_ecart_pct":   ca_ecart,
    "ca_evo_n1_pct":  ca_evo,
    "marge_pct":      marge_n,
    "marge_obj_pct":  marge_obj,
    "marge_ecart_pts": marge_ecart,
    "marge_eur":      marge_eur_n,
    "marge_eur_obj":  marge_obj_eur,
    "marge_eur_ecart_pct": marge_eur_ecart,
    "ls_ca":          int(ls_ca),
    "ls_ca_evo_pct":  ls_ca_evo,
    "ls_marge_pct":   ls_marge,
    "at_ca":          int(at_ca),
    "at_ca_evo_pct":  at_ca_evo,
    "at_marge_pct":   at_marge,
    "at_nb_or":       at_nb_or,
    "rapport_path":   output_path,
}

print(f"✅ Rapport créé      : {output_path}")
print(f"✅ Mois              : {mois_str.capitalize()} {annee}")
print(f"✅ CA TTC            : {fmt_eur(cattc_n)} | Obj : {fmt_eur(ca_obj_ttc)} | Écart : {fmt_pct(ca_ecart)}")
print(f"✅ Marge %           : {fmt_pct(marge_n, sign=False)} | Obj : {fmt_pct(marge_obj, sign=False)} | Écart : {fmt_pts(marge_ecart)}")
print(f"✅ Marge €           : {fmt_eur(marge_eur_n)} | Obj : {fmt_eur(marge_obj_eur)} | Écart : {fmt_pct(marge_eur_ecart)}")
print(f"✅ LS CA             : {fmt_eur(ls_ca)} | Évo N-1 : {fmt_pct(ls_ca_evo)}")
print(f"✅ Atelier CA        : {fmt_eur(at_ca)} | Évo N-1 : {fmt_pct(at_ca_evo)}")
```

---

## Après exécution du script

Sections 2 et 3 remplies sans intervention de l'IA.

**L'IA rédige uniquement la Section 1** depuis le dict `kpis` ci-dessus :

> "Rédige la Section 1 (Bilan global) du rapport mensuel Feu Vert Annecy {kpis['mois']}.
> CA TTC : {kpis['ca_ttc']} € | Obj : {kpis['ca_obj']} € | Écart : {kpis['ca_ecart_pct']} %
> Marge % : {kpis['marge_pct']} % | Marge € : {kpis['marge_eur']} € | Écart obj : {kpis['marge_eur_ecart_pct']} %
> LS : {kpis['ls_ca']} € ({kpis['ls_ca_evo_pct']:+} % vs N-1) | Atelier : {kpis['at_ca']} € ({kpis['at_ca_evo_pct']:+} % vs N-1)
> Ton : senior business analyst, 3-4 phrases, en français."

Ensuite invoquer automatiquement `/ratios-mensuel`.
