# Data Catalog — Template

Each project maintains its own data catalog as a table in this format. Copy this
template into the project's `README.md` or a dedicated `data_catalog.md` inside
the project directory.

---

## Catalog format

| Name | Category | Source URL | Description | Format | License | Time range | Geo granularity | Direction of good | Tags | Ingestion script |
|------|----------|-----------|-------------|--------|---------|------------|-----------------|-------------------|------|-----------------|
| *example:* median_household_income | economic | https://data.census.gov/... | Median household income from ACS 5-year estimates | CSV | Public domain | 1990–2024 | County | Higher | income, wealth | `pipeline/ingest.py` |

### Column definitions

- **Name:** Machine-readable indicator name (snake_case). Must match the
  indicator name in `config.yaml`.
- **Category:** Freeform category string (e.g., economic, health, immigration,
  military, political). Must match `config.yaml`.
- **Source URL:** Direct link to the dataset or its landing page.
- **Description:** One-sentence description of what the data measures.
- **Format:** File format of the raw download (CSV, JSON, Excel, API, etc.).
- **License:** Data license or terms of use (Public domain, CC-BY, etc.).
- **Time range:** Years covered by the dataset.
- **Geo granularity:** Geographic level (national, state, county, district,
  city, zip code, etc.).
- **Direction of good:** Whether higher values are "better" (e.g., income),
  "worse" (e.g., crime rate), or "neutral" (context-dependent).
- **Tags:** Freeform labels for grouping and filtering.
- **Ingestion script:** Which pipeline script handles downloading/importing
  this data.

### Usage

1. During **Phase 1 (Find)**, populate this catalog as data sources are
   identified and approved.
2. During **Phase 2 (Study & Coalesce)**, update with actual schemas, row
   counts, and any quality notes discovered during cleaning.
3. Keep current throughout the study — if a source is dropped or replaced,
   note the change here and in `docs/decisions.md`.
