# QoL vs. Immigration — Project Notes

## Narrative hypothesis

How politicians have sold out the American people and diluted their vote and
the American knowledge base by systematically immigrating susceptible
populations and strategically placing them in districts and cities so they can
ensure the USA never moves away from the 2-party political system — and how
this has contributed to a substantial drop in quality of living in this
country for the 98% of Americans who are not millionaire+ rich.

*The data work will either support, refine, or challenge this narrative.*

## Status

**Phase:** 1 — Find (data sources identified; data download pending)

## Data catalog

| Name | Category | Source | Format | Time range | Geo | Dir | Tags |
|------|----------|--------|--------|------------|-----|-----|------|
| median_household_income | economic | Census ACS | CSV | 1990–2024 | state | higher | income, wealth |
| real_median_weekly_earnings | economic | BLS CPS | CSV | 1990–2024 | national | higher | wages, labor |
| gini_coefficient | economic | FRED/Census | CSV | 1967–2024 | national | lower | inequality |
| poverty_rate | economic | Census SAIPE | CSV | 1990–2024 | state | lower | poverty |
| home_price_to_income_ratio | economic | Census/NAR/FHFA | CSV/Excel | 1998–2024 | state | lower | housing |
| life_expectancy | health | CDC WONDER | CSV | 1990–2023 | state | higher | health, mortality |
| high_school_graduation_rate | education | NCES CCD | Excel | 2005–2024 | state | higher | education |
| college_attainment_rate | education | Census ACS | CSV | 1990–2024 | state | higher | education |
| foreign_born_population_share | immigration | MPI/Census | CSV | 1990–2022 | state | null | immigration |
| lawful_permanent_residents | immigration | DHS Yearbook | Excel | 2002–2023 | state | null | immigration |
| refugee_arrivals | immigration | DHS Yearbook | Excel | 2002–2023 | state | null | refugee |
| voter_turnout | political | UF Elections | CSV/Excel | 1980–2024 | state | higher | political |
| cook_pvi | political | Cook Political | CSV | 1997–2025 | district | null | partisanship |
| noncitizen_apportionment_impact | political | CIS/Census | report | 1990–2020 | state | null | redistricting |

See [citations.md](citations.md) for full source URLs and referenced studies.

## Hypotheses to test

1. **Immigration concentrated in competitive districts** — foreign-born growth
   is disproportionately located in politically competitive or party-favorable
   districts. (Pattern: segmentation)
2. **QoL diverges from GDP as immigration rises** — states with higher
   immigration growth show greater divergence between GDP and median income.
   (Pattern: divergence)
3. **Immigration precedes QoL decline with lag** — increases in foreign-born
   share precede income stagnation by 5–10 years. (Pattern: lag/lead)
4. **Noncitizen populations shift congressional seats** — states gaining seats
   due to noncitizens shift partisan lean predictably. (Pattern: segmentation)
5. **Housing affordability collapses in high-immigration metros** — threshold
   of foreign-born share above which affordability deteriorates sharply.
   (Pattern: threshold)

## Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | 14 indicators across 5 categories (economic, health, education, immigration, political) | Covers the major dimensions of the narrative hypothesis |
| 2026-03-02 | State-level as primary geographic unit; district-level for political indicators | Best balance of data availability and analytical granularity |
| 2026-03-02 | 5 custom hypotheses defined using narrative reframing patterns | Tests the specific mechanisms in the narrative, not just correlations |
| 2026-03-02 | 29 citations cataloged (17 data sources, 12 studies/papers) | Both pro and contra perspectives on immigration/wages included for rigor |

## Next steps

- [ ] Download raw data files for each source into `data/raw/`
- [ ] Run `python run.py qol-immigration --stage data` to process
- [ ] Advance to Phase 2 (Study & coalesce)
