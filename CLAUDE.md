# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Obsidian vault** used for professional data analysis at **Feu Vert Annecy** (automotive service center). It converts CSV export data into structured French-language business analysis reports in Markdown format.

- **Core logic:** `.agent/skills/` — full Markdown skill definitions; `.claude/commands/` — one-liner prompts that trigger each skill via Claude Code slash commands (both must stay in sync for weekly skills)
- **Incoming data:** `resources/` — CSV exports organized in subfolders; `resources/Resources mensuelles/` — parallel structure for monthly data (note: skill files reference this as `monthly_recap` via `find_dir()`, but the actual folder name on disk is `Resources mensuelles`)
- **Templates:** `templates/` — Markdown report templates in French
- **Output:** `Rapport hebdomadaire/` — generated weekly reports; `Rapport mensuel/` — generated monthly reports

## Slash Commands (Agent Skills)

Run these commands inside Claude Code to trigger report generation:

| Command | Skill File | Purpose |
|---------|-----------|---------|
| `/chiffre` | `.agent/skills/chiffre.md` | Fill Sections 2, 3, and 7 from SUC CSV exports |
| `/ratios` | `.agent/skills/ratios_prioritaires.md` | Fill Section 4 (Priority KPIs) from ratios CSV |
| `/defectuosite` | `.agent/skills/defectuosite.md` | Fill Section 5 Atelier (Taux de Défectuosité) from CA_Main_d_oeuvre CSV |
| `/suivi_vendeur` | `.agent/skills/suivi_vendeur.md` | Fill Section 5 LS (Ratios de Vente par vendeur) from Suivi Individuel CSV |

`/chiffre` also invokes `/ratios` at completion. **Section 5 LS** is fully automated via `/suivi_vendeur` — all columns (Garantie Pneu, Géométrie, VCR, VCF, Plaquette, Dépollution) are implemented.

### Monthly Commands (no registered slash command — invoke by description or keyword)

| Trigger keyword | Skill File | Purpose |
|----------------|-----------|---------|
| `/chiffre-mensuel` | `.agent/skills/chiffre-mensuel.md` | Fill Sections 2 and 3 from `resources/Resources mensuelles/SUC/` — expects **two** `SUC - Situation de chiffre*.csv` files (one for year N, one for N-1) + one Objectifs file |
| `/ratios-mensuel` | `.agent/skills/ratios-mensuel.md` | Fill Section 4 KPIs from `resources/Resources mensuelles/ratios prioritaires/` |
| `/defectuosite-mensuel` | `.agent/skills/defectuosite-mensuel.md` | Fill Section 5 Atelier from `resources/Resources mensuelles/defectuosite/` |
| `/suivi-vendeur-mensuel` | `.agent/skills/suivi-vendeur-mensuel.md` | Fill Section 5 LS from `resources/Resources mensuelles/suivi vendeur/` |

Monthly skills are **not registered in `.claude/commands/`** — Claude Code reads the skill file directly from `.agent/skills/` when the trigger keyword is used.

## Architecture

**Data flow:**

```
CSV in resources/ → Agent Skill (slash command) → Markdown Report in Rapport hebdomadaire/
```

### Skills

**`chiffre.md`** — 6-step workflow:
1. Extract week number N from CSV date fields (ISO calendar)
2. Create output file from template: `Rapport hebdomadaire/rapport hebdomadaire semaine {N}.md`
3. Identify the 3 SUC files in `resources/SUC/` **by content, not filename**:
   - `fichier_objectifs`: contains column `libelleJour`
   - `fichier_mtd`: period string starts with `Du 01/`
   - `fichier_semaine`: everything else (mid-month period, e.g. `Du 16/03/2026`)
4. Extract values using block/column mappings defined in the skill
5. Fill placeholders in Sections 2, 3, and 7
6. Confirm to user

**`ratios_prioritaires.md`** — fills Section 4:
1. Scan `resources/ratios prioritaires/` for file containing `libelleUnivers` column
2. Extract week end date from 2nd line (format: `ANNECY 2,16/03/2026-22/03/2026`)
3. Find matching rapport file by week number
4. Extract 6 KPI values and update Section 4

**`suivi_vendeur.md`** — fills Section 5 LS (Ratios de Vente par vendeur):
1. Scan `resources/suivi vendeur/` for file containing column `textbox390` in its content
2. Extract week end date from line 2 (format: `ANNECY 2,DD/MM/YYYY - DD/MM/YYYY`)
3. Find matching rapport file by week number
4. Parse **Bloc 1** (`textbox3,` header): Garantie Pneu (col 22) and Géométrie (col 28) per vendeur — **if value at col 22/28 doesn't contain `%`, fall back to col 23/29** (position shifts for vendors with few tyre sales)
5. Parse **Bloc 2** (`textbox590,` header): VCR (col 19), Plaquette (col 21), VCF (col 23) per vendeur
6. Parse **Bloc 4** (`textbox326,` header): Dépollution (col 17) per vendeur
7. Write all ratios into Section 5 LS table
8. Confirm to user, listing all values written per vendeur

**`defectuosite.md`** — fills Section 5 Atelier:
1. Scan `resources/defectuosite/` for file containing `technicien3` column
2. Extract week end date from the line containing `ANNECY` with `/` date separators (format: `ANNECY SEYNOD,DD/MM/YYYY,DD/MM/YYYY`; split on `\r\n`)
3. Find matching rapport file by week number
4. Split file on `\r\n\r\n` to find the block starting with `technicien3`; parse with `csv.DictReader`
5. Write per-technician rates into Section 5 Atelier table; ignore excluded staff (see below)

### Templates

- `templates/rapport_hebdomadaire_template.md` — 8-section weekly report (Sections 1–8)
- `templates/rapport_mensuel_template.md` — monthly recap (same structure; **known issue**: title header incorrectly reads "Hebdomadaire")

### Resources Structure

```
resources/
├── SUC/
│   ├── SUC - Objectifs Journaliers (...).csv   ← contains libelleJour column
│   ├── SUC - Situation de chiffre (...).csv    ← fichier_mtd (Du 01/...)
│   └── SUC - Situation de chiffre (...).csv    ← fichier_semaine (Du 16/...)
├── ratios prioritaires/
│   └── Ratios Atelier de date à date .csv
├── defectuosite/
│   └── CA_Main_d_oeuvre (...).csv              ← contains technicien3 column
└── suivi vendeur/
    └── Suivi Individuel des ratios atelier (...).csv  ← contains textbox390 column
resources/Resources mensuelles/           ← monthly data (skill files call this "monthly_recap")
├── SUC/
│   ├── SUC - Objectifs Journaliers (...).csv    ← contains libelleJour column
│   ├── SUC - Situation de chiffre (...).csv     ← fichier_mtd (Du 01/ + current year)
│   └── SUC - Situation de chiffre (...).csv     ← fichier_n1  (Du 01/ + prior year) — must be present
├── ratios prioritaires/
│   └── Ratios Atelier de date à date (...).csv
├── defectuosite/
│   └── CA_Main_d_oeuvre (...).csv
└── suivi vendeur/
    └── Suivi Individuel des ratios atelier (...).csv
```

## Key CSV Mappings

### CSV Parsing Rule

SUC files are **not clean tables** — they contain multiple data blocks separated by blank lines. **Always read raw** with `open(..., encoding='utf-8-sig')`. Do not use pandas with auto-detected headers.

### SUC — Global Block (Section 2)

| Report Field | CSV Column |
|-------------|-----------|
| CA HT Total | `caht_n` |
| Marge % | `marge_n` |
| Fréquentation | `textbox14` |
| Panier TTC (hebdo) | `cattc_n_2` ÷ 1.2 |
| Panier TTC (mensuel) | `cattc_n_2` direct — **do not divide by 1.2** |
| N-1 values (hebdo) | derive: `realized / (1 + evo/100)` |
| N-1 values (mensuel) | read directly from `fichier_n1` — no derivation |

### SUC — LS Block (Section 3 Libre Service)

`textbox22` through `textbox41` — columns defined fully in `chiffre.md`

### SUC — Atelier Block (Section 3 Atelier)

`textbox43` through `textbox64` — columns defined fully in `chiffre.md`

### Ratios Prioritaires — Section 4 KPI Mapping

| Section 4 KPI | CSV `textbox1` (libellé exact) | Objective |
|--------------|-------------------------------|-----------|
| Garantie Pneu | `Garantie Pneu / Pneus vendus` | 50% |
| Géométrie | `Géométrie / Pose Pneu` | 19% |
| VCR (Refroid) | `Liquide de refroidissement / Nb OR` | 7% |
| VCF (Frein) | `Liquide de frein / Nb OR` | 11% |
| Plaquette | `Plaquette / Nb OR` | 11% |
| Dépollution | `Traitements dépollution moteurs / Nb Vidange` | 35% |

Extract columns: `objectif`, `ratioN` (realized), `ratioN_1` (N-1), `textbox130` (écart pts).

### Suivi Vendeur — Section 5 LS Mapping

File identified by presence of `textbox390` in content. Parsed raw with `open(..., encoding='utf-8-sig')`.

**Vendor name map (CSV → Template):**

| Nom Template | Nom CSV (`textbox390`, col 8) |
|:-------------|:------------------------------|
| **Sandrine** | `SANDRINE R.` |
| **Paul** | `PAUL P.` |
| **Kamilia** | `KAMILIA A.` |
| **Chouaib** | `CHOUAIB G.` |
| **Pauline** | `PAULINE R.` |
| **Valentin** | `VALENTIN C.` |

Vendeurs présents dans le CSV mais absents du template (Arnaud B., Elyne S., Isabelle P., Sofiane B.) sont ignorés.

**Bloc 1 confirmed columns** (header starts with `textbox3,`):

| Position | CSV Column | Report Field |
|:---------|:-----------|:-------------|
| 8 | `textbox390` | Nom du vendeur |
| 21 | `textbox46` | Garantie Pneu — quantité (N) |
| 22 | `textbox56` | Garantie Pneu — ratio % (N) ✅ |
| 27 | `textbox158` | Géométrie / Pose Pneu — quantité (N) |
| 28 | `textbox159` | Géométrie / Pose Pneu — ratio % (N) ✅ |

**Bloc 2 confirmed columns** (header `textbox590,`, vendeur name at col 11 `textbox144`):

| Position | CSV Column | Report Field |
|:---------|:-----------|:-------------|
| 19 | `textbox156` | VCR — ratio % ✅ |
| 21 | `textbox146` | Plaquette — ratio % ✅ |
| 23 | `textbox136` | VCF — ratio % ✅ |

**Bloc 4 confirmed columns** (header `textbox326,`, vendeur name at col 9 `textbox14`):

| Position | CSV Column | Report Field |
|:---------|:-----------|:-------------|
| 17 | `textbox201` | Dépollution — ratio % ✅ |

**NCI**: column position not yet confirmed — not extracted.

Ratios are already formatted as `"24,2 %"` in the CSV — preserve as-is. Output ratio % only; never output raw quantities.

### Défectuosité — Section 5 Atelier Mapping

| CSV `technicien3` | Template name |
|------------------|---------------|
| `ALISHAN A.` | **Alishan A.** |
| `CHANDRACK K.` | **Chandrack K.** |
| `MOHAMMED ALI M.` | **Mohammed Ali M.** |
| `GAEL R.` | **Gael R.** |
| `DENIS D.` | **Denis D.** |

Columns: `nb_diag_realises`, `taux_def_batterie3`, `taux_def_disques_av3`, `taux_def_disques_ar3`, `taux_def_plaquettes_av3`, `taux_def_plaquettes_ar3`, `taux_def_nci3`, `taux_def_vcf3`, `taux_def_geometrie3`, `taux_def_beg3`, `taux_def_vcr3`, `taux_def_amortisseurs3`, `taux_def_pare_brise`

## Useful Helper Commands

```bash
# Get the week number being reported (previous week)
python -c "import datetime; print((datetime.date.today() - datetime.timedelta(days=7)).isocalendar()[1])"

# Get current month number and name
python -c "import datetime; now=datetime.datetime.now(); print(f'{now.month:02d}', now.strftime('%B'))"
```

## Known Issues

- **Portable paths**: All skill files use a `find_dir()` helper that walks up the directory tree to locate `resources/`, `Rapport hebdomadaire/`, and `templates/` by name — no hardcoded absolute paths. This works on any machine provided the folder names remain unchanged.
- **Monthly folder name mismatch**: Skill files call `find_dir("monthly_recap")` but the actual folder on disk is `resources/Resources mensuelles/`. The `find_dir()` search will fail unless the folder is renamed to `monthly_recap` or the skill files are updated.
- **Marge Brute € (mensuel)**: `chiffre-mensuel.md` instructs reading `marge_n_2` from the `libelle,marge_n_2,...` block — but this value is "Marge Produit" only (e.g. 46 985), not total marge. The correct total Marge € is `round(caht_n * marge_pct / 100)` (e.g. 186 418 × 54,2 % = 101 039 €). Always use the computed formula, not `marge_n_2`, for the Marge Brute (€) row.
- **Monthly N-1 file**: `/chiffre-mensuel` requires two `SUC - Situation de chiffre*.csv` files — one dated with the current year, one with the prior year. If only one file is present, N-1 values cannot be read and must be preserved from a prior run or marked `N/A`.
- **Section 7 template mismatch**: The template shows `%` placeholders for the Marge row, but the actual output uses euros (`€`). Follow the format in `chiffre.md` and existing generated reports, not the template skeleton.
- **`suivi_vendeur.md` NCI column**: NCI is not extracted (no confirmed column position in any bloc). All other Section 5 LS columns are implemented.
- **`.skill` files at root** (`chiffre.skill`, `defectuosite.skill`, etc.) are binary ZIP archives — do not edit or read them.

## Content & Style Rules

- All reports are written in French, in the voice of a **Senior Business Analyst / Workshop Manager**
- No emojis, no AI branding, no decorative formatting — clean standard Markdown only
- Missing data must be written as `N/A` — never guess or hallucinate values
- **Strict Percentages**: In Staff tables (LS or Atelier), output ONLY the final percentage (e.g. `71,4 %`). Never append raw fractions or context strings like `(10/14 PP)`.
- **Clean Tables**: In Section 2, output only the exact rows defined in the template — do not add extra rows.
- **Strict Weekly Perimeter**: Use only data for week N-1. If a CSV provides MTD/cumul figures without daily breakdown, mark Realized fields as `N/A`.
- **Excluded staff** (never appear in atelier aggregations or individual sections): Ihsan, Emilie, Nathan
