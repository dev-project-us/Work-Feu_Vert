import os, glob, re, csv
from datetime import datetime
import traceback

def clean_num(x):
    if not x: return 0
    return float(x.replace('\xa0', '').replace(' ', '').replace('€', '').replace('%', '').replace('pts', '').replace(',', '.').strip())

def main():
    try:
        # File identification
        folder = r"C:\Users\utilisateur203\Documents\Personnal\Feu Vert Seynod\resources\SUC"
        csv_files = glob.glob(os.path.join(folder, "SUC - *.csv"))

        annee_courante = datetime.today().year
        fichier_semaine = None
        fichier_objectifs = None

        for f in csv_files:
            with open(f, 'r', encoding='utf-8-sig') as fh:
                content = fh.read()
            if 'libelleJour' in content:
                fichier_objectifs = f
            else:
                m = re.search(r'Du \d{2}/\d{2}/(\d{4})', content)
                if m and int(m.group(1)) == annee_courante:
                    fichier_semaine = f

        if not fichier_semaine or not fichier_objectifs:
            print("Erreur: Fichiers CSV requis manquants.")
            return

        with open(fichier_semaine, 'r', encoding='utf-8-sig') as f:
            c = f.read()

        m = re.search(r'Du \d{2}/\d{2}/\d{4},(\d{2}/\d{2}/\d{4})', c)
        date_fin_str = m.group(1)
        date_fin = datetime.strptime(date_fin_str, "%d/%m/%Y")
        semaine = date_fin.isocalendar()[1]
        date_debut_str = re.search(r'Du (\d{2}/\d{2}/\d{4}),', c).group(1)

        lines = c.split('\n')
        def get_vals_csv(header_prefix):
            for i, l in enumerate(lines):
                if l.startswith(header_prefix):
                    if i + 1 < len(lines):
                        return next(csv.reader([lines[i+1]]))
            return []

        vals_glob = get_vals_csv('caht_n')
        cattc_n_raw = vals_glob[4]
        textbox4 = vals_glob[1]
        marge_n_raw = vals_glob[6]
        textbox24 = vals_glob[7]
        textbox14_value = vals_glob[11]
        textbox17_freq_evo = vals_glob[12]
        cattc_n_2 = vals_glob[13]
        textbox17_panier_evo = vals_glob[14]

        vals_ls = get_vals_csv('textbox22')
        ls_ca_raw = vals_ls[2]
        ls_evo_ca = vals_ls[1]
        ls_marge_raw = vals_ls[4]
        ls_evo_marge = vals_ls[5]
        ls_panier_raw = vals_ls[9]
        ls_evo_panier = vals_ls[10]

        vals_at = get_vals_csv('textbox43')
        at_ca_raw = vals_at[2]
        at_evo_ca = vals_at[1]
        at_marge_raw = vals_at[4]
        at_evo_marge = vals_at[5]
        at_nb_or_raw = vals_at[7]
        at_evo_nbor = vals_at[8]
        at_panier_raw = vals_at[9]
        at_evo_panier = vals_at[10]

        with open(fichier_objectifs, 'r', encoding='utf-8-sig') as f:
            obj_lines = f.read().split('\n')

        obj_vals = None
        for l in obj_lines:
            if ',' in l and 'CATTC' not in l and l.split(',')[2] != '0':
                try:
                    vals = next(csv.reader([l]))
                    if len(vals) > 20: 
                        obj_vals = vals
                        break
                except: pass

        textbox8 = obj_vals[16] # 17th
        textbox50 = obj_vals[28] # 29th
        textbox42 = obj_vals[29] # 30th

        # Values comp
        cattc_n = int(clean_num(cattc_n_raw))
        ca_obj_ttc = int(clean_num(textbox8))
        caht_evo = clean_num(textbox4)
        ca_n1 = round(cattc_n / (1 + caht_evo / 100))
        ca_ecart = round((cattc_n / ca_obj_ttc - 1) * 100, 1)

        marge_n = clean_num(marge_n_raw)
        marge_obj = clean_num(textbox50)
        marge_evo = clean_num(textbox24)
        marge_n1 = round(marge_n - marge_evo, 1)
        marge_ecart = round(marge_n - marge_obj, 1)

        freq_n = int(clean_num(textbox14_value))
        freq_evo = clean_num(textbox17_freq_evo)
        freq_n1 = round(freq_n / (1 + freq_evo / 100))

        panier_n = clean_num(cattc_n_2)
        panier_n1 = ca_n1 / freq_n1 if freq_n1 else 0
        panier_evo = clean_num(textbox17_panier_evo)

        # LS
        ls_ca = int(clean_num(ls_ca_raw))
        ls_evo = clean_num(ls_evo_ca)
        ls_n1 = round(ls_ca / (1 + ls_evo / 100))

        ls_marge = clean_num(ls_marge_raw)
        ls_marge_evo = clean_num(ls_evo_marge)
        ls_marge_n1 = round(ls_marge - ls_marge_evo, 1)

        ls_panier = clean_num(ls_panier_raw)
        ls_panier_evo = clean_num(ls_evo_panier)
        ls_panier_n1 = round(ls_panier / (1 + ls_panier_evo / 100), 1)

        # Atelier
        at_ca = int(clean_num(at_ca_raw))
        at_evo = clean_num(at_evo_ca)
        at_n1 = round(at_ca / (1 + at_evo / 100))

        at_marge = clean_num(at_marge_raw)
        at_marge_evo = clean_num(at_evo_marge)
        at_marge_n1 = round(at_marge - at_marge_evo, 1)

        at_nb_or = int(clean_num(at_nb_or_raw))
        at_nb_or_evo = clean_num(at_evo_nbor)
        at_nb_or_n1 = round(at_nb_or / (1 + at_nb_or_evo / 100))

        at_panier = clean_num(at_panier_raw)
        at_panier_evo = clean_num(at_evo_panier)
        at_panier_n1 = round(at_panier / (1 + at_panier_evo / 100), 1)

        def statut_n1(val):
            if val > 0:    return '🟢'
            elif val == 0: return '🟡'
            else:          return '🔴'

        tmpl_path = r"C:\Users\utilisateur203\Documents\Personnal\Feu Vert Seynod\templates\rapport_hebdomadaire_template.md"
        with open(tmpl_path, 'r', encoding='utf-8') as f:
            tmpl = f.read()

        tmpl = tmpl.replace('[JJ/MM/AAAA] au [JJ/MM/AAAA]', f"{date_debut_str} au {date_fin_str}")

        s2 = f"|**CA TTC Total**|{cattc_n} €|{ca_obj_ttc} €|{ca_ecart:+.1f} %|{ca_n1} €|{caht_evo:+.1f} %|\n|**Marge Brute**|{marge_n} %|{marge_obj} %|{marge_ecart:+.1f} pts|{marge_n1} %|{marge_evo:+.1f} pts|\n|**Fréquentation**|{freq_n} clts|-| - |{freq_n1} clts|{freq_evo:+.1f} %|\n|**Panier Moyen**|{panier_n} €|-| - |{panier_n1:.1f} €|{panier_evo:+.1f} %|\n"
        tmpl = re.sub(r'\|.*CA HT Total.*(?:\n\|.*)*\n', s2, tmpl, count=1)

        s3_ls = f"|**CA TTC Magasin**|{ls_ca} €|- €|{ls_n1} €|{ls_evo:+.1f} %|{statut_n1(ls_evo)}|\n|**Marge Magasin**|{ls_marge} %|-|{ls_marge_n1} %|{ls_marge_evo:+.1f} pts|{statut_n1(ls_marge_evo)}|\n|**Panier Moyen LS**|{ls_panier} €|-|{ls_panier_n1} €|{ls_panier_evo:+.1f} %|{statut_n1(ls_panier_evo)}|\n"
        tmpl = re.sub(r'\|.*CA HT Magasin.*(?:\n\|.*)*\n', s3_ls, tmpl, count=1)

        s3_at = f"|**CA TTC Atelier**|{at_ca} €|- €|{at_n1} €|{at_evo:+.1f} %|{statut_n1(at_evo)}|\n|**Marge Atelier**|{at_marge} %|-|{at_marge_n1} %|{at_marge_evo:+.1f} pts|{statut_n1(at_marge_evo)}|\n|**Nombre d'OR**|{at_nb_or}|-|{at_nb_or_n1}|{at_nb_or_evo:+.1f} %|{statut_n1(at_nb_or_evo)}|\n|**Panier Moyen Atel.**|{at_panier} €|-|{at_panier_n1} €|{at_panier_evo:+.1f} %|{statut_n1(at_panier_evo)}|\n"
        tmpl = re.sub(r'\|.*CA HT Atelier.*(?:\n\|.*)*\n', s3_at, tmpl, count=1)

        out_dir = r"C:\Users\utilisateur203\Documents\Personnal\Feu Vert Seynod\Rapport hebdomadaire"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"rapport hebdomadaire semaine {semaine}.md")

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(tmpl)

        print(f"SUCCESS|{out_path}|{cattc_n}|{marge_n}|{freq_n}")

    except Exception as e:
        print("ERROR")
        traceback.print_exc()

if __name__ == '__main__':
    main()
