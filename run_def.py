import pathlib, glob, os, csv, io
from datetime import datetime

folder = "C:/Users/mendo/Documents/Work/resources/defectuosite"
csv_files = glob.glob(os.path.join(folder, "*.csv"))

fichier_def = None
for f in csv_files:
    with open(f, 'r', encoding='utf-8-sig') as fh:
        content = fh.read()
    if 'technicien3' in content:
        fichier_def = f
        break

if not fichier_def:
    print("CSV not found")
    exit(1)

blocks = content.split('\n\n')
if not any('technicien3' in b for b in blocks):
    blocks = content.split('\r\n\r\n')
if not any('technicien3' in b for b in blocks):
    blocks = content.split('\n')
    
synthese_block = None
for block in blocks:
    if 'technicien3' in block:
        lines = block.splitlines()
        for i, line in enumerate(lines):
            if line.startswith('technicien3'):
                synthese_block = '\n'.join(lines[i:])
                break
        if synthese_block: break

if not synthese_block:
    lines = content.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('technicien3'):
            synthese_block = '\n'.join(lines[i:])
            break

techniciens = {}
reader = csv.DictReader(io.StringIO(synthese_block))
for row in reader:
    nom = row.get('technicien3', '').strip()
    if nom:
        techniciens[nom] = row

NOM_MAP = {
    'Alishan A.':      'ALISHAN A.',
    'Chandrack K.':    'CHANDRACK K.',
    'Mohammed Ali M.': 'MOHAMMED ALI M.',
    'Gael R.':         'GAEL R.',
    'Denis D.':        'DENIS D.',
}

COLS = [
    ('nb_diag_realises',        'Nb OR'),
    ('taux_def_batterie3',      'Déf. Batterie'),
    ('taux_def_disques_av3',    'Disq AV'),
    ('taux_def_disques_ar3',    'Disq AR'),
    ('taux_def_plaquettes_av3', 'Plaq Av'),
    ('taux_def_plaquettes_ar3', 'Plaq Ar'),
    ('taux_def_nci3',           'Déf. NCI'),
    ('taux_def_vcf3',           'Déf. VCF (Frein)'),
    ('taux_def_geometrie3',     'Déf. Géo'),
    ('taux_def_beg3',           'Def BEG'),
    ('taux_def_vcr3',           'Déf. VCR'),
    ('taux_def_amortisseurs3',  'Déf. Amort'),
    ('taux_def_pare_brise',     'Déf. Pare-brise'),
]

rapport_path = "C:/Users/mendo/Documents/Work/Rapport hebdomadaire/rapport hebdomadaire semaine 14.md"

with open(rapport_path, 'r', encoding='utf-8') as fh:
    rapport = fh.read()

lines = rapport.splitlines()

for nom_template, nom_csv in NOM_MAP.items():
    if nom_csv not in techniciens:
        continue
    data = techniciens[nom_csv]
    vals = [data.get(col, '').strip() or '-' for col, _ in COLS]
    
    for i, line in enumerate(lines):
        if nom_template in line and '|' in line:
            new_line = f"| **{nom_template}** | " + " | ".join(vals) + " |"
            lines[i] = new_line
            break

with open(rapport_path, 'w', encoding='utf-8') as fh:
    fh.write("\n".join(lines) + "\n")
print("Done writing to rapport")
