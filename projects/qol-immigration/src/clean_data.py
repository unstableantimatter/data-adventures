"""Project-specific data cleaning for the QoL vs Immigration study.

Standards applied to every output Parquet file:

- **Tidy format** — one observation per row.
- **Column naming** — ``lowercase_snake_case``.
- **Geographic IDs** — ``state_fips`` (zero-padded 2-digit str),
  ``state_name``, ``state_abbr``.  All 50 states + DC; Puerto Rico and
  territories excluded for panel consistency.
- **Time** — ``year`` (int); quarterly data also has ``quarter`` (int 1-4).
- **Data types** — measurements as float64, identifiers as str.
- **Missing values** — ``NaN`` only (no placeholder strings).
- **Sort order** — ``year``, then ``state_fips`` (or ``district_number``).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from pipeline.config import get_data_raw_dir, get_data_processed_dir
from pipeline.geo import (
    ABBR_TO_FIPS,
    NAME_TO_FIPS,
    VALID_STATE_FIPS,
    add_state_ids,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SENTINELS = frozenset({"N", "(X)", "-", "---", "‡", "(L)", "(NA)", "nan", ""})


def _to_float(val, extra_sentinels: frozenset[str] | None = None) -> float:
    """Convert a messy cell value to float, treating sentinels as NaN."""
    if pd.isna(val):
        return float("nan")
    val = str(val).strip()
    if val in _SENTINELS or (extra_sentinels and val in extra_sentinels):
        return float("nan")
    # Strip footnote markers like \12\ or trailing superscript digits
    val = re.sub(r"\\+\d+\\*", "", val).strip()
    # Blurred values (NCES privacy): =90 → 90
    if val.startswith("="):
        val = val[1:]
    val = val.replace("%", "").replace("$", "").replace(",", "").strip()
    if not val:
        return float("nan")
    try:
        return float(val)
    except ValueError:
        return float("nan")


def _report(path: Path, df: pd.DataFrame) -> None:
    print(f"  [clean] → {path.name}  ({len(df):,} rows × {len(df.columns)} cols)")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(config: dict) -> list[Path]:
    """Clean all raw files and write standardised Parquet to data/processed/."""
    raw = get_data_raw_dir(config)
    out = get_data_processed_dir(config)
    out.mkdir(parents=True, exist_ok=True)

    outputs: list[Path] = []

    # ACS state-level (already tidy)
    outputs += _clean_acs_median_income(raw, out)
    outputs += _clean_acs_poverty(raw, out)
    outputs += _clean_acs_college(raw, out)
    outputs += _clean_acs_foreign_born(raw, out)

    # FRED / BLS national-level
    outputs += _clean_fred_gini(raw, out)
    outputs += _clean_fred_median_income(raw, out)
    outputs += _clean_fred_poverty(raw, out)
    outputs += _clean_bls_earnings(raw, out)

    # State-level economic
    outputs += _clean_bea_gdp(raw, out)
    outputs += _clean_fhfa_hpi(raw, out)

    # Health
    outputs += _clean_cdc_life_expectancy(raw, out)

    # Immigration
    outputs += _clean_dhs_immigration(raw, out)

    # Education
    outputs += _clean_nces_graduation(raw, out)

    # Political
    outputs += _clean_census_voting(raw, out)
    outputs += _clean_cook_pvi(raw, out)
    outputs += _clean_cis_noncitizen(raw, out)

    print(f"\n  [clean] Wrote {len(outputs)} processed file(s) to {out}")
    return outputs


# ── ACS files ────────────────────────────────────────────────────────────────

def _standardise_acs(df: pd.DataFrame) -> pd.DataFrame:
    """Common post-processing for ACS downloads."""
    df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    df = df[df["state_fips"].isin(VALID_STATE_FIPS)].copy()
    df = add_state_ids(df, "state_fips", "fips")
    df["year"] = df["year"].astype(int)
    return df.sort_values(["year", "state_fips"]).reset_index(drop=True)


def _clean_acs_median_income(raw: Path, out: Path) -> list[Path]:
    p = raw / "acs_median_income_by_state.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p)
    df = _standardise_acs(df)
    df["median_household_income"] = pd.to_numeric(
        df["median_household_income"], errors="coerce"
    )
    df = df[["year", "state_fips", "state_name", "state_abbr",
             "median_household_income"]]
    o = out / "acs_median_income.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


def _clean_acs_poverty(raw: Path, out: Path) -> list[Path]:
    p = raw / "acs_poverty_rate_by_state.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p)
    df = _standardise_acs(df)
    df["poverty_pct"] = pd.to_numeric(df["poverty_pct"], errors="coerce")
    df = df[["year", "state_fips", "state_name", "state_abbr", "poverty_pct"]]
    o = out / "acs_poverty_rate.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


def _clean_acs_college(raw: Path, out: Path) -> list[Path]:
    p = raw / "acs_college_attainment_by_state.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p)
    df = _standardise_acs(df)
    for c in ("pop_25plus", "bachelors_or_higher", "bachelors_pct"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[["year", "state_fips", "state_name", "state_abbr",
             "pop_25plus", "bachelors_or_higher", "bachelors_pct"]]
    o = out / "acs_college_attainment.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


def _clean_acs_foreign_born(raw: Path, out: Path) -> list[Path]:
    p = raw / "acs_foreign_born_by_state.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p)
    df = _standardise_acs(df)
    for c in ("total_pop", "foreign_born", "foreign_born_pct"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[["year", "state_fips", "state_name", "state_abbr",
             "total_pop", "foreign_born", "foreign_born_pct"]]
    o = out / "acs_foreign_born.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


# ── FRED / BLS national-level ───────────────────────────────────────────────

def _fred_year(date_str: str) -> int:
    return int(str(date_str)[:4])


def _clean_fred_gini(raw: Path, out: Path) -> list[Path]:
    p = raw / "gini_coefficient_usa.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p)
    df["year"] = df["observation_date"].apply(_fred_year)
    df["gini_coefficient"] = pd.to_numeric(df["GINIALLRF"], errors="coerce")
    df = df[["year", "gini_coefficient"]].sort_values("year").reset_index(drop=True)
    o = out / "fred_gini.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


def _clean_fred_median_income(raw: Path, out: Path) -> list[Path]:
    p = raw / "median_household_income_usa.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p)
    df["year"] = df["observation_date"].apply(_fred_year)
    df["median_household_income_real"] = pd.to_numeric(
        df["MEHOINUSA672N"], errors="coerce"
    )
    df = df[["year", "median_household_income_real"]].sort_values("year").reset_index(drop=True)
    o = out / "fred_median_income_national.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


def _clean_fred_poverty(raw: Path, out: Path) -> list[Path]:
    p = raw / "poverty_rate_usa.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p)
    df["year"] = df["observation_date"].apply(_fred_year)
    df["poverty_rate"] = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    df = df[["year", "poverty_rate"]].dropna(subset=["poverty_rate"])
    df = df.sort_values("year").reset_index(drop=True)
    o = out / "fred_poverty_rate_national.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


def _clean_bls_earnings(raw: Path, out: Path) -> list[Path]:
    p = raw / "bls_median_weekly_earnings.csv"
    if not p.exists():
        return []
    df = pd.read_csv(p, dtype=str)
    df["year"] = df["year"].astype(int)
    df["quarter"] = df["quarter"].astype(int)
    df["median_weekly_earnings_real"] = df["value"].apply(
        lambda v: _to_float(v, frozenset({"-"}))
    )
    df = df[["year", "quarter", "median_weekly_earnings_real"]]
    df = df.dropna(subset=["median_weekly_earnings_real"])
    df = df.sort_values(["year", "quarter"]).reset_index(drop=True)
    o = out / "bls_weekly_earnings.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


# ── BEA state GDP ───────────────────────────────────────────────────────────

def _clean_bea_gdp(raw: Path, out: Path) -> list[Path]:
    p = raw / "SAGDP1__ALL_AREAS_1997_2024.csv"
    if not p.exists():
        return []

    df = pd.read_csv(p, dtype=str)

    # GeoFIPS comes as ' "01000"' — clean to "01"
    df["state_fips"] = (
        df["GeoFIPS"]
        .str.strip()
        .str.strip('"')
        .str.strip()
        .str[:2]
    )
    df = df[df["state_fips"].isin(VALID_STATE_FIPS)].copy()

    df["LineCode"] = pd.to_numeric(df["LineCode"], errors="coerce")
    measures = {
        1: "real_gdp_millions",
        3: "current_dollar_gdp_millions",
        4: "compensation_millions",
    }
    df = df[df["LineCode"].isin(measures)]

    year_cols = [c for c in df.columns if re.fullmatch(r"\d{4}", c)]

    long = df.melt(
        id_vars=["state_fips", "LineCode"],
        value_vars=year_cols,
        var_name="year",
        value_name="value",
    )
    long["year"] = long["year"].astype(int)
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long["measure"] = long["LineCode"].map(measures)

    wide = (
        long.pivot_table(index=["state_fips", "year"], columns="measure", values="value")
        .reset_index()
    )
    wide.columns.name = None

    wide = add_state_ids(wide, "state_fips", "fips")
    cols = ["year", "state_fips", "state_name", "state_abbr"] + list(measures.values())
    wide = wide[cols].sort_values(["year", "state_fips"]).reset_index(drop=True)

    o = out / "bea_state_gdp.parquet"
    wide.to_parquet(o, index=False)
    _report(o, wide)
    return [o]


# ── FHFA House Price Index ──────────────────────────────────────────────────

def _clean_fhfa_hpi(raw: Path, out: Path) -> list[Path]:
    p = raw / "fhfa_hpi_state.txt"
    if not p.exists():
        return []

    df = pd.read_csv(
        p, sep="\t", header=None,
        names=["state_abbr", "year", "quarter", "hpi"],
    )
    df["state_abbr"] = df["state_abbr"].str.strip()
    df = add_state_ids(df, "state_abbr", "abbr")
    df = df.dropna(subset=["state_fips"])

    df["year"] = df["year"].astype(int)
    df["quarter"] = df["quarter"].astype(int)
    df["hpi"] = pd.to_numeric(df["hpi"], errors="coerce")

    cols = ["year", "quarter", "state_fips", "state_name", "state_abbr", "hpi"]
    df = df[cols].sort_values(["year", "quarter", "state_fips"]).reset_index(drop=True)

    o = out / "fhfa_hpi.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


# ── CDC life expectancy ─────────────────────────────────────────────────────

def _clean_cdc_life_expectancy(raw: Path, out: Path) -> list[Path]:
    p = raw / "cdc_state_life_expectancy.csv"
    if not p.exists():
        return []

    df = pd.read_csv(p)
    df.columns = [c.lower().strip() for c in df.columns]
    df.rename(columns={"life_expectancy": "life_expectancy", "se": "se"}, inplace=True)
    df["state_fips"] = df["state"].str.strip().map(NAME_TO_FIPS)
    df = df.dropna(subset=["state_fips"])
    df = add_state_ids(df, "state_fips", "fips")

    df["year"] = df["year"].astype(int)
    df["life_expectancy"] = pd.to_numeric(df["life_expectancy"], errors="coerce")
    df["se"] = pd.to_numeric(df["se"], errors="coerce")

    cols = ["year", "state_fips", "state_name", "state_abbr",
            "sex", "life_expectancy", "se"]
    df = df[cols].sort_values(["year", "state_fips", "sex"]).reset_index(drop=True)

    o = out / "cdc_life_expectancy.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


# ── DHS state immigration ───────────────────────────────────────────────────

def _clean_dhs_immigration(raw: Path, out: Path) -> list[Path]:
    p = raw / "dhs_state_immigration.csv"
    if not p.exists():
        return []

    df = pd.read_csv(p)
    df["state_fips"] = df["State"].str.strip().map(NAME_TO_FIPS)
    df = df.dropna(subset=["state_fips"])
    df = add_state_ids(df, "state_fips", "fips")

    keep = {
        "Year": "year",
        "Population": "population",
        "Lawful Permanent Residents Total": "lpr_total",
        "New Arrivals Total": "new_arrivals_total",
        "Naturalizations Total": "naturalizations_total",
        "Refugees Total": "refugees_total",
        "Asylees Total": "asylees_total",
        "Nonimmigrants Total": "nonimmigrants_total",
        "Lawful Permanent Residents Per Million": "lpr_per_million",
        "Refugees Per Million": "refugees_per_million",
        "Asylees Per Million": "asylees_per_million",
    }
    rename_map = {k: v for k, v in keep.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    numeric_cols = [c for c in rename_map.values() if c != "year"]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["year"] = df["year"].astype(int)

    cols = (["year", "state_fips", "state_name", "state_abbr"]
            + [c for c in rename_map.values() if c != "year" and c in df.columns])
    df = df[cols].sort_values(["year", "state_fips"]).reset_index(drop=True)

    o = out / "dhs_immigration.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


# ── NCES graduation rates ───────────────────────────────────────────────────

def _clean_nces_graduation(raw: Path, out: Path) -> list[Path]:
    p = raw / "nces_graduation_rates_by_state.xlsx"
    if not p.exists():
        return []

    df_raw = pd.read_excel(p, header=None, dtype=str)

    # School-year ending → calendar year (graduation year)
    grad_years = list(range(2012, 2023))  # 11 school years 2011-12 .. 2021-22

    # Data starts after the multi-row header; find first state row
    data_start = None
    for i in range(len(df_raw)):
        cell = str(df_raw.iloc[i, 0]).strip()
        cleaned = re.sub(r"\\?\d+\\?$", "", cell).strip()
        if cleaned in NAME_TO_FIPS:
            data_start = i
            break

    if data_start is None:
        # Try matching "United States" which appears before state rows
        for i in range(len(df_raw)):
            if "United States" in str(df_raw.iloc[i, 0]):
                data_start = i
                break

    if data_start is None:
        print("  [clean] NCES: could not locate data rows")
        return []

    records: list[dict] = []
    for i in range(data_start, len(df_raw)):
        raw_name = str(df_raw.iloc[i, 0]).strip()
        if pd.isna(df_raw.iloc[i, 0]) or raw_name == "nan":
            continue

        state_clean = re.sub(r"\\?\d+\\?$", "", raw_name).strip()
        fips = NAME_TO_FIPS.get(state_clean)
        if fips is None:
            # Also try stripping trailing digits without backslashes
            state_clean2 = re.sub(r"\d+$", "", raw_name).strip()
            fips = NAME_TO_FIPS.get(state_clean2)
        if fips is None:
            continue

        for col_offset, year in enumerate(grad_years):
            col_idx = col_offset + 1  # column 0 is state name
            if col_idx >= len(df_raw.columns):
                break
            records.append({
                "year": year,
                "state_fips": fips,
                "acgr_total": _to_float(df_raw.iloc[i, col_idx]),
            })

    df = pd.DataFrame(records)
    df = add_state_ids(df, "state_fips", "fips")
    df = df[["year", "state_fips", "state_name", "state_abbr", "acgr_total"]]
    df = df.sort_values(["year", "state_fips"]).reset_index(drop=True)

    o = out / "nces_graduation.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


# ── Census voter registration ───────────────────────────────────────────────

# Table A-5b: Registration rates by state for presidential elections.
# 27 columns: state + 26 data columns.
# 1972 and 1976 have Total only; 1980-2024 have Total + Citizen pairs.
_VOTING_COL_MAP: list[tuple[int, int, str]] = [
    (1, 1972, "total"),
    (2, 1976, "total"),
    (3, 1980, "total"),   (4, 1980, "citizen"),
    (5, 1984, "total"),   (6, 1984, "citizen"),
    (7, 1988, "total"),   (8, 1988, "citizen"),
    (9, 1992, "total"),   (10, 1992, "citizen"),
    (11, 1996, "total"),  (12, 1996, "citizen"),
    (13, 2000, "total"),  (14, 2000, "citizen"),
    (15, 2004, "total"),  (16, 2004, "citizen"),
    (17, 2008, "total"),  (18, 2008, "citizen"),
    (19, 2012, "total"),  (20, 2012, "citizen"),
    (21, 2016, "total"),  (22, 2016, "citizen"),
    (23, 2020, "total"),  (24, 2020, "citizen"),
    (25, 2024, "total"),  (26, 2024, "citizen"),
]


def _clean_census_voting(raw: Path, out: Path) -> list[Path]:
    p = raw / "census_voting_by_state.xlsx"
    if not p.exists():
        return []

    df_raw = pd.read_excel(p, header=None, dtype=str)

    # Locate first state data row
    data_start = None
    for i in range(len(df_raw)):
        cell = str(df_raw.iloc[i, 0]).strip()
        if cell in NAME_TO_FIPS:
            data_start = i
            break

    if data_start is None:
        print("  [clean] Census voting: could not locate data rows")
        return []

    records: list[dict] = []
    for i in range(data_start, len(df_raw)):
        state_raw = str(df_raw.iloc[i, 0]).strip()
        fips = NAME_TO_FIPS.get(state_raw)
        if fips is None:
            break  # hit footnotes

        year_bucket: dict[int, dict] = {}
        for col_idx, year, rate_type in _VOTING_COL_MAP:
            if col_idx >= len(df_raw.columns):
                continue
            if year not in year_bucket:
                year_bucket[year] = {"year": year, "state_fips": fips}
            val = _to_float(df_raw.iloc[i, col_idx])
            year_bucket[year][f"voter_reg_{rate_type}_pct"] = val

        records.extend(year_bucket.values())

    df = pd.DataFrame(records)
    df = add_state_ids(df, "state_fips", "fips")

    for c in ("voter_reg_total_pct", "voter_reg_citizen_pct"):
        if c not in df.columns:
            df[c] = float("nan")

    df = df[["year", "state_fips", "state_name", "state_abbr",
             "voter_reg_total_pct", "voter_reg_citizen_pct"]]
    df = df.sort_values(["year", "state_fips"]).reset_index(drop=True)

    o = out / "census_voter_registration.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


# ── Cook PVI ────────────────────────────────────────────────────────────────

def _parse_pvi(val: str) -> float:
    """Convert 'R+15' / 'D+7' / 'EVEN' to a numeric score.

    Convention: positive = Dem lean, negative = Rep lean, 0 = even.
    """
    if pd.isna(val):
        return float("nan")
    val = val.strip().upper()
    if val in ("EVEN", "0"):
        return 0.0
    m = re.match(r"([RD])\+(\d+\.?\d*)", val)
    if m:
        sign = 1.0 if m.group(1) == "D" else -1.0
        return sign * float(m.group(2))
    return float("nan")


def _clean_cook_pvi(raw: Path, out: Path) -> list[Path]:
    p = raw / "cook_pvi_by_district.csv"
    if not p.exists():
        return []

    df = pd.read_csv(p, dtype=str)

    # Drop "Sources:" footer row
    df = df[
        df["District"].notna()
        & ~df["District"].str.lower().str.startswith("source")
    ].copy()

    df["state_abbr"] = df["District"].str.split("-").str[0]
    df["district_number"] = pd.to_numeric(
        df["District"].str.split("-").str[1], errors="coerce"
    ).astype("Int64")
    df["district_label"] = df["District"]

    df["cook_pvi_raw"] = df.get("Cook PVI", pd.Series(dtype=str))
    df["cook_pvi_numeric"] = df["cook_pvi_raw"].apply(_parse_pvi)

    # Parse all percentage / currency string columns to numeric
    for col in df.columns:
        if col in ("District", "Incumbent", "Party", "Density Index",
                    "state_abbr", "district_label", "cook_pvi_raw",
                    "cook_pvi_numeric", "district_number"):
            continue
        df[col] = df[col].apply(lambda v: _to_float(v))

    # Rename select columns to snake_case
    rename = {
        "Party": "party_incumbent",
        "Density Index": "density_index",
        "FiveThirtyEight Elasticity": "fte_elasticity",
        "Non-Hispanic White CVAP": "white_cvap_pct",
        "Black CVAP": "black_cvap_pct",
        "Hispanic CVAP": "hispanic_cvap_pct",
        "Asian CVAP": "asian_cvap_pct",
        "Median Household Income": "median_household_income",
        "% Bachelor's Degree or Higher (25+ Pop.)": "bachelors_pct",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    o = out / "cook_pvi_districts.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]


# ── CIS noncitizen by district ──────────────────────────────────────────────

def _parse_cis_district(geo_name: str) -> tuple[str | None, int | None]:
    """'Congressional District 1 (118th Congress), Alabama' → ('Alabama', 1)."""
    if pd.isna(geo_name):
        return None, None
    s = str(geo_name).strip()
    m = re.match(r"Congressional District (\d+).*?,\s*(.+)$", s)
    if m:
        return m.group(2).strip(), int(m.group(1))
    m = re.match(r"Congressional District \(at Large\).*?,\s*(.+)$", s)
    if m:
        return m.group(1).strip(), 0
    return None, None


def _clean_cis_noncitizen(raw: Path, out: Path) -> list[Path]:
    p = raw / "cis_noncitizen_by_district.xlsx"
    if not p.exists():
        return []

    df = pd.read_excel(p, header=1)

    # Identify the geography column (contains "Congressional District")
    geo_col = None
    for col in df.columns:
        sample = df[col].dropna().astype(str)
        if sample.str.contains("Congressional District", case=False).any():
            geo_col = col
            break

    if geo_col is None:
        print("  [clean] CIS: could not identify geography column")
        return []

    parsed = df[geo_col].apply(_parse_cis_district)
    df["state_name_raw"] = parsed.apply(lambda x: x[0])
    df["district_number"] = parsed.apply(lambda x: x[1])

    df = df.dropna(subset=["state_name_raw", "district_number"])
    df["district_number"] = df["district_number"].astype(int)
    df["state_fips"] = df["state_name_raw"].map(NAME_TO_FIPS)
    df = df.dropna(subset=["state_fips"])
    df = add_state_ids(df, "state_fips", "fips")

    # Standardise numeric columns
    for col in df.columns:
        if col in ("state_name_raw", "state_fips", "state_name", "state_abbr",
                    "district_number", geo_col):
            continue
        if df[col].dtype == object:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["district_label"] = (
        df["state_abbr"] + "-" + df["district_number"].astype(str)
    )

    o = out / "cis_noncitizen_districts.parquet"
    df.to_parquet(o, index=False)
    _report(o, df)
    return [o]
