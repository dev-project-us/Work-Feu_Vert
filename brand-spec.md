# Feu Vert Brand Spec — Dark Dashboard Variant

Based on tech-utility direction (Datadog/GitHub) with Feu Vert's signature lime green accent.

## Color Tokens

```css
:root {
  /* Dark surfaces — tech-utility base inverted for dark mode */
  --bg:      oklch(15% 0.015 240);   /* near-black with slight cool tint */
  --surface: oklch(20% 0.012 240);   /* card/panel background */
  --border:  oklch(30% 0.010 240);   /* subtle borders */
  
  /* Text */
  --fg:      oklch(95% 0.005 240);   /* primary text — near white */
  --muted:   oklch(65% 0.010 240);   /* secondary text */
  
  /* Feu Vert accent — their signature lime green */
  --accent:  oklch(72% 0.20 130);    /* ~#78BE20 Feu Vert green */
  --accent-dim: oklch(55% 0.15 130); /* muted green for backgrounds */
  
  /* Semantic */
  --positive: oklch(72% 0.20 130);   /* green — same as accent */
  --negative: oklch(65% 0.20 25);    /* red for negative deltas */
  --warning:  oklch(75% 0.18 85);    /* amber */
}
```

## Typography

```css
:root {
  --font-display: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif;
  --font-body:    -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', system-ui, sans-serif;
  --font-mono:    'JetBrains Mono', 'IBM Plex Mono', ui-monospace, Menlo, monospace;
}
```

## Layout Posture

- Sans display + sans body (one family) — utility trumps editorial
- Tabular numerics everywhere: `font-variant-numeric: tabular-nums`
- Mono for KPIs, metrics, timestamps, IDs
- Dense tables with hairline borders, no row striping
- Inline status pills with restrained tinted backgrounds
- No hero images or marketing copy — show the data
- Cards use 1px solid borders, no shadows
- Border radius: 4–6px (subtle, not rounded)

## Accent Discipline

- Feu Vert green used for: positive deltas, sparklines, primary KPIs
- Red used only for negative deltas
- Accent never used on large surfaces — small pips, lines, text highlights only
