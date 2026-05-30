---
name: rapport-html
description: >
  Transforms a Feu Vert Annecy weekly report (Markdown .md file) into a
  polished, shareable single-file HTML dashboard. ALWAYS use this skill when
  the user types /rapport-html, /html-report, or asks to "transform", "convert",
  "générer le HTML", or "mettre en forme" a weekly/hebdomadaire report file.
  Also triggers when the user uploads a rapport_hebdomadaire_*.md file and asks
  to convert it or send it to someone.
---

# Rapport HTML — Skill

Converts a Feu Vert Annecy `rapport_hebdomadaire_sXX.md` file into a
self-contained, interactive HTML dashboard that can be sent directly to
anyone and opened in any browser — no internet needed for layout (fonts load
from Google Fonts if available, degrade gracefully otherwise).

---

## Trigger

User types `/rapport-html`, `/html-report`, or words like:
- "transforme le rapport en HTML"
- "génère le fichier HTML"
- "convertis le rapport"
- "mets en forme le rapport"
- "crée le fichier à envoyer"

Or uploads a `rapport_hebdomadaire_*.md` and asks to convert/send it.

---

## Step 1 — Find the source file

1. Check if the user referenced a specific `.md` file path
2. Check if a `.md` report is referenced in the conversation
3. If no file found, ask: *"Quel fichier rapport veux-tu convertir ?"*

Read the full Markdown content before proceeding.

---

## Step 2 — Parse the report

Extract these blocks (all may not be present every week — skip gracefully):

| Block | Source section in MD |
|---|---|
| `periode` | Line starting with **Période :** |
| `semaine` | Headline number (e.g. "Semaine 19") |
| `brief` | Section `## 1. Brief global` |
| `chiffres_globaux` | Table in `## 2. Chiffres Globaux` |
| `ls_chiffres` | Table `### Section Libre Service` |
| `atelier_chiffres` | Table `### Section Atelier` |
| `familles` | Table `# Analyse par Familles` |
| `familles_points_cles` | Bullet list after families table |
| `pneus_saison` | Table `### Analyse Pneus par Saison` |
| `pneus_marque` | Table `### Détail par Marque` |
| `pneus_points_cles` | Bullet list after pneus tables |
| `ratios` | Table `## 4. Ratios Prioritaires` |
| `ls_staff` | Table `### Staff Libre Service` |
| `atelier_staff` | Table `### Staff Atelier` |
| `actions_ls` | Numbered list `### Plan d'Action Libre Service` |
| `actions_atelier` | Numbered list `### Plan d'Action Atelier` |
| `raf` | Table `## 7. Reste à Faire` |
| `rh_alertes` | `### 8.1 Alerte RH` |
| `rh_absences` | `### 8.2 Absence / Congé` |
| `rh_recrutement` | `### 8.3 Recrutement / Départ` |

**Status emoji mapping:**
- 🟢 → `<span class="tag green">🟢</span>` + use `num-green` on positive deltas
- 🔴 → `<span class="tag red">🔴</span>` + use `num-red` on negative deltas
- 🟡 → `<span class="tag yellow">🟡</span>`

**KPI card status:** Compare realised vs objective/N-1:
- Above target → `class="kpi-card good"`
- Below target → `class="kpi-card bad"`
- Neutral/no target → `class="kpi-card neutral"`

**RAF progress bar colour:**
- ≥ 70 % → green
- 40–69 % → yellow
- < 40 % → red

---

## Step 3 — Build the HTML file

Use the full CSS block below verbatim inside `<style>`. Do NOT modify the CSS.
Replace only the data content.

Output filename: `rapport_semaine_XX.html` (use the week number from the report).
Save to: `Rapport hebdomadaire/html/rapport_semaine_XX.html` (locate `Rapport hebdomadaire/` with `find_dir()` — walk up from the current file).

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
<title>Rapport Hebdomadaire S{XX} — Feu Vert Annecy</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  /* PASTE FULL CSS HERE */
</style>
</head>
<body>

<header>
  <div class="label">Rapport Hebdomadaire · Centre Annecy Seynod</div>
  <h1>Semaine {XX}</h1>
  <div class="meta">
    <span>📅 {PERIODE}</span>
    <span>🏪 Feu Vert Annecy</span>
  </div>
</header>

<nav>
  <button class="active" onclick="show('brief')">🔍 Brief Global</button>
  <button onclick="show('ls')">🛒 LS</button>
  <button onclick="show('atelier')">🔧 Atelier</button>
  <button onclick="show('actions-ls')">🎯 Plans d'action LS</button>
  <button onclick="show('actions-atelier')">🎯 Plans d'action Atelier</button>
  <button onclick="show('raf')">📅 RAF Mois</button>
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
section-title: "Vision Globale"
section-sub: "Synthèse exécutive de la semaine {XX}"
- brief-box: full brief paragraph from MD (keep bold tags)
- kpi-grid (4 cards): CA TTC Total, Marge Brute, Fréquentation, Panier Moyen
  - status: CA bad if below obj, Marge good if above obj, Fréquentation good if > N-1, Panier bad if < N-1
```

### Tab: ls
```
section-title: "Libre Service"
section-sub: "Chiffres, familles produit et ratios de vente par conseiller"
1. kpi-grid: CA TTC Magasin, Marge Magasin, Panier Moyen LS
2. sub-title: "Ratios de vente par conseiller" → table from ls_staff
3. sub-title: "Familles produit" → table from familles (ALL rows including I, J, U, X)
4. sub-title: "Pneus — Par saison et catégorie" → full pneus_saison table with subtotals
5. sub-title: "Détail par Marque — Été" → pneus_marque table (if present)
```

### Tab: atelier
```
section-title: "Atelier"
section-sub: "Chiffres, ratios prioritaires et taux de défectuosité"
1. kpi-grid: CA TTC Atelier, Marge Atelier, Nombre d'OR, Panier Moyen
2. sub-title: "Ratios Prioritaires" → kpi-grid (6 cards: Garantie Pneu, Géométrie, VCR, VCF, Plaquette, Dépollution)
   - good if realised ≥ objectif, bad if below
3. sub-title: "Taux de Défectuosité par technicien" → table from atelier_staff
```

### Tab: actions-ls
```
section-title: "Plans d'Action — Libre Service"
section-sub: "Priorités opérationnelles semaine {XX}"
- action-list with numbered action-items from actions_ls
```

### Tab: actions-atelier
```
section-title: "Plans d'Action — Atelier"
section-sub: "Priorités opérationnelles semaine {XX}"
- action-list with numbered action-items from actions_atelier
```

### Tab: raf
```
section-title: "Reste à Faire — {MOIS} {ANNÉE}"
section-sub: "Avancement mensuel au {DATE FIN SEMAINE} — {N} jours restants"
- raf-grid: one raf-card per row in raf table (CA, Marge, Contrat, Cofidis)
  - compute pct = Réalisé / Objectif * 100
  - progress bar colour: ≥70% green, 40-69% yellow, <40% red
- alert warn: brief note on daily run-rate needed to reach monthly target
  (daily rate = RAF CA / jours restants, round to nearest 100)
```

### Tab: rh
```
section-title: "Informations RH"
section-sub: "Absences, congés, mouvements de personnel"
- sub-title "🚨 Alertes RH" → alert.warn per item in rh_alertes
- sub-title "📅 Absence / Congé" → alert.info per item in rh_absences
- sub-title "🔄 Recrutement / Départ" → mix warn/info per item in rh_recrutement
  (departures = warn, incoming/recruiting = info)
```

---

## Step 5 — Output

1. Write the complete HTML to `Rapport hebdomadaire/html/rapport_semaine_XX.html`
2. Confirm the file path to the user
3. Say: *"Voici le rapport semaine XX en HTML — prêt à envoyer !"*

---

## Notes & edge cases

- If a section is missing from the MD (e.g. no RH section), skip that tab entirely and remove its nav button.
- If N/A appears in a table cell, render as `<td class="num" style="color:var(--muted)">N/A</td>`
- Negative CA values (like U-Services) → render the value as-is with `num-red`
- Week number: extract from filename (`rapport_hebdomadaire_semaine_XX.md`) or from report title
- For RAF: if "jours restants" isn't stated explicitly, compute from the period end date to month end
- Always use French number formatting: spaces as thousands separator, commas as decimal (e.g. `56 688 €`, `52,5 %`)