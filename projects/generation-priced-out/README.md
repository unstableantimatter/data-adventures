# Generation Priced Out — Project Notes

## Narrative hypothesis

A 30-year-old today lives a fundamentally different life than a 30-year-old in
1983. Independent living, marriage, homeownership, and having children have all
collapsed for young adults over four decades. Meanwhile, several countries show
the inverse pattern — rising fertility, growing young-adult homeownership, and
expanding populations. This study proves the divergence with public data and
names the countries going the other direction.

## Status

**Phase:** 1 — Find (data source identification and acquisition)

## Core claims to validate

| Claim | 1983 (stated) | Today (stated) | Age bracket | Source |
|---|---|---|---|---|
| Living independently | ~85% | ~64% | 25-34 or 30-34 | Census CPS AD-1 |
| Married | ~80% | ~47% | 30-34 | Census CPS MS-2 |
| Homeowner | ~50% | ~32% | Under 35 | Census HVS Table 14 |
| TFR (population proxy) | ~1.8 | ~1.6 | All women 15-49 | CDC / World Bank |

> Where the data diverges from the stated numbers, we report the data.

## Data catalog

| Name | Category | Source URL | Description | Format | License | Time range | Geo | Tags | Script |
|------|----------|-----------|-------------|--------|---------|------------|-----|------|--------|
| census_cps_living | household | Census CPS AD-1 | Young adults living at home (18-34) | documented | public_domain | 1960-2023 | national | living, independence | fetch_data.py |
| census_cps_marital | household | Census CPS MS-2 | Marital status by age | documented | public_domain | 1950-2023 | national | marriage, family | fetch_data.py |
| census_hvs | economic | Census HVS Table 14 | Homeownership by age | documented | public_domain | 1982-2023 | national | homeownership | fetch_data.py |
| world_bank_fred_tfr | demographic | FRED SPDYNTFRTINUSA | US Total Fertility Rate | CSV | public_domain | 1960-2022 | national | fertility | fetch_data.py |
| fred_MSPUS | economic | FRED | Median Sales Price of Houses Sold | CSV | public_domain | 1963-2023 | national | housing, price | fetch_data.py |
| fred_MEHOINUSA646N | economic | FRED | Median Household Income (nominal) | CSV | public_domain | 1984-2023 | national | income | fetch_data.py |
| fred_MORTGAGE30US | economic | FRED | 30-Year Fixed Mortgage Rate | CSV | public_domain | 1971-2023 | national | mortgage | fetch_data.py |
| fred_CPIAUCSL | economic | FRED/BLS | CPI-U (All Urban Consumers) | CSV | public_domain | 1947-2023 | national | inflation, CPI | fetch_data.py |
| fred_CUSR0000SAH1 | economic | FRED/BLS | CPI: Shelter component | CSV | public_domain | 1947-2023 | national | inflation, shelter | fetch_data.py |
| fred_COMPSFLAM1FQ | economic | FRED/Census | Median sqft, new single-family | CSV | public_domain | 1978-2023 | national | housing, size | fetch_data.py |
| census_lot_size | economic | Census SOC / Fed | Median lot size, new homes | documented | public_domain | 1978-2022 | national | land, lot size | fetch_data.py |
| world_bank_intl | demographic | World Bank API | TFR + pop growth + GDP/cap growth | JSON | public_domain | 1960-2022 | country | intl, fertility | fetch_data.py |

## Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-04 | Age bracket 25-34 for CPS, Under 35 for HVS | Matches closest available Census published tables |
| 2026-03-04 | Use World Bank API for international comparison | Broadest country coverage, free, no API key |
| 2026-03-04 | Report data as-is, not the stated claim numbers | Academic defensibility requires citing the source, not the narrative |
