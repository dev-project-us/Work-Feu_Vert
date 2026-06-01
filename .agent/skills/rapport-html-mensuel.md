---
name: rapport-html-mensuel
description: >
  Transforms a Feu Vert Annecy monthly report (Markdown .md file) into a
  polished, shareable single-file HTML dashboard. ALWAYS use this skill when
  the user types /html-mensuel, /rapport-html-mensuel, or asks to "transformer",
  "convertir", "générer le HTML", or "mettre en forme" a monthly/mensuel report
  file. Also triggers when the user uploads a rapport_mensuel_*.md file and
  asks to convert it or send it to someone.
---

# Rapport HTML Mensuel — Skill

Converts a Feu Vert Annecy `rapport mensuel *.md` file into a
self-contained, interactive HTML dashboard that can be sent directly to
anyone and opened in any browser — no internet needed for layout (fonts load
from Google Fonts if available, degrade gracefully otherwise).

---

## Trigger

User types `/html-mensuel`, `/rapport-html-mensuel`, or words like:
- "transforme le rapport mensuel en HTML"
- "génère le fichier HTML du mois"
- "convertis le rapport mensuel"
- "mets en forme le rapport du mois"
- "crée le fichier mensuel à envoyer"

Or uploads a `rapport mensuel *.md` and asks to convert/send it.

---

## Step 1 — Find the source file

1. Check if the user referenced a specific `.md` file path
2. Check if a monthly `.md` report is referenced in the conversation
3. If no file found, scan `Rapport mensuel/` for the most recent file
4. If still ambiguous, ask: *"Quel fichier rapport mensuel veux-tu convertir ?"*

Read the full Markdown content before proceeding.

---

## Step 2 — Parse the report

Extract these blocks (all may not be present every month — skip gracefully):

| Block | Source section in MD |
|---|---|
| `mois_annee` | Line starting with **Mois :** (e.g. "Mai 2026") |
| `brief` | Section `## 1. Bilan global` — full paragraph after **Vision Globale :** |
| `chiffres_globaux` | Main table in `## 2. Chiffres Globaux` |
| `contrats` | Sub-table `### Contrat & Cofidis` |
| `ls_chiffres` | Table `### Libre Service (LS)` inside Section 3 |
| `atelier_chiffres` | Table `### Atelier` inside Section 3 |
| `familles` | Table `# Analyse spécifique / Familles` or `## Analyse par Familles` |
| `familles_points_cles` | Bullet list `### Points clés de l'analyse par famille` |
| `pneus_saison` | Table `### Analyse Pneus par Saison` |
| `pneus_marque` | Table `### Détail par Marque` |
| `pneus_points_cles` | Bullet list `### Points clés de l'analyse pneus` |
| `ratios` | Table `## 4. Ratios Prioritaires` |
| `ls_staff` | Table `### Staff Libre Service` |
| `atelier_staff` | Table `### Staff Atelier` |
| `bilan_actions` | Numbered list `## 6. Bilan & Plans d'Action` |
| `rh_alertes` | `### 7.1 Alerte RH` |
| `rh_absences` | `### 7.2 Absence / Congé` |
| `rh_recrutement` | `### 7.3 Recrutement / Départ` |

**Status emoji mapping:**
- 🟢 → `<span class="tag green">🟢</span>` + use `num-green` on positive deltas
- 🔴 → `<span class="tag red">🔴</span>` + use `num-red` on negative deltas
- 🟡 → `<span class="tag yellow">🟡</span>`

**KPI card status:** Compare realised vs objective/N-1:
- Above target → `class="kpi-card good"`
- Below target → `class="kpi-card bad"`
- Neutral/no target → `class="kpi-card neutral"`

---

## Step 3 — Build the HTML file

Use the full CSS block below verbatim inside `<style>`. Do NOT modify the CSS.
Replace only the data content.

Output filename: `rapport_mensuel_{mois_slug}_{annee}.html`
  — where `{mois_slug}` is the month in lowercase French with no accents (e.g. `mai`, `juin`, `fevrier`).
Save to: `Rapport mensuel/html/rapport_mensuel_{mois_slug}_{annee}.html`
  (locate `Rapport mensuel/` with `find_dir()` — walk up from the current file).

### Full CSS (copy verbatim)

```css
:root {
  --red: #E8321A;
  --dark: #0F0F0F;
  --card: #181818;
  --card2: #1F1F1F;
  --border: #2A2A2A;
  --text: #E8E8E0;
  --muted: #888;
  --green: #2ECC71;
  --yellow: #F4C430;
  --accent: #E8321A;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--dark); color: var(--text); font-family: 'DM Sans', sans-serif; font-size: 14px; line-height: 1.6; }
header { background: #1A6B38; padding: 40px 48px 32px; position: relative; overflow: hidden; }
header::before { content: "FEU VERT"; font-family: 'Bebas Neue', sans-serif; font-size: 180px; color: rgba(0,0,0,0.12); position: absolute; right: -10px; top: -20px; letter-spacing: 4px; line-height: 1; pointer-events: none; }
header .label { font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 3px; text-transform: uppercase; opacity: 0.75; margin-bottom: 8px; }
header h1 { font-family: 'Bebas Neue', sans-serif; font-size: 52px; letter-spacing: 2px; line-height: 1; }
header .meta { margin-top: 16px; font-size: 13px; opacity: 0.85; display: flex; gap: 24px; flex-wrap: wrap; }
nav { background: var(--card); border-bottom: 1px solid var(--border); padding: 0 48px; display: flex; gap: 0; overflow-x: auto; }
nav button { background: none; border: none; cursor: pointer; color: var(--muted); font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500; padding: 16px 20px; border-bottom: 2px solid transparent; white-space: nowrap; transition: all .2s; letter-spacing: 0.3px; }
nav button:hover { color: var(--text); }
nav button.active { color: var(--red); border-bottom-color: var(--red); }
main { padding: 40px 48px; max-width: 1200px; margin: 0 auto; }
.section { display: none; animation: fadeIn .3s ease; }
.section.active { display: block; }
@keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
.section-title { font-family: 'Bebas Neue', sans-serif; font-size: 32px; letter-spacing: 1px; color: var(--text); margin-bottom: 6px; }
.section-sub { color: var(--muted); font-size: 13px; margin-bottom: 28px; }
.brief-box { background: var(--card); border-left: 4px solid var(--red); border-radius: 0 12px 12px 0; padding: 24px 28px; font-size: 14px; line-height: 1.8; color: #ccc; margin-bottom: 32px; }
.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }
.kpi-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px 22px; position: relative; overflow: hidden; transition: transform .2s, box-shadow .2s; }
.kpi-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.4); }
.kpi-card .kpi-label { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
.kpi-card .kpi-value { font-family: 'Bebas Neue', sans-serif; font-size: 36px; letter-spacing: 1px; line-height: 1; }
.kpi-card .kpi-delta { font-size: 12px; margin-top: 6px; font-family: 'DM Mono', monospace; }
.kpi-card.good .kpi-value { color: var(--green); }
.kpi-card.bad .kpi-value { color: var(--red); }
.kpi-card.neutral .kpi-value { color: var(--text); }
.kpi-card .corner-dot { width: 6px; height: 6px; border-radius: 50%; position: absolute; top: 16px; right: 16px; }
.kpi-card.good .corner-dot { background: var(--green); }
.kpi-card.bad .corner-dot { background: var(--red); }
.kpi-card.neutral .corner-dot { background: var(--yellow); }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 32px; }
@media(max-width:700px){ .two-col { grid-template-columns: 1fr; } main { padding: 24px 20px; } nav { padding: 0 16px; } header { padding: 28px 20px 24px; } header::before { font-size:100px; } }
.card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 22px 24px; }
.card h3 { font-family: 'Bebas Neue', sans-serif; font-size: 20px; letter-spacing: 1px; margin-bottom: 14px; }
.tbl-wrap { overflow-x: auto; margin-bottom: 28px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead tr { border-bottom: 2px solid var(--border); }
thead th { text-align: left; padding: 10px 12px; font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--muted); font-weight: 400; }
tbody tr { border-bottom: 1px solid var(--border); transition: background .15s; }
tbody tr:hover { background: var(--card2); }
tbody td { padding: 11px 12px; }
tbody td:first-child { font-weight: 500; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-family: 'DM Mono', monospace; font-weight: 500; }
.tag.green { background: rgba(46,204,113,.18); color: var(--green); }
.tag.red { background: rgba(232,50,26,.18); color: var(--red); }
.tag.yellow { background: rgba(244,196,48,.18); color: var(--yellow); }
.num-green { color: var(--green); font-family: 'DM Mono', monospace; }
.num-red { color: var(--red); font-family: 'DM Mono', monospace; }
.num-yellow { color: var(--yellow); font-family: 'DM Mono', monospace; }
.num { font-family: 'DM Mono', monospace; }
.progress-row { margin-bottom: 16px; }
.progress-label { display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 5px; }
.progress-label span:first-child { font-weight: 500; }
.progress-label span:last-child { font-family: 'DM Mono', monospace; color: var(--muted); }
.progress-track { background: var(--border); border-radius: 4px; height: 8px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 4px; transition: width 1s ease; }
.progress-fill.green { background: var(--green); }
.progress-fill.red { background: var(--red); }
.progress-fill.yellow { background: var(--yellow); }
.raf-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 32px; }
.raf-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px 22px; }
.raf-card .raf-label { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 12px; }
.raf-card .raf-main { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 10px; }
.raf-card .raf-val { font-family: 'Bebas Neue', sans-serif; font-size: 28px; }
.raf-card .raf-pct { font-family: 'DM Mono', monospace; font-size: 20px; }
.alert { border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; font-size: 13px; border-left: 3px solid; }
.alert.warn { background: rgba(232,50,26,.1); border-color: var(--red); }
.alert.info { background: rgba(46,204,113,.1); border-color: var(--green); }
.alert strong { display: block; margin-bottom: 4px; font-size: 13px; }
.action-list { list-style: none; display: grid; gap: 14px; }
.action-item { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; display: flex; gap: 14px; align-items: flex-start; }
.action-num { background: var(--red); color: #fff; font-family: 'Bebas Neue', sans-serif; font-size: 18px; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border-radius: 6px; flex-shrink: 0; margin-top: 2px; }
.action-content strong { display: block; font-size: 14px; margin-bottom: 4px; }
.action-content p { font-size: 13px; color: var(--muted); }
.divider { border: none; border-top: 1px solid var(--border); margin: 28px 0; }
.sub-title { font-family: 'Bebas Neue', sans-serif; font-size: 22px; letter-spacing: 1px; margin-bottom: 16px; margin-top: 36px; color: var(--muted); padding-top: 24px; border-top: 1px solid var(--border); }
```

### HTML Structure

```html
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rapport Mensuel {MOIS} {ANNÉE} — Feu Vert Annecy</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  /* PASTE FULL CSS HERE */
</style>
</head>
<body>

<header>
  <div class="label">Rapport Mensuel · Centre Annecy Seynod</div>
  <h1>{MOIS} {ANNÉE}</h1>
  <div class="meta">
    <span>📅 {MOIS} {ANNÉE}</span>
    <span>🏪 Feu Vert Annecy</span>
  </div>
</header>

<nav>
  <button class="active" onclick="show('brief')">🔍 Bilan Global</button>
  <button onclick="show('ls')">🛒 LS</button>
  <button onclick="show('atelier')">🔧 Atelier</button>
  <button onclick="show('familles')">📦 Familles</button>
  <button onclick="show('pneus')">🔵 Pneus</button>
  <button onclick="show('actions')">🎯 Bilan & Actions</button>
  <button onclick="show('rh')">🧑‍💼 RH</button>
</nav>

<main>
  <!-- SECTIONS HERE — see tab specs below -->
</main>

<script>
function show(id) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  event.target.classList.add('active');
}
</script>
</body>
</html>
```

---

## Step 4 — Tab content specs

Build each tab from the parsed data. Skip any sub-section whose data is absent.

### Tab: brief
```
section-title: "Bilan Global"
section-sub: "Synthèse exécutive de {MOIS} {ANNÉE}"
- brief-box: full brief paragraph from MD (keep bold tags)
- kpi-grid (4 cards): CA TTC Total, Marge Brute %, Marge Brute (€), Panier Moyen
  - CA TTC: bad if below objectif, good if above
  - Marge %: good if above objectif, bad if below
  - Marge €: good if above objectif, bad if below
  - Panier: neutral (no monthly objective defined)
- sub-title: "Contrats & Cofidis" → table from contrats
  - color cells: Écart green if positive, red if negative
```

### Tab: ls
```
section-title: "Libre Service"
section-sub: "Chiffres et ratios de vente par conseiller — {MOIS} {ANNÉE}"
1. kpi-grid (3 cards): CA TTC Magasin, Marge Magasin %, Panier Moyen LS
   - status from Statut column (🟢 → good, 🔴 → bad, 🟡 → neutral)
2. sub-title: "Ratios de vente par conseiller" → table from ls_staff
```

### Tab: atelier
```
section-title: "Atelier"
section-sub: "Chiffres, ratios prioritaires et taux de défectuosité — {MOIS} {ANNÉE}"
1. kpi-grid (4 cards): CA TTC Atelier, Marge Atelier %, Nombre d'OR, Panier Moyen Atelier
   - status from Statut column (🟢 → good, 🔴 → bad)
2. sub-title: "Ratios Prioritaires" → kpi-grid (6 cards: Garantie Pneu, Géométrie, VCR, VCF, Plaquette, Dépollution)
   - good if Statut is 🟢, bad if 🔴, neutral if 🟡
   - kpi-delta: show "Réalisé vs Obj: {écart}" and "vs N-1: {évolution}"
3. sub-title: "Taux de Défectuosité par technicien" → table from atelier_staff
```

### Tab: familles
```
section-title: "Familles Produit"
section-sub: "Analyse par famille — {MOIS} {ANNÉE}"
1. tbl-wrap: full familles table (ALL rows including I, J, U, X)
   - Statut column: use tag green/red/yellow
   - Évol. CA: use num-green if positive, num-red if negative
2. sub-title: "Points clés" → render as alert.info per bullet point
   (first bullet as first card, etc. — one alert.info per bullet)
```

### Tab: pneus
```
section-title: "Analyse Pneus"
section-sub: "Par saison, catégorie et marque — {MOIS} {ANNÉE}"
1. sub-title: "Par Saison et Catégorie" → full pneus_saison table
   - Total rows (e.g. "Total ÉTÉ") → render with bold, slightly different background (card2)
   - Statut: tag green/red
   - Évo CA %: num-green if positive, num-red if negative
2. sub-title: "Détail par Marque — ÉTÉ" → pneus_marque table (if present)
   - N/A cells: render as `<td class="num" style="color:var(--muted)">N/A</td>`
3. sub-title: "Points clés" → render as alert.info per bullet (one alert per bullet)
```

### Tab: actions
```
section-title: "Bilan & Plans d'Action"
section-sub: "Retour sur le mois écoulé et priorités pour {MOIS SUIVANT}"
- action-list: one action-item per top-level numbered item in bilan_actions
  - action-num: the item number
  - action-content strong: the bold title text (the part after the number and before "→")
  - action-content p: flatten sub-items into a compact summary (join sub-titles as a single
    descriptive sentence; omit nested Plan d'action / Objectif labels — keep only the key phrase)
```

### Tab: rh
```
section-title: "Informations RH"
section-sub: "Absences, congés, mouvements de personnel — {MOIS} {ANNÉE}"
- sub-title "🚨 Alertes RH" → alert.warn per item in rh_alertes (skip if empty)
- sub-title "📅 Absence / Congé" → alert.info per item in rh_absences (skip if empty)
- sub-title "🔄 Recrutement / Départ" → mix warn/info per item in rh_recrutement
  (departures = warn, incoming/recruiting = info)
- If all three sub-sections are empty, show a single alert.info: "Aucune information RH ce mois."
```

---

## Step 5 — Output

1. Write the complete HTML to `Rapport mensuel/html/rapport_mensuel_{mois_slug}_{annee}.html`
2. Confirm the file path to the user
3. Say: *"Voici le rapport mensuel {MOIS} {ANNÉE} en HTML — prêt à envoyer !"*

---

## Notes & edge cases

- If a section is missing from the MD (e.g. no RH section), skip that tab entirely and remove its nav button.
- If N/A appears in a table cell, render as `<td class="num" style="color:var(--muted)">N/A</td>`
- Negative CA values (like U-Services) → render the value as-is with `num-red`
- Month slug: lowercase, no accents (janvier, fevrier, mars, avril, mai, juin, juillet, aout, septembre, octobre, novembre, decembre)
- Mois suivant in actions tab: compute from the report month (e.g. Mai → Juin)
- Always use French number formatting: spaces as thousands separator, commas as decimal (e.g. `56 688 €`, `52,5 %`)
- The Familles section header may appear as `# Analyse spécifique / Familles` (h1) — treat as Section 3 subsection regardless of heading level
