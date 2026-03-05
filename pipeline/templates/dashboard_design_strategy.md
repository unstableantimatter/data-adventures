# Dashboard Design Strategy

Reference guide for presenting data in dashboards and reports. Based on patterns
from Pew Research Center, Our World in Data, NYT Upshot, Urban Institute, and
OECD housing dashboards.

Applies to all projects in the pipeline. Every dashboard should be visually
indistinguishable in style — only the content changes.

## Visual System

### Theme
Dark background (`#0b0f1a`), neutral card surfaces, single-weight border
(`rgba(255,255,255,0.06)`). No gradients, no glows, no colored backgrounds
on containers. Color is reserved for data (chart lines, headline numbers).

### Typography
Inter (400/500/600/700). Hierarchy through weight and size, not decoration.
Section headings in white, body text in `--muted` (#94a3b8), tertiary in
`--dim` (#64748b). No all-caps except small section labels.

### Color Palette
A fixed 5-color palette used consistently across every chart and stat:
- Rose `#f43f5e` — primary accent, declines, warnings
- Amber `#f59e0b` — secondary warm
- Sky `#38bdf8` — cool informational
- Emerald `#34d399` — positive, historical, international
- Violet `#a78bfa` — highlight (e.g., US marker in international charts)

Muted slate (`#94a3b8`) for past/historical values. White for present values.

### Iconography
Google Material Symbols Outlined via CDN. Loaded alongside Inter from
Google Fonts — zero additional dependencies.

```html
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL@20,400,0" rel="stylesheet" />
```

Rules:
- Icons carry meaning, never decoration. Every icon must convey information
  the viewer cannot get from the text alone.
- Color follows the palette — icons inherit data color, not arbitrary color.
- Weight 400–500, optical size 20. Consistent across all dashboards.
- Standard icon vocabulary:
  - `trending_up` / `trending_down` — directional indicators in scorecards
  - `arrow_upward` / `arrow_downward` — magnitude emphasis
  - `info` — supplementary context cues
  - `open_in_new` — external source links

### Borders and Surfaces
One border weight everywhere: `1px solid rgba(255,255,255,0.06)`.
Card backgrounds: `rgba(255,255,255,0.02)`.
Border radius: `8px` for all containers (charts, scorecards).
No box shadows, no colored borders.

## Core Principles

1. **Show raw numbers, not derived percentages.** If marriage went from 64% to
   38%, show "64% → 38%". Do not show "▼ 41%". The viewer's brain processes
   the comparison naturally.

2. **Express change in natural units.** Percentage-point metrics change in
   percentage points ("down 26 points"). Ratios change in their native unit
   ("from 3.6× to 5.3×"). Dollar figures change in dollars ("$80K → $427K").
   Never convert to relative percentage change.

3. **The prose narrates; the data proves.** Charts and tables present the
   evidence. Body text and section intros translate it into meaning.

4. **Minimal decoration.** No colored badges, pill indicators, gradient
   backgrounds, or colored card borders. Typography and whitespace do the
   work. The one exception: Material Symbols directional icons in scorecards
   and stat rows, where they convey trend direction at a glance.

5. **Limit chart complexity.** No more than 5 lines per chart. Use small
   multiples instead of cramming. One chart, one finding.

## Component Library

### Scorecard (hero comparison)
Clean table: metric name left, time-period columns right-aligned. Past values
muted, present values white. A narrow center column holds a Material Symbols
directional icon (`trending_up` / `trending_down`) colored to signal whether
the change is positive or negative for the viewer. No delta numbers — the
raw values tell the story, the icon shows direction at a glance.

### Section Header
Small numbered label (e.g., "01 — The Big Picture") in `--dim`, followed by
`h2` in white, then a `lead` paragraph in `--muted`. No colored section tags.

### Chart Card
`.chart` — subtle border, `8px` radius, `1rem` padding. Source citation below
the chart in `--dim` at `.65rem`. No additional decoration.

### Aside (metric briefs, insights, callouts)
`.aside` — left border (2px, `--border` color), left padding. Used for:
- Metric definitions ("Reading this chart", "What is CPI-Shelter?")
- Analytical insights ("Why CPI understates the housing crisis")
- Data-vs-claim notes
All use the same component. Title via `<h4>`, body in `--muted`.

### Stat Row
`.stats` grid of `.stat` items. Each has a large white number (`.stat-n`)
and a one-line description in `--muted`. The number may be colored to match
a chart line, but the container is never colored.

### Transition
Centered italic text in `--dim` linking sections. No anchor links, no arrows.
Brief — one sentence maximum.

## Narrative Flow

1. **Hero** — Title + scorecard + summary paragraph + neutral CTA button
2. **01 — The Big Picture** — Combined overlay, stats row
3. **02 — The Why** — Economic/structural deep-dive (housing, CPI, affordability)
4. **03 — The Details** — Individual metric small multiples
5. **04 — The World** — International context
6. **Methodology** — Sources, definitions, limitations

## Plotly Chart Styling

- `paper_bgcolor: rgba(0,0,0,0)`, `plot_bgcolor: rgba(255,255,255,0.02)`
- Grid: `rgba(255,255,255,0.06)`
- Font: Inter, `#e2e8f0`, size 11 for ticks, 15 for title
- Horizontal legend at top center, transparent background
- Line width: 2–3px. Markers: 4px where used.
- Hover: unified x-axis mode, dark tooltip

## Reference Dashboards

- **Pew Research Center**: Housing affordability, generational economics
  https://www.pewresearch.org/topic/income-wealth-poverty/homeownership-renting/
- **Our World in Data**: Economic indicators, clean single-variable charts
  https://ourworldindata.org/
- **NYT Upshot**: Concrete, human-scale comparisons
- **Urban Institute**: "Nine Charts about Wealth Inequality in America"
  https://apps.urban.org/features/wealth-inequality-charts/
- **OECD Affordable Housing Database**: Price-to-income, cost burden metrics
  https://www.oecd.org/en/data/datasets/oecd-affordable-housing-database.html
