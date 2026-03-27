# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Obsidian vault** used for professional data analysis at **Feu Vert Annecy** (automotive service center). It converts CSV export data into structured French-language business analysis reports in Markdown format.

- **Core logic:** `.agent/skills/` — Markdown skill definitions invoked via slash commands
- **Incoming data:** `resources/` — CSV exports organized in subfolders
- **Templates:** `templates/` — Markdown report templates in French
- **Output:** `Rapport hebdomadaire/` — generated weekly reports

## Slash Commands (Agent Skills)

Run these commands inside Claude Code to trigger report generation:

| Command | Skill File | Purpose |
|---------|-----------|---------|
| `/chiffre` | `.agent/skills/chiffre.md` | Fill Sections 2, 3, and 7 from SUC CSV exports |
| `/ratios` | `.agent/skills/ratios_prioritaires.md` | Fill Section 4 (Priority KPIs) from ratios CSV |
| `/defectuosite` | `.agent/skills/defectuosite.md` | Fill Section 5 Atelier (Taux de Défectuosité) from CA_Main_d_oeuvre CSV |

`/chiffre` also invokes `/ratios` at completion. **Section 5 LS** (Staff Libre Service ratios de vente) has no skill yet — must be filled manually.

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

**`defectuosite.md`** — fills Section 5 Atelier:
1. Scan `resources/defectuosite/` for file containing `technicien3` column
2. Extract week end date from the line containing `ANNECY` with `/` date separators
3. Find matching rapport file by week number
4. Parse the last CSV block (starts with `technicien3`) for per-technician rates
5. Write into Section 5 Atelier table; ignore excluded staff (see below)
> **Note:** Steps 4–6 are stubs in the current skill file — implement when first needed.

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
└── defectuosite/
    └── CA_Main_d_oeuvre (...).csv              ← contains technicien3 column
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
| Panier TTC→HT | `cattc_n_2` ÷ 1.2 |
| N-1 values | derive: `realized / (1 + evo/100)` |

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

- **Hardcoded paths in skills**: All skill files reference `C:\Users\utilisateur203\Documents\Personnal\Second Brain\` — this does not match the actual vault path `C:\Users\mendo\Documents\Work\`. Adjust paths when executing any file-system operations from the skills.
- **`rapport_mensuel_template.md`**: Title header incorrectly reads "Rapport d'Analyse Hebdomadaire" instead of monthly.
- **Section 7 template mismatch**: The template shows `%` placeholders for the Marge row, but the actual output uses euros (`€`). Follow the format in `chiffre.md` and existing generated reports, not the template skeleton.
- **`defectuosite.md` incomplete**: Skill steps 4–6 are stubs — implement the extraction and writing logic when first invoked.

## Content & Style Rules

- All reports are written in French, in the voice of a **Senior Business Analyst / Workshop Manager**
- No emojis, no AI branding, no decorative formatting — clean standard Markdown only
- Missing data must be written as `N/A` — never guess or hallucinate values
- **Strict Percentages**: In Staff tables (LS or Atelier), output ONLY the final percentage (e.g. `71,4 %`). Never append raw fractions or context strings like `(10/14 PP)`.
- **Clean Tables**: In Section 2, output only the exact rows defined in the template — do not add extra rows.
- **Strict Weekly Perimeter**: Use only data for week N-1. If a CSV provides MTD/cumul figures without daily breakdown, mark Realized fields as `N/A`.
- **Excluded staff** (never appear in atelier aggregations or individual sections): Ihsan, Emilie, Nathan
