---
description: familles trimestriel
---

ALWAYS use this skill when the user types "/familles-trimestriel", or when
/chiffre-trimestriel completes. Execute the Python script below in full. It parses
the comparatifCAv2_Famille CSV, fills the Familles table with str.replace per row,
then passes a compact summary to the AI for the "Points clés" section only.
Do NOT read the CSV yourself.
Other triggers: "remplis les familles trimestrielles", "analyse les familles du trimestre".

---

# Skill : Analyse par Familles — Rapport Trimestriel Feu Vert Annecy

## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité.**
Python remplit chaque ligne famille avec str.replace.
L'IA reçoit uniquement le dict `summary` pour rédiger les Points clés.

---

```python
import os, glob, csv, pathlib

# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}'")

def parse_pct(s):
    try:
        return float(s.replace(' %','').replace(' pts','').replace(',','.').replace('+','').strip())
    except:
        return None

def parse_int(s):
    try:
        return int(s.replace('\xa0','').replace(' ','').replace('€','').strip())
    except:
        return None

def statut(evo_str):
    val = parse_pct(evo_str)
    if val is None: return '⚪'
    if val > 0:     return '🟢'
    if val == 0:    return '🟡'
    return '🔴'

def marge_delta(marge_n_str, marge_n1_str):
    mn  = parse_pct(marge_n_str)
    mn1 = parse_pct(marge_n1_str)
    if mn is None or mn1 is None:
        return 'N/A'
    delta = round(mn - mn1, 1)
    sign  = '+' if delta >= 0 else ''
    return f'{sign}{delta:.1f} pts'.replace('.', ',')

# ─────────────────────────────────────────────
# STEP 1 — LOCATE FILES
# ─────────────────────────────────────────────

familles_folder = str(find_dir("Resources trimestrielles") / "Familles")
csv_files       = glob.glob(os.path.join(familles_folder, "comparatifCAv2_Famille*.csv"))

assert csv_files, "ERREUR : aucun fichier comparatifCAv2_Famille*.csv trouvé dans Resources trimestrielles/Familles/"
fichier_familles = csv_files[0]

rapport_dir = str(find_dir("trimestres"))
rapports    = glob.glob(os.path.join(rapport_dir, "rapport trimestriel *.md"))
assert rapports, "ERREUR : aucun rapport trimestriel trouvé. Lancer /chiffre-trimestriel d'abord."
rapport_path = sorted(rapports)[-1]   # most recent alphabetically

# ─────────────────────────────────────────────
# STEP 2 — PARSE CSV AND EXTRACT PER-FAMILY DATA
# ─────────────────────────────────────────────

with open(fichier_familles, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

data_lines    = lines[4:]
seen_families = {}
reader        = csv.reader(data_lines)

for row in reader:
    if len(row) < 27:
        continue
    fam = row[14].strip()
    if not fam or fam in seen_families:
        continue
    seen_families[fam] = {
        'ca_n':     row[15].strip(),   # CAHT_n_4
        'ca_n1':    row[16].strip(),   # CAHT_n_1_1
        'evo_ca':   row[18].strip(),   # textbox57
        'marge_n':  row[21].strip(),   # MARGE_n
        'marge_n1': row[22].strip(),   # MARGE_n_1
        'qty_n':    row[26].strip(),   # textbox63
    }

# ─────────────────────────────────────────────
# STEP 3 — FILL TABLE WITH str.replace PER ROW
# ─────────────────────────────────────────────
# Quarterly template placeholder per family (uses N/A, NOT empty cells):
# | **A-ENTRETIEN** | N/A | N/A | N/A | N/A | N/A | N/A | ⚪ |
# Replace with actual data when available, keep N/A if family absent.

TEMPLATE_FAMILIES = [
    'A-ENTRETIEN', 'B-ELECTRICITE', 'C-PIECES TECHNIQUES', 'D-OUTILLAGE',
    'E-EQUIPEMENT EXTERIEUR', 'F-EQUIPEMENT INTERIEUR', 'G-AUTO SON',
    'H-LUBRIFIANTS', 'I-PNEUMATIQUES', 'J-2 ROUES', 'U-SERVICES',
    'W-DIVERS', "X-TARIF MAIN D'OEUVRE",
]

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

filled  = []
missing = []

for fam in TEMPLATE_FAMILIES:
    # Exact placeholder in quarterly template
    old = f"| **{fam}** | N/A | N/A | N/A | N/A | N/A | N/A | ⚪ |"
    d   = seen_families.get(fam)

    if d:
        ca_n  = f"{d['ca_n']} €"  if d['ca_n']  else 'N/A'
        ca_n1 = f"{d['ca_n1']} €" if d['ca_n1'] else 'N/A'
        evo   = d['evo_ca']        or 'N/A'
        mg_n  = d['marge_n']       or 'N/A'
        mg_d  = marge_delta(d['marge_n'], d['marge_n1'])
        qty   = d['qty_n']         or 'N/A'
        st    = statut(d['evo_ca'])
        new   = f"| **{fam}** | {ca_n} | {ca_n1} | {evo} | {mg_n} | {mg_d} | {qty} | {st} |"
        rapport = rapport.replace(old, new)
        filled.append(fam)
    else:
        missing.append(fam)
        # Placeholder already reads N/A — leave unchanged

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 4 — BUILD COMPACT SUMMARY FOR AI
# ─────────────────────────────────────────────

families_data = []
for fam in TEMPLATE_FAMILIES:
    d = seen_families.get(fam)
    if not d:
        continue
    ca_n_val     = parse_int(d['ca_n'])
    evo_val      = parse_pct(d['evo_ca'])
    mn           = parse_pct(d['marge_n'])
    mn1          = parse_pct(d['marge_n1'])
    mg_delta_val = round(mn - mn1, 1) if mn is not None and mn1 is not None else None
    families_data.append({'fam': fam, 'ca_n': ca_n_val, 'evo': evo_val, 'mg_delta': mg_delta_val})

top_gainers = sorted([f for f in families_data if f['evo'] is not None],
                     key=lambda x: x['evo'], reverse=True)[:3]
top_losers  = sorted([f for f in families_data if f['evo'] is not None],
                     key=lambda x: x['evo'])[:3]
mg_alerts   = [f for f in families_data
               if f['mg_delta'] is not None and f['mg_delta'] < -5]

summary = {
    "rapport":         rapport_path,
    "familles_remplies": len(filled),
    "familles_absentes": missing,
    "top_croissance":  [{"famille": f['fam'], "evo": f['evo']} for f in top_gainers],
    "top_declin":      [{"famille": f['fam'], "evo": f['evo']} for f in top_losers],
    "alertes_marge":   [{"famille": f['fam'], "delta_pts": f['mg_delta']} for f in mg_alerts],
}

# ─────────────────────────────────────────────
# STEP 5 — CONFIRM
# ─────────────────────────────────────────────

print(f"✅ Tableau Familles mis à jour : {rapport_path}")
print(f"✅ Familles remplies : {len(filled)}/13")
if missing:
    print(f"⚠️  Absentes du CSV  : {', '.join(missing)}")
print()
print("Top croissance CA :")
for f in top_gainers:
    print(f"  {f['fam']:<30} {f['evo']:+.1f} %")
print("Top déclin CA :")
for f in top_losers:
    print(f"  {f['fam']:<30} {f['evo']:+.1f} %")
if mg_alerts:
    print("Alertes marge (dégradation > 5 pts) :")
    for f in mg_alerts:
        print(f"  {f['fam']:<30} {f['mg_delta']:+.1f} pts")
```

---

## Après exécution du script

Le tableau Familles est rempli sans intervention de l'IA.

**L'IA rédige uniquement les Points clés** depuis le dict `summary` :

> "Rédige 4-5 points clés de l'analyse trimestrielle par famille pour Feu Vert Annecy.
> Top croissance : {summary['top_croissance']}
> Top déclin : {summary['top_declin']}
> Alertes marge : {summary['alertes_marge']}
> Perspective trimestrielle (tendances 3 mois, non ponctuelles).
> Ton : factuel, orienté management, en français, puces courtes."

Insérer le résultat dans la section `### Points clés de l'analyse par famille`
en remplaçant les lignes `* [Point clé...]` existantes.
