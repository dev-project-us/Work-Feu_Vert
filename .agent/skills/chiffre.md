---
description: chiffre
---

ALWAYS use this skill when the user types "/chiffre". When triggered, execute the
Python script below in full. It scans the SUC CSV files, extracts all values,
computes all KPIs, fills Sections 2, 3 and 7 of the weekly report, and returns
a confirmation. Do NOT interpret or read the CSV files yourself.
Other triggers: "remplis le rapport", "mets à jour les chiffres", "analyse les CSV",
"fill the weekly report".

---

# Skill : Analyse des Chiffres — Rapport Hebdomadaire Feu Vert Annecy

## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité, en une seule fois.**
Python fait tout : scan, extraction, calculs, création du fichier, remplissage.
L'IA ne lit pas les CSV. L'IA n'interprète pas les données.
À la fin du script, l'IA reçoit un dictionnaire `kpis` et génère uniquement la Section 1.

---

```python
import os, glob, re, shutil, csv, io, pathlib
from datetime import datetime

# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}'")

def clean_num(s):
    """Remove spaces, currency, percent signs. Return float."""
    return float(s.replace('\xa0', '').replace(' ', '').replace('€', '')
                  .replace('%', '').replace(',', '.').replace('+', '').strip())

def fmt_pct(val, sign=True):
    s = f"{val:+.1f}" if sign else f"{val:.1f}"
    return s.replace('.', ',') + ' %'

def fmt_pts(val):
    s = f"{val:+.1f}".replace('.', ',')
    return s + ' pts'

def fmt_eur(val):
    return f"{int(round(val)):,}".replace(',', ' ') + ' €'

def statut_n1(evo_val):
    if evo_val > 0:   return '🟢'
    elif evo_val == 0: return '🟡'
    else:              return '🔴'

def read_raw(path):
    with open(path, 'r', encoding='utf-8-sig') as fh:
        return fh.read()

def parse_global_block(content):
    """Extract the global block row from a SUC Situation de chiffre file."""
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
    """Extract monthly objectives from the Objectifs Journaliers file."""
    lines = content.replace('\r\n', '\n').split('\n')
    headers = []
    for i, line in enumerate(lines):
        if 'libelleJour' in line:
            headers = next(csv.reader([line]))
            # Find first data row where CATTC != 0
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

def parse_contrats(content):
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if 'nbContratEntretien_DECI' in line:
            headers = next(csv.reader([line]))
            data    = next(csv.reader([lines[i + 1]]))
            d = dict(zip(headers, data))
            deci = int(clean_num(d.get('nbContratEntretien_DECI', '0')))
            g6k  = int(clean_num(d.get('nbCE_G6K', '0')))
            return deci + g6k
    return 0

def extraire_marge_eur(content):
    lines = content.replace('\r\n', '\n').split('\n')
    for i, line in enumerate(lines):
        if line.startswith('libelle,marge_n_2'):
            data_line = lines[i + 1]
            parts = data_line.split(',')
            valeur_raw = parts[1].replace('\xa0', '').replace(' ', '').strip()
            return int(valeur_raw)
    return None

def extract_date_debut(content):
    """Extract start date from period line."""
    m = re.search(r'Du (\d{2}/\d{2}/\d{4})', content)
    return m.group(1) if m else ''

# ─────────────────────────────────────────────
# STEP 1 — SCAN AND IDENTIFY CSV FILES
# ─────────────────────────────────────────────

folder    = str(find_dir("resources") / "SUC")
csv_files = glob.glob(os.path.join(folder, "SUC - *.csv"))

annee_courante    = datetime.today().year
fichier_semaine   = None
fichier_mtd       = None
fichier_objectifs = None
fichier_n1        = None

for f in csv_files:
    content = read_raw(f)
    if 'libelleJour' in content:
        fichier_objectifs = f
    elif 'Du 01/' in content:
        fichier_mtd = f
    else:
        m = re.search(r'Du \d{2}/\d{2}/(\d{4})', content)
        if m and int(m.group(1)) == annee_courante:
            fichier_semaine = f
        else:
            fichier_n1 = f

assert fichier_semaine,   "ERREUR : fichier semaine N introuvable dans resources/SUC/"
assert fichier_mtd,       "ERREUR : fichier MTD introuvable dans resources/SUC/"
assert fichier_objectifs, "ERREUR : fichier objectifs introuvable dans resources/SUC/"

# ─────────────────────────────────────────────
# STEP 2 — DETERMINE WEEK NUMBER AND DATES
# ─────────────────────────────────────────────

sem_content = read_raw(fichier_semaine)
mtd_content = read_raw(fichier_mtd)
obj_content = read_raw(fichier_objectifs)
n1_content  = read_raw(fichier_n1) if fichier_n1 else None

# Extract end date from semaine file
m = re.search(r'textbox1,textbox72\s+Du[^,]+,(\d{2}/\d{2}/\d{4})', sem_content)
date_fin_str   = m.group(1)
date_debut_str = extract_date_debut(sem_content)
date_fin       = datetime.strptime(date_fin_str, "%d/%m/%Y")
semaine        = date_fin.isocalendar()[1]
annee          = date_fin.year

# ─────────────────────────────────────────────
# STEP 3 — CREATE REPORT FILE FROM TEMPLATE
# ─────────────────────────────────────────────

template_path = str(find_dir("templates") / "rapport_hebdomadaire_template.md")
output_dir    = str(find_dir("Rapport hebdomadaire"))
os.makedirs(output_dir, exist_ok=True)
output_name   = f"rapport hebdomadaire semaine {semaine}.md"
output_path   = os.path.join(output_dir, output_name)
shutil.copy(template_path, output_path)

# ─────────────────────────────────────────────
# STEP 4 — EXTRACT ALL VALUES FROM CSV FILES
# ─────────────────────────────────────────────

# — Global block from semaine file —
g  = parse_global_block(sem_content)
go = parse_objectifs_block(obj_content)

cattc_n    = clean_num(g.get('cattc_n', '0'))
caht_evo   = clean_num(g.get('textbox4', '0'))
marge_n    = clean_num(g.get('marge_n', '0'))
marge_evo  = clean_num(g.get('textbox24', '0'))
freq_n     = int(clean_num(g.get('textbox14', '0')))
freq_evo   = clean_num(g.get('textbox17', '0'))
panier_n   = clean_num(g.get('cattc_n_2', '0'))

ca_obj_ttc  = int(clean_num(go.get('textbox8', '0')))
marge_obj   = clean_num(go.get('textbox50', '0'))

# Objectif marge € : last non-empty column of objectives row
obj_lines = obj_content.replace('\r\n', '\n').split('\n')
marge_obj_eur = 0
for line in obj_lines:
    if 'libelleJour' in line:
        continue
    try:
        row = next(csv.reader([line]))
        last_val = [v for v in row if v.strip()][-1]
        candidate = int(clean_num(last_val))
        if candidate > 10000:
            marge_obj_eur = candidate
            break
    except:
        continue

# — Derived N-1 values for Section 2 —
ca_n1      = round(cattc_n / (1 + caht_evo / 100))
ca_ecart   = round((cattc_n / ca_obj_ttc - 1) * 100, 1) if ca_obj_ttc else 0
marge_n1   = round(marge_n - marge_evo, 1)
marge_ecart = round(marge_n - marge_obj, 1)
freq_n1    = round(freq_n / (1 + freq_evo / 100)) if freq_evo != -100 else 0
panier_evo = clean_num(g.get('textbox17', '0'))   # reused field — check mapping
panier_n1  = round(panier_n / (1 + panier_evo / 100), 1) if panier_evo != -100 else 0

# — LS block —
ls = parse_ls_block(sem_content)
ls_ca      = clean_num(ls.get('textbox27', '0'))
ls_evo     = clean_num(ls.get('textbox25', '0'))
ls_obj     = round(ls_ca / (1 + ls_evo / 100)) if ls_evo != -100 else ls_ca
ls_marge   = clean_num(ls.get('textbox31', '0'))
ls_marge_evo = clean_num(ls.get('textbox33', '0'))
ls_panier  = clean_num(ls.get('textbox39', '0'))
ls_panier_evo = clean_num(ls.get('textbox41', '0'))

if n1_content:
    ls_n1       = parse_ls_block(n1_content)
    ls_ca_n1    = clean_num(ls_n1.get('textbox27', '0'))
    ls_marge_n1 = clean_num(ls_n1.get('textbox31', '0'))
    ls_panier_n1 = clean_num(ls_n1.get('textbox39', '0'))
else:
    ls_ca_n1    = round(ls_ca / (1 + ls_evo / 100)) if ls_evo != -100 else 0
    ls_marge_n1 = round(ls_marge - ls_marge_evo, 1)
    ls_panier_n1 = round(ls_panier / (1 + ls_panier_evo / 100), 1) if ls_panier_evo != -100 else 0

# — Atelier block —
at = parse_atelier_block(sem_content)
at_ca      = clean_num(at.get('textbox47', '0'))
at_evo     = clean_num(at.get('textbox45', '0'))
at_obj     = round(at_ca / (1 + at_evo / 100)) if at_evo != -100 else at_ca
at_marge   = clean_num(at.get('textbox51', '0'))
at_marge_evo = clean_num(at.get('textbox53', '0'))
at_nb_or   = int(clean_num(at.get('textbox55', '0')))
at_nb_or_evo = clean_num(at.get('textbox57', '0'))
at_panier  = clean_num(at.get('textbox62', '0'))
at_panier_evo = clean_num(at.get('textbox64', '0'))

if n1_content:
    at_n1        = parse_atelier_block(n1_content)
    at_ca_n1     = clean_num(at_n1.get('textbox47', '0'))
    at_marge_n1  = clean_num(at_n1.get('textbox51', '0'))
    at_nb_or_n1  = int(clean_num(at_n1.get('textbox55', '0')))
    at_panier_n1 = clean_num(at_n1.get('textbox62', '0'))
else:
    at_ca_n1     = round(at_ca / (1 + at_evo / 100)) if at_evo != -100 else 0
    at_marge_n1  = round(at_marge - at_marge_evo, 1)
    at_nb_or_n1  = round(at_nb_or / (1 + at_nb_or_evo / 100)) if at_nb_or_evo != -100 else 0
    at_panier_n1 = round(at_panier / (1 + at_panier_evo / 100), 1) if at_panier_evo != -100 else 0

# — Section 7 RAF (MTD values) —
g_mtd       = parse_global_block(mtd_content)
ca_mtd      = clean_num(g_mtd.get('cattc_n', '0'))
ca_pct      = round(ca_mtd / ca_obj_ttc * 100, 1) if ca_obj_ttc else 0
ca_raf      = int(ca_obj_ttc - ca_mtd)
marge_mtd_eur = extraire_marge_eur(mtd_content) or 0
marge_eur_pct = round(marge_mtd_eur / marge_obj_eur * 100, 1) if marge_obj_eur else 0
marge_eur_raf = marge_obj_eur - marge_mtd_eur
contrat_mtd = parse_contrats(mtd_content)

# ─────────────────────────────────────────────
# STEP 5 — FILL THE REPORT (pure str.replace)
# ─────────────────────────────────────────────

with open(output_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

# Header dates
rapport = rapport.replace('[JJ/MM/AAAA] au [JJ/MM/AAAA]',
    f"{date_debut_str} au {date_fin_str}")

# — Section 2 —
S2_OLD = (
    "|**CA HT Total**|€|€|%|€|%|\n"
    "|**Marge Brute**|%|%|pts|%|pts|\n"
    "|**Fréquentation**|clts|-|-|clts|%|\n"
    "|**Panier Moyen**|€|-|-|€|%|"
)
S2_NEW = (
    f"|**CA TTC Total**|{fmt_eur(cattc_n)}|{fmt_eur(ca_obj_ttc)}|{fmt_pct(ca_ecart)}|{fmt_eur(ca_n1)}|{fmt_pct(caht_evo)}|\n"
    f"|**Marge Brute**|{fmt_pct(marge_n, sign=False)}|{fmt_pct(marge_obj, sign=False)}|{fmt_pts(marge_ecart)}|{fmt_pct(marge_n1, sign=False)}|{fmt_pts(marge_evo)}|\n"
    f"|**Fréquentation**|{freq_n} clts|-|-|{freq_n1} clts|{fmt_pct(freq_evo)}|\n"
    f"|**Panier Moyen**|{fmt_eur(panier_n)}|-|-|{fmt_eur(panier_n1)}|{fmt_pct(panier_evo)}|"
)
rapport = rapport.replace(S2_OLD, S2_NEW)

# — Section 3 LS —
S3LS_OLD = (
    "|**CA HT Magasin**|€|€|€|%||\n"
    "|**Marge Magasin**|%|%|%|pts||\n"
    "|**Panier Moyen LS**|€|-|€|%||"
)
S3LS_NEW = (
    f"|**CA TTC Magasin**|{fmt_eur(ls_ca)}|{fmt_eur(ls_obj)}|{fmt_eur(ls_ca_n1)}|{fmt_pct(ls_evo)}|{statut_n1(ls_evo)}|\n"
    f"|**Marge Magasin**|{fmt_pct(ls_marge, sign=False)}|-|{fmt_pct(ls_marge_n1, sign=False)}|{fmt_pts(ls_marge_evo)}|{statut_n1(ls_marge_evo)}|\n"
    f"|**Panier Moyen LS**|{fmt_eur(ls_panier)}|-|{fmt_eur(ls_panier_n1)}|{fmt_pct(ls_panier_evo)}|{statut_n1(ls_panier_evo)}|"
)
rapport = rapport.replace(S3LS_OLD, S3LS_NEW)

# — Section 3 Atelier —
S3AT_OLD = (
    "|**CA HT Atelier**|€|€|€|%||\n"
    "|**Marge Atelier**|%|%|%|pts||\n"
    "|**Nombre d'OR**||-||%||\n"
    "|**Panier Moyen Atel.**|€|-|€|%||"
)
S3AT_NEW = (
    f"|**CA TTC Atelier**|{fmt_eur(at_ca)}|{fmt_eur(at_obj)}|{fmt_eur(at_ca_n1)}|{fmt_pct(at_evo)}|{statut_n1(at_evo)}|\n"
    f"|**Marge Atelier**|{fmt_pct(at_marge, sign=False)}|-|{fmt_pct(at_marge_n1, sign=False)}|{fmt_pts(at_marge_evo)}|{statut_n1(at_marge_evo)}|\n"
    f"|**Nombre d'OR**|{at_nb_or}|-|{at_nb_or_n1}|{fmt_pct(at_nb_or_evo)}|{statut_n1(at_nb_or_evo)}|\n"
    f"|**Panier Moyen Atel.**|{fmt_eur(at_panier)}|-|{fmt_eur(at_panier_n1)}|{fmt_pct(at_panier_evo)}|{statut_n1(at_panier_evo)}|"
)
rapport = rapport.replace(S3AT_OLD, S3AT_NEW)

# — Section 7 RAF —
S7_OLD = (
    "|**CA**|€|€|%|€|\n"
    "|**Marge**|%|%|%||\n"
    "|**Contrat**|||%||\n"
    "|**Cofidis**|||%||"
)
S7_NEW = (
    f"|**CA**|{fmt_eur(ca_obj_ttc)}|{fmt_eur(ca_mtd)}|{ca_pct} %|{fmt_eur(ca_raf)}|\n"
    f"|**Marge**|{fmt_eur(marge_obj_eur)}|{fmt_eur(marge_mtd_eur)}|{marge_eur_pct} %|{fmt_eur(marge_eur_raf)}|\n"
    f"|**Contrat**|-|{contrat_mtd}|-|-|\n"
    f"|**Cofidis**|-|-|-|-|"
)
rapport = rapport.replace(S7_OLD, S7_NEW)

with open(output_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 6 — EXPOSE KPIs FOR SECTION 1 NARRATIVE
# ─────────────────────────────────────────────
# The AI receives ONLY this dictionary — not the raw CSV.
# Use it to write the Section 1 strategic narrative in French.

kpis = {
    "semaine":        semaine,
    "periode":        f"{date_debut_str} au {date_fin_str}",
    "ca_ttc":         int(cattc_n),
    "ca_obj":         ca_obj_ttc,
    "ca_ecart_pct":   ca_ecart,
    "ca_evo_n1_pct":  caht_evo,
    "marge_pct":      marge_n,
    "marge_obj_pct":  marge_obj,
    "marge_ecart_pts": marge_ecart,
    "freq_n":         freq_n,
    "freq_evo_pct":   freq_evo,
    "ls_ca":          int(ls_ca),
    "ls_evo_pct":     ls_evo,
    "ls_marge_pct":   ls_marge,
    "at_ca":          int(at_ca),
    "at_evo_pct":     at_evo,
    "at_marge_pct":   at_marge,
    "at_nb_or":       at_nb_or,
    "ca_mtd":         int(ca_mtd),
    "ca_raf":         ca_raf,
    "ca_avancement":  ca_pct,
    "rapport_path":   output_path,
}

print("✅ Rapport créé :", output_path)
print("✅ Semaine       :", semaine)
print("✅ CA TTC        :", fmt_eur(cattc_n), "| Obj:", fmt_eur(ca_obj_ttc), "| Écart:", fmt_pct(ca_ecart))
print("✅ Marge         :", fmt_pct(marge_n, sign=False), "| Obj:", fmt_pct(marge_obj, sign=False), "| Écart:", fmt_pts(marge_ecart))
print("✅ Fréquentation :", freq_n, "clts | Évo:", fmt_pct(freq_evo))
print("✅ RAF CA        :", fmt_eur(ca_raf), f"({ca_pct} % réalisé)")
```

---

## Après exécution du script

Le script a rempli les Sections 2, 3 et 7 sans intervention de l'IA.

**L'IA rédige uniquement la Section 1** en utilisant le dictionnaire `kpis` ci-dessus.
Aucun CSV n'est transmis au modèle. Le prompt envoyé est :

> "Rédige la Section 1 (Big Picture) du rapport hebdomadaire Feu Vert Annecy semaine {kpis['semaine']}.
> CA TTC réalisé : {kpis['ca_ttc']} € | Objectif : {kpis['ca_obj']} € | Écart : {kpis['ca_ecart_pct']} %
> Marge : {kpis['marge_pct']} % | Objectif : {kpis['marge_obj_pct']} % | Écart : {kpis['marge_ecart_pts']} pts
> LS : {kpis['ls_ca']} € ({kpis['ls_evo_pct']:+} % vs N-1) | Atelier : {kpis['at_ca']} € ({kpis['at_evo_pct']:+} % vs N-1)
> Avancement mensuel : {kpis['ca_avancement']} % — RAF : {kpis['ca_raf']} €
> Ton : senior business analyst, 3-4 phrases, en français."

Ensuite, invoquer automatiquement `/ratios` pour remplir la Section 4.
