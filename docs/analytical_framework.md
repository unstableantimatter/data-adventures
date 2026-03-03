# Analytical Framework

The analytical brain of the pipeline. Defines what analysis runs, how findings
are surfaced, and how non-obvious relationships are explored.

---

## Three analysis layers

### Layer 1 — Automatic descriptive pass

Runs on every project automatically once processed data exists. No configuration
needed beyond having indicators defined in `config.yaml`.

| Analysis | What it does |
|----------|-------------|
| **Univariate profiles** | For each metric: distribution, min/max/median/mean, missing data %, outlier flags |
| **Time series trends** | Direction (rising/falling/flat), rate of change per decade, visual trend line |
| **Changepoint detection** | Sharp shifts in a metric's trajectory (via `ruptures`); reports year and magnitude |
| **Pairwise correlations** | Pearson and Spearman across all indicator pairs; flags pairs above configurable threshold (default \|r\| > 0.5) |
| **Geographic variation** | If data has state/district granularity: rank regions, identify outliers, produce heatmap-ready summaries |

**Output:** A descriptive report notebook (`01_descriptive.ipynb`) with tables
and interactive Plotly charts. This is the "what does the data look like?"
baseline.

### Layer 2 — Flagging engine

Runs after Layer 1. Scores and ranks findings to surface what's worth
investigating.

| Flag type | What it surfaces |
|-----------|-----------------|
| **Correlation flags** | Pairs with strong correlation, sorted by strength. Each gets a one-liner summary with r-value, p-value, and trend direction. |
| **Changepoint clusters** | Multiple metrics that shifted sharply around the same year — potential shared cause or policy event. |
| **Divergence flags** | Metrics that moved in opposite directions (e.g., immigration up while a QoL metric declined). Directly tests narrative hypotheses. |
| **Outlier regions** | States/districts that break the overall pattern — either supporting or contradicting the hypothesis. |

**Output:** A findings summary (`02_findings.ipynb` or `findings.md`) — a
ranked list of flagged findings, each with:

- Short description
- Strength indicator (strong / moderate / weak)
- Suggested next step (deep-dive type, narrative pattern to apply)
- Suggested LLM interpretation prompt

The human reviews this and marks which findings to pursue in Layer 3.

### Layer 3 — Directed deep-dives

Human-selected from Layer 2 output. The pipeline has reusable templates for
each type of deep-dive.

| Deep-dive type | What it does |
|----------------|-------------|
| **Regression** | Does Metric A predict Metric B after controlling for confounders? (OLS, multiple regression via `statsmodels`) |
| **Lag analysis** | Does a change in X precede a change in Y by N years? (Cross-correlation, Granger-style tests) |
| **Segmented comparison** | Compare high-X vs. low-X regions on outcome metrics (e.g., high-immigration vs. low-immigration districts on QoL) |
| **Before/after analysis** | Pick an event year or policy change; compare metrics before vs. after |
| **Narrative threading** | Given a set of confirmed findings, assemble them into a coherent narrative arc with supporting charts |

**Output:** One deep-dive notebook per selected finding, plus an updated
findings summary with confirmed/rejected status.

---

## Flexible indicator schema

Indicators are defined per project in `config.yaml`. The schema is open-ended —
new categories and variables can be added at any time without restructuring the
pipeline or existing data.

### Indicator definition format

```yaml
indicators:
  - name: median_household_income
    category: economic
    source: census_acs
    time_range: "1990-2024"
    geo_level: county
    direction_of_good: higher
    tags: [income, wealth]

  - name: military_recruitment_rate
    category: military
    source: dod_manpower
    time_range: "2000-2024"
    geo_level: state
    direction_of_good: null  # neutral — context-dependent
    tags: [employment, military]
```

### Rules

- **Categories are freeform strings.** There is no fixed list. Use whatever
  makes sense for the project: "economic", "health", "military", "political",
  "immigration", etc.
- **New indicators can be added mid-study.** Add a new entry to `config.yaml`,
  place the raw data in `data/raw/`, and re-run the pipeline. Layer 1 will
  automatically include the new indicator in its descriptive pass and
  correlation matrix.
- **`direction_of_good`** tells the pipeline whether higher values are
  "better" (e.g., income), "worse" (e.g., crime rate), or `null` (neutral /
  context-dependent). Used for divergence flag interpretation.
- **`tags`** are optional freeform labels for grouping and filtering.

---

## Custom hypothesis definitions

Each project can define specific relationships to test in `config.yaml`. These
go beyond standard correlations — they express a mechanism or narrative claim
that the pipeline should evaluate.

### Hypothesis definition format

```yaml
hypotheses:
  - name: "Military recruitment masks unemployment"
    pattern: masking
    hidden_variable: military_recruitment_rate
    surface_variable: unemployment_rate
    expected: >
      Periods of high recruitment coincide with lower reported unemployment,
      but underlying job quality (wages, benefits) does not improve.
    indicators: [military_recruitment_rate, unemployment_rate, median_wages, benefits_coverage]

  - name: "Immigration concentrated in swing districts"
    pattern: segmentation
    segment_variable: partisan_lean
    outcome_variable: foreign_born_share_change
    expected: >
      Foreign-born population growth is disproportionately concentrated
      in politically competitive districts.
    indicators: [foreign_born_share, partisan_lean_pvi, district_competitiveness]
```

### How hypotheses are tested

1. The pipeline reads the `hypotheses` section from `config.yaml`.
2. For each hypothesis, it identifies the matching **narrative reframing
   pattern** (see below) and applies the pattern's test template.
3. Results are included in the Layer 2 findings summary alongside the
   automated flags.
4. Deep-thinking LLM interprets the results in context (via Cursor session).

---

## Narrative reframing patterns

A library of reusable analytical lenses. Each pattern has a definition, a
statistical test approach, and a visualization template. The library is
extensible — new patterns are added as they are discovered across studies.

### Masking

**Question:** Does variable C absorb or hide the real effect of A on B?

**Example:** Military recruitment absorbing unemployment — the headline
unemployment number looks fine, but the mechanism is people entering the
military rather than finding civilian jobs.

**Test approach:**
- Correlate A and B with and without controlling for C.
- Compare time periods where C is high vs. low.
- Check if removing C's effect changes the A–B relationship significantly.

**Visualization:** Dual-axis chart showing A and B over time, with C overlaid;
scatter plot of A vs. B colored by C level.

### Displacement

**Question:** Did a change in X push people/resources from one bucket to
another rather than improving outcomes?

**Example:** A policy reduces homelessness in one city, but neighboring cities
see an increase of the same magnitude.

**Test approach:**
- Sum across buckets to check if the total is unchanged.
- Compare the "winner" region with "loser" regions on the same metric.
- Time-align the shifts.

**Visualization:** Stacked area chart showing bucket composition over time;
before/after comparison across regions.

### Divergence

**Question:** Two metrics that should move together are moving apart — what
changed?

**Example:** GDP is rising but median household income is flat or declining.

**Test approach:**
- Compute the ratio or difference between the two metrics over time.
- Identify the inflection point where they diverge.
- Look for a third variable that correlates with the divergence onset.

**Visualization:** Normalized dual-line chart (indexed to a base year);
divergence gap highlighted.

### Lag / lead

**Question:** Does a change in X precede a change in Y by N years?

**Example:** Immigration policy changes in year T correlate with QoL shifts
in year T+5.

**Test approach:**
- Cross-correlation at multiple lag values.
- Granger causality test (does past X improve prediction of Y?).
- Visual alignment of shifted time series.

**Visualization:** Cross-correlation bar chart; overlaid time series with
optimal lag applied.

### Segmentation

**Question:** Does the relationship between A and B only hold in certain
regions, demographics, or time periods?

**Example:** Immigration correlates with QoL decline only in districts with
specific economic characteristics.

**Test approach:**
- Split data by segment variable (e.g., urban/rural, income quartile,
  partisan lean).
- Run the A–B analysis separately for each segment.
- Compare effect sizes and significance across segments.

**Visualization:** Small multiples (one chart per segment); forest plot of
effect sizes.

### Threshold

**Question:** Is there a tipping point where the relationship between A and
B changes character?

**Example:** Low levels of immigration correlate with QoL improvement, but
above a certain rate the relationship reverses.

**Test approach:**
- Piecewise linear regression (find breakpoints).
- Binned analysis (divide X into quantiles, plot mean Y per bin).
- Compare slopes before and after candidate thresholds.

**Visualization:** Scatter plot with piecewise regression line; bin-averaged
step chart.

---

## Adding new patterns

When a study reveals a new type of non-obvious relationship:

1. Give it a name and a one-sentence question.
2. Define the test approach (what statistical methods to apply).
3. Define the visualization template.
4. Add it to this document and to the pipeline's pattern library.
5. It becomes available for all future projects via `config.yaml` hypothesis
   definitions.
