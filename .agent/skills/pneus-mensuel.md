---
description: pneus mensuel
---

ALWAYS use this skill when the user types "/pneus-mensuel" on a monthly report context. Execute the Python script
below in full. It parses the Pneus CSV from Resources mensuelles/pneus/, fills the Analyse Pneus tables
(season summary + ÉTÉ brand detail) with str.replace per row, then passes a compact summary to the AI
for the "Points clés" section only. Do NOT read the CSV yourself.
Other triggers: "remplis les pneus mensuel", "analyse les pneus mois", "mets à jour le tableau pneus mensuel".

---

```python
import os, glob, csv, pathlib, datetime

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

MOIS_FR = {
    1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
    5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
    9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
}

# STEP 1 — LOCATE FILES

pneus_folder = str(find_dir("resources") / "Resources mensuelles" / "pneus")
csv_files    = glob.glob(os.path.join(pneus_folder, "Pneus*.csv"))
assert csv_files, "ERREUR : aucun fichier Pneus*.csv trouvé dans Resources mensuelles/pneus/"
fichier_pneus = csv_files[0]

rapport_dir = str(find_dir("Rapport mensuel"))
rapports    = glob.glob(os.path.join(rapport_dir, "rapport mensuel *.md"))
assert rapports, "ERREUR : aucun rapport mensuel trouvé. Lancer /chiffre-mensuel d'abord."

# STEP 2 — PARSE CSV
# Blocks: marque4=ÉTÉ, marque=4SAISONS, marque2=HIVER; col[0]=brand, [3]=qty, [4]=pdm%,
# [8]=CA€, [9]=CA_evo%, [14]=marge€, [15]=marge%, [16]=cat, [19]=cat_qty,
# [20]=cat_pdm, [24]=cat_CA, [25]=cat_CA_evo, [30]=cat_marge€, [31]=cat_marge%

with open(fichier_pneus, 'r', encoding='utf-8-sig') as f:
    content = f.read()

lines = content.split('\n')

meta_row   = list(csv.reader([lines[1]]))[0]
period_str = meta_row[1].strip()
end_date   = datetime.datetime.strptime(period_str.split(' - ')[1].strip(), '%d/%m/%Y').date()
mois_num   = end_date.month
annee      = end_date.year
mois_str   = MOIS_FR[mois_num]

rapport_path = None
for r in rapports:
    if f"rapport mensuel {mois_str} {annee}" in os.path.basename(r).lower():
        rapport_path = r
        break
if rapport_path is None:
    rapport_path = sorted(rapports)[-1]
    print(f"⚠️  Rapport mensuel {mois_str} {annee} non trouvé — utilisation de : {os.path.basename(rapport_path)}")

def find_block_range(lines, col0_value):
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
    brand_data = {}
    cat_totals = {}
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

_, s1, e1 = find_block_range(lines, 'marque4')
_, s2, e2 = find_block_range(lines, 'marque')
_, s3, e3 = find_block_range(lines, 'marque2')

brand_data_ete,   cat_totals_ete   = parse_block(lines, s1, e1) if s1 else ({}, {})
brand_data_4s,    cat_totals_4s    = parse_block(lines, s2, e2) if s2 else ({}, {})
brand_data_hiver, cat_totals_hiver = parse_block(lines, s3, e3) if s3 else ({}, {})

CATS = ['PREMIUM', 'MEDIUM', 'BUDGET']

def sum_cats(ct_dict):
    qty = ca = marge = 0
    evos = []
    for cat in CATS:
        ct = ct_dict.get(cat, {})
        qty   += parse_int(ct.get('qty', 'N/A'))       or 0
        ca    += parse_int(ct.get('ca', 'N/A'))         or 0
        marge += parse_int(ct.get('marge_eur', 'N/A')) or 0
        evo = parse_pct(ct.get('ca_evo', 'N/A'))
        if evo is not None:
            evos.append(evo)
    avg_evo = round(sum(evos)/len(evos), 1) if evos else None
    marge_pct = round(marge/ca*100, 1) if ca else None
    return qty, ca, marge, avg_evo, marge_pct

s_ete   = sum_cats(cat_totals_ete)
s_4s    = sum_cats(cat_totals_4s)
s_hiver = sum_cats(cat_totals_hiver)

g_qty   = s_ete[0] + s_4s[0] + s_hiver[0]
g_ca    = s_ete[1] + s_4s[1] + s_hiver[1]
g_marge = s_ete[2] + s_4s[2] + s_hiver[2]
g_marge_pct = round(g_marge / g_ca * 100, 2) if g_ca else None
g_evos  = [v[3] for v in (s_ete, s_4s, s_hiver) if v[3] is not None]
g_evo   = round(sum(g_evos)/len(g_evos), 1) if g_evos else None

season_summary = {
    'ÉTÉ':       {'qty': s_ete[0],   'ca': s_ete[1],   'marge_pct': s_ete[4]},
    '4 SAISONS': {'qty': s_4s[0],    'ca': s_4s[1],    'marge_pct': s_4s[4]},
    'HIVER':     {'qty': s_hiver[0], 'ca': s_hiver[1], 'marge_pct': s_hiver[4]},
}

# STEP 3 — FILL TABLES WITH str.replace

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

SEASON_BLOCKS = [
    ('ÉTÉ',       cat_totals_ete,   s_ete),
    ('4 SAISONS', cat_totals_4s,    s_4s),
    ('HIVER',     cat_totals_hiver, s_hiver),
]

for saison, cat_totals, s_tot in SEASON_BLOCKS:
    for cat in CATS:
        old = f"| **{saison}** | {cat} | | | | | | | |"
        ct  = cat_totals.get(cat)
        if ct:
            st  = statut(ct['ca_evo'])
            new = f"| **{saison}** | {cat} | {ct['qty']} | {ct['pdm']} | {fmt_eur(ct['ca'])} | {ct['ca_evo']} | {fmt_eur(ct['marge_eur'])} | {ct['marge_pct']} | {st} |"
        else:
            new = f"| **{saison}** | {cat} | N/A | N/A | N/A | N/A | N/A | N/A | ⚪ |"
        rapport = rapport.replace(old, new)

    sq, sc, sm, s_evo_avg, s_marge_pct = s_tot
    s_evo_str      = f"{'+' if s_evo_avg and s_evo_avg >= 0 else ''}{s_evo_avg} %" if s_evo_avg is not None else 'N/A'
    s_marge_pct_str = f"{s_marge_pct} %" if s_marge_pct is not None else 'N/A'

    old_tot = f"| *Total {saison}* | | | | | | | | |"
    new_tot = f"| *Total {saison}* | | {sq} | — | {sc} € | {s_evo_str} | {sm} € | {s_marge_pct_str} | {statut(s_evo_str)} |"
    rapport = rapport.replace(old_tot, new_tot)

g_evo_str       = f"{'+' if g_evo and g_evo >= 0 else ''}{g_evo} %" if g_evo is not None else 'N/A'
g_marge_pct_str = f"{round(g_marge_pct, 2)} %" if g_marge_pct is not None else 'N/A'
old_grand = "| **TOTAL PNEUS** | | | | | | | | |"
new_grand = f"| **TOTAL PNEUS** | | {g_qty} | — | {g_ca} € | {g_evo_str} | {g_marge} € | {g_marge_pct_str} | {statut(g_evo_str)} |"
rapport = rapport.replace(old_grand, new_grand)

TEMPLATE_BRANDS = {
    'PREMIUM': ['AUTRE', 'CONTINENTAL', 'GOODYEAR', 'MICHELIN', 'PIRELLI'],
    'MEDIUM':  ['AUTRE', 'FEU VERT', 'HANKOOK', 'KUMHO', 'NEXEN', 'NOKIAN'],
    'BUDGET':  ['AUTRE', 'ROVELO', 'TRACMAX'],
}

missing = []
for cat, brands in TEMPLATE_BRANDS.items():
    for brand in brands:
        old = f"| **{cat}** | {brand} | | | | | | | |"
        d   = brand_data_ete.get((cat, brand))
        if d:
            st  = statut(d['ca_evo'])
            new = f"| **{cat}** | {brand} | {d['qty']} | {d['pdm']} | {fmt_eur(d['ca'])} | {d['ca_evo']} | {fmt_eur(d['marge_eur'])} | {d['marge_pct']} | {st} |"
            rapport = rapport.replace(old, new)
        else:
            rapport = rapport.replace(old, f"| **{cat}** | {brand} | N/A | N/A | N/A | N/A | N/A | N/A | ⚪ |")
            missing.append(f"{cat}/{brand}")

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write(rapport)

# STEP 4 — BUILD COMPACT SUMMARY FOR AI

brands_list = [
    {'cat': c, 'brand': b, 'ca': parse_int(d['ca']), 'evo': parse_pct(d['ca_evo']), 'marge_pct': parse_pct(d['marge_pct'])}
    for (c, b), d in brand_data_ete.items()
]
top_gainers = sorted([b for b in brands_list if b['evo'] and b['ca'] and b['ca'] > 0],
                     key=lambda x: x['evo'], reverse=True)[:3]
top_losers  = sorted([b for b in brands_list if b['evo'] and b['evo'] < 0], key=lambda x: x['evo'])[:3]
mg_alerts   = [b for b in brands_list if b['marge_pct'] and b['marge_pct'] < 10 and b['ca'] and b['ca'] > 0]

summary = {
    "rapport":         rapport_path,
    "mois":            mois_str,
    "annee":           annee,
    "periode":         period_str,
    "total_qty":       g_qty,
    "total_ca":        g_ca,
    "total_marge_pct": g_marge_pct_str,
    "saisons":         season_summary,
    "top_croissance":  [{"cat": b['cat'], "brand": b['brand'], "evo": b['evo']} for b in top_gainers],
    "top_declin":      [{"cat": b['cat'], "brand": b['brand'], "evo": b['evo']} for b in top_losers],
    "alertes_marge":   [{"cat": b['cat'], "brand": b['brand'], "marge_pct": b['marge_pct']} for b in mg_alerts],
}

# STEP 5 — CONFIRM

print(f"✅ Tableaux Pneus mis à jour : {rapport_path}")
print(f"✅ Mois : {mois_str} {annee} — période : {period_str}")
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

> "Rédige 4 points clés de l'analyse pneus pour le rapport mensuel Feu Vert Annecy.
> Total pneus mois : {summary['total_qty']} unités, CA {summary['total_ca']} €, marge {summary['total_marge_pct']}.
> Répartition par saison : {summary['saisons']}
> Top croissance marque ÉTÉ : {summary['top_croissance']}
> Top déclin marque ÉTÉ : {summary['top_declin']}
> Alertes marge (< 10 %) : {summary['alertes_marge']}
> Ton : factuel, orienté management, en français, puces courtes."

Insérer le résultat dans la section `### Points clés de l'analyse pneus`
en remplaçant les lignes `* [Point clé...]` existantes.
