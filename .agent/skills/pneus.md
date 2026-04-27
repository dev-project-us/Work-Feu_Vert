---
description: pneus hebdomadaire
---

ALWAYS use this skill when the user types "/pneus" on a weekly report context. Execute the Python script
below in full. It parses the Pneus CSV from resources/Pneus/, fills the Analyse Pneus tables
(season summary + ÉTÉ brand detail) with str.replace per row, then passes a compact summary to the AI
for the "Points clés" section only. Do NOT read the CSV yourself.
Other triggers: "remplis les pneus hebdo", "analyse les pneus semaine", "mets à jour le tableau pneus hebdo".

---

# Skill : Analyse Pneus — Rapport Hebdomadaire Feu Vert Annecy

## Instruction d'exécution

**Exécuter le script Python ci-dessous dans son intégralité.**
Python remplit les tableaux Pneus avec str.replace par ligne.
L'IA reçoit uniquement le dict `summary` pour rédiger les Points clés.

---

```python
import os, glob, csv, pathlib, datetime

# ─────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────

def find_dir(name):
    for p in [pathlib.Path.cwd()] + list(pathlib.Path.cwd().parents):
        candidate = p / name
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(f"Cannot find directory '{name}'")

def clean(s):
    return s.strip() if s.strip() and s.strip() not in ('-', '') else 'N/A'

def parse_pct(s):
    try:
        return float(s.replace(' %','').replace('%','').replace(',','.').replace('+','').strip())
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

def fmt_eur(val):
    return f"{val} €" if val != 'N/A' else 'N/A'

# ─────────────────────────────────────────────
# STEP 1 — LOCATE FILES
# ─────────────────────────────────────────────

pneus_folder = str(find_dir("resources") / "Pneus")
csv_files    = glob.glob(os.path.join(pneus_folder, "Pneus*.csv"))
assert csv_files, "ERREUR : aucun fichier Pneus*.csv trouvé dans resources/Pneus/"
fichier_pneus = csv_files[0]

rapport_dir = str(find_dir("Rapport hebdomadaire"))
rapports    = glob.glob(os.path.join(rapport_dir, "rapport hebdomadaire semaine *.md"))
assert rapports, "ERREUR : aucun rapport hebdomadaire trouvé. Lancer /chiffre d'abord."

# ─────────────────────────────────────────────
# STEP 2 — PARSE CSV
# ─────────────────────────────────────────────
# The CSV has 4 blocks separated by blank lines, each representing a tire season type:
#   Block 1 (header marque4,  lines 4-18):  ÉTÉ (Summer)
#   Block 2 (header marque,   lines 20-32): 4 SAISONS (All Season)
#   Block 3 (header marque2,  lines 34-47): HIVER (Winter)
#   Block 4 (header marque3,  lines 49-57): other (not displayed)
#
# Column positions (same across all blocks):
#   [0]  brand name
#   [3]  qty realized (N)
#   [4]  market share % (N)
#   [8]  CA realized € (N)
#   [9]  CA evo vs N-1 %
#   [14] marge realized € (N)
#   [15] marge % (N)
#   [16] category (PREMIUM / MEDIUM / BUDGET)
#   [19] category qty total
#   [20] category PdM %
#   [24] category CA total €
#   [25] category CA evo %
#   [30] category marge total €
#   [31] category marge %

with open(fichier_pneus, 'r', encoding='utf-8-sig') as f:
    content = f.read()

lines = content.split('\n')

# Extract period and week number from line 2
meta_row   = list(csv.reader([lines[1]]))[0]
period_str = meta_row[1].strip()   # e.g. "20/04/2026 - 26/04/2026"
end_date   = datetime.datetime.strptime(period_str.split(' - ')[1].strip(), '%d/%m/%Y').date()
week_num   = end_date.isocalendar()[1]

# Find matching rapport
rapport_path = None
for r in rapports:
    if f"semaine {week_num}" in os.path.basename(r):
        rapport_path = r
        break
if rapport_path is None:
    rapport_path = sorted(rapports)[-1]
    print(f"⚠️  Rapport semaine {week_num} non trouvé — utilisation de : {os.path.basename(rapport_path)}")

def find_block_range(lines, col0_value):
    """Return (header_idx, data_start, data_end) for a block whose first CSV column equals col0_value."""
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            row = list(csv.reader([line]))[0]
        except Exception:
            continue
        if row and row[0].strip() == col0_value:
            start = i + 1
            end   = start
            for j in range(start, len(lines)):
                if not lines[j].strip():
                    end = j
                    break
            else:
                end = len(lines)
            return i, start, end
    return None, None, None

def parse_block(lines, start, end):
    """Parse one block: return (brand_data, cat_totals) dicts."""
    brand_data = {}   # (cat, brand) -> metrics
    cat_totals = {}   # cat -> metrics
    for line in lines[start:end]:
        if not line.strip():
            continue
        row = list(csv.reader([line]))[0]
        if len(row) < 20:
            continue
        brand = row[0].strip()
        cat   = row[16].strip()
        if not brand or not cat:
            continue
        brand_data[(cat, brand)] = {
            'qty':       clean(row[3]),
            'pdm':       clean(row[4]),
            'ca':        clean(row[8]),
            'ca_evo':    clean(row[9]),
            'marge_eur': clean(row[14]),
            'marge_pct': clean(row[15]),
        }
        if cat not in cat_totals:
            cat_totals[cat] = {
                'qty':       clean(row[19]),
                'pdm':       clean(row[20]),
                'ca':        clean(row[24]),
                'ca_evo':    clean(row[25]),
                'marge_eur': clean(row[30]),
                'marge_pct': clean(row[31]),
            }
    return brand_data, cat_totals

# Parse the 3 season blocks (col0 = the block's first column header value)
_, s1, e1 = find_block_range(lines, 'marque4')
_, s2, e2 = find_block_range(lines, 'marque')
_, s3, e3 = find_block_range(lines, 'marque2')

brand_data_ete,   cat_totals_ete   = parse_block(lines, s1, e1) if s1 else ({}, {})
brand_data_4s,    cat_totals_4s    = parse_block(lines, s2, e2) if s2 else ({}, {})
brand_data_hiver, cat_totals_hiver = parse_block(lines, s3, e3) if s3 else ({}, {})

# Compute grand total (sum across all 3 seasons)
def sum_seasons(cat_totals_list, cats):
    total_qty = total_ca = total_marge = 0
    all_evo = []
    for ct_dict in cat_totals_list:
        for cat in cats:
            ct = ct_dict.get(cat, {})
            total_qty   += parse_int(ct.get('qty', 'N/A')) or 0
            total_ca    += parse_int(ct.get('ca', 'N/A'))  or 0
            total_marge += parse_int(ct.get('marge_eur', 'N/A')) or 0
            evo = parse_pct(ct.get('ca_evo', 'N/A'))
            if evo is not None:
                all_evo.append(evo)
    avg_evo = round(sum(all_evo)/len(all_evo), 1) if all_evo else None
    return total_qty, total_ca, total_marge, avg_evo

CATS = ['PREMIUM', 'MEDIUM', 'BUDGET']
g_qty, g_ca, g_marge, g_evo = sum_seasons(
    [cat_totals_ete, cat_totals_4s, cat_totals_hiver], CATS
)
g_marge_pct = round(g_marge / g_ca * 100, 2) if g_ca else None

# ─────────────────────────────────────────────
# STEP 3 — FILL TABLES WITH str.replace
# ─────────────────────────────────────────────

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

SEASON_BLOCKS = [
    ('ÉTÉ',       cat_totals_ete),
    ('4 SAISONS', cat_totals_4s),
    ('HIVER',     cat_totals_hiver),
]

# --- Season summary table ---
for saison, cat_totals in SEASON_BLOCKS:
    # Per-category rows: placeholder "| **ÉTÉ** | PREMIUM | | | | | | | |"
    for cat in CATS:
        old = f"| **{saison}** | {cat} | | | | | | | |"
        ct  = cat_totals.get(cat)
        if ct:
            st  = statut(ct['ca_evo'])
            new = f"| **{saison}** | {cat} | {ct['qty']} | {ct['pdm']} | {fmt_eur(ct['ca'])} | {ct['ca_evo']} | {fmt_eur(ct['marge_eur'])} | {ct['marge_pct']} | {st} |"
        else:
            new = f"| **{saison}** | {cat} | N/A | N/A | N/A | N/A | N/A | N/A | ⚪ |"
        rapport = rapport.replace(old, new)

    # Season total row: compute from category subtotals
    s_qty = s_ca = s_marge = 0
    s_evo_list = []
    for cat in CATS:
        ct = cat_totals.get(cat, {})
        s_qty   += parse_int(ct.get('qty', 'N/A'))       or 0
        s_ca    += parse_int(ct.get('ca', 'N/A'))         or 0
        s_marge += parse_int(ct.get('marge_eur', 'N/A')) or 0
        evo = parse_pct(ct.get('ca_evo', 'N/A'))
        if evo is not None:
            s_evo_list.append(evo)

    s_evo_avg   = round(sum(s_evo_list)/len(s_evo_list), 1) if s_evo_list else None
    s_marge_pct = round(s_marge / s_ca * 100, 2) if s_ca else None
    s_evo_str   = f"{'+' if s_evo_avg and s_evo_avg >= 0 else ''}{s_evo_avg} %" if s_evo_avg is not None else 'N/A'
    s_marge_pct_str = f"{s_marge_pct} %" if s_marge_pct is not None else 'N/A'
    st_tot = statut(s_evo_str)

    old_tot = f"| *Total {saison}* | | | | | | | | |"
    new_tot = f"| *Total {saison}* | | {s_qty} | — | {s_ca} € | {s_evo_str} | {s_marge} € | {s_marge_pct_str} | {st_tot} |"
    rapport = rapport.replace(old_tot, new_tot)

# Grand total row
g_evo_str   = f"{'+' if g_evo and g_evo >= 0 else ''}{g_evo} %" if g_evo is not None else 'N/A'
g_marge_pct_str = f"{round(g_marge_pct, 2)} %" if g_marge_pct is not None else 'N/A'
st_grand = statut(g_evo_str)
old_grand = "| **TOTAL PNEUS** | | | | | | | | |"
new_grand = f"| **TOTAL PNEUS** | | {g_qty} | — | {g_ca} € | {g_evo_str} | {g_marge} € | {g_marge_pct_str} | {st_grand} |"
rapport = rapport.replace(old_grand, new_grand)

# --- ÉTÉ brand detail table ---
TEMPLATE_BRANDS = {
    'PREMIUM': ['AUTRE', 'CONTINENTAL', 'GOODYEAR', 'MICHELIN', 'PIRELLI'],
    'MEDIUM':  ['AUTRE', 'FEU VERT', 'HANKOOK', 'KUMHO', 'NEXEN', 'NOKIAN'],
    'BUDGET':  ['AUTRE', 'ROVELO', 'TRACMAX'],
}

filled  = []
missing = []

for cat, brands in TEMPLATE_BRANDS.items():
    for brand in brands:
        old = f"| **{cat}** | {brand} | | | | | | | |"
        d   = brand_data_ete.get((cat, brand))
        if d:
            st       = statut(d['ca_evo'])
            ca_fmt   = fmt_eur(d['ca'])
            mg_fmt   = fmt_eur(d['marge_eur'])
            new = f"| **{cat}** | {brand} | {d['qty']} | {d['pdm']} | {ca_fmt} | {d['ca_evo']} | {mg_fmt} | {d['marge_pct']} | {st} |"
            rapport = rapport.replace(old, new)
            filled.append(f"{cat}/{brand}")
        else:
            new = f"| **{cat}** | {brand} | N/A | N/A | N/A | N/A | N/A | N/A | ⚪ |"
            rapport = rapport.replace(old, new)
            missing.append(f"{cat}/{brand}")

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# ─────────────────────────────────────────────
# STEP 4 — BUILD COMPACT SUMMARY FOR AI
# ─────────────────────────────────────────────

season_summary = {}
for saison, ct_dict in [('ÉTÉ', cat_totals_ete), ('4 SAISONS', cat_totals_4s), ('HIVER', cat_totals_hiver)]:
    sq = sm = sc = 0
    for cat in CATS:
        ct = ct_dict.get(cat, {})
        sq += parse_int(ct.get('qty', 'N/A'))       or 0
        sc += parse_int(ct.get('ca', 'N/A'))         or 0
        sm += parse_int(ct.get('marge_eur', 'N/A')) or 0
    sp = round(sm/sc*100, 1) if sc else None
    season_summary[saison] = {'qty': sq, 'ca': sc, 'marge_pct': sp}

brands_list = [
    {'cat': c, 'brand': b, 'ca': parse_int(d['ca']), 'evo': parse_pct(d['ca_evo']), 'marge_pct': parse_pct(d['marge_pct'])}
    for (c, b), d in brand_data_ete.items()
]
top_gainers = sorted([b for b in brands_list if b['evo'] and b['ca'] and b['ca'] > 0],
                     key=lambda x: x['evo'], reverse=True)[:3]
top_losers  = sorted([b for b in brands_list if b['evo'] and b['evo'] < 0], key=lambda x: x['evo'])[:3]
mg_alerts   = [b for b in brands_list if b['marge_pct'] and b['marge_pct'] < 10 and b['ca'] and b['ca'] > 0]

summary = {
    "rapport":        rapport_path,
    "semaine":        week_num,
    "periode":        period_str,
    "total_qty":      g_qty,
    "total_ca":       g_ca,
    "total_marge_pct": g_marge_pct_str,
    "saisons":        season_summary,
    "top_croissance": [{"cat": b['cat'], "brand": b['brand'], "evo": b['evo']} for b in top_gainers],
    "top_declin":     [{"cat": b['cat'], "brand": b['brand'], "evo": b['evo']} for b in top_losers],
    "alertes_marge":  [{"cat": b['cat'], "brand": b['brand'], "marge_pct": b['marge_pct']} for b in mg_alerts],
}

# ─────────────────────────────────────────────
# STEP 5 — CONFIRM
# ─────────────────────────────────────────────

print(f"✅ Tableaux Pneus mis à jour : {rapport_path}")
print(f"✅ Semaine {week_num} — période : {period_str}")
print(f"✅ Grand total : {g_qty} unités | CA {g_ca} € | Marge {g_marge_pct_str}")
print()
for saison, v in season_summary.items():
    print(f"  [{saison}] qty={v['qty']} CA={v['ca']} € marge={v['marge_pct']} %")
print()
if missing:
    print(f"⚠️  Marques absentes du CSV ÉTÉ : {', '.join(missing)}")
```

---

## Après exécution du script

Les tableaux Pneus sont remplis sans intervention de l'IA.

**L'IA rédige uniquement les Points clés** depuis le dict `summary` ci-dessus :

> "Rédige 4 points clés de l'analyse pneus pour le rapport hebdomadaire Feu Vert Annecy.
> Total pneus semaine : {summary['total_qty']} unités, CA {summary['total_ca']} €, marge {summary['total_marge_pct']}.
> Répartition par saison : {summary['saisons']}
> Top croissance marque ÉTÉ : {summary['top_croissance']}
> Top déclin marque ÉTÉ : {summary['top_declin']}
> Alertes marge (< 10 %) : {summary['alertes_marge']}
> Ton : factuel, orienté management, en français, puces courtes."

Insérer le résultat dans la section `### Points clés de l'analyse pneus`
en remplaçant les lignes `* [Point clé...]` existantes.
