"""Project-specific data cleaning for the Generation Priced Out study.

Produces tidy Parquet files from raw CSVs and World Bank JSON:
  - census_living.parquet        — % living independently, 25-34, annual
  - census_marital.parquet       — % married, 25-34, annual
  - census_homeownership.parquet — homeownership rate, under 35, annual
  - us_tfr.parquet               — US Total Fertility Rate, annual
  - housing_economics.parquet    — Home price, income, mortgage, sqft, CPI, lot size
  - world_bank_intl.parquet      — International TFR + pop growth + GDP/cap growth

Standards:
  - Column naming: lowercase_snake_case
  - Time: year (int)
  - Measurements: float64
  - Missing: NaN only
  - Sort: year (US), country_code + year (international)
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import numpy as np

from pipeline.config import get_data_raw_dir, get_data_processed_dir


def _report(path: Path, df: pd.DataFrame) -> None:
    print(f"  [clean] -> {path.name}  ({len(df):,} rows x {len(df.columns)} cols)")


# ---------------------------------------------------------------------------
# Census CPS: Living arrangements
# ---------------------------------------------------------------------------

def clean_census_living(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "census_cps_living_arrangements.csv"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    df = pd.read_csv(src)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    df["pct_independent_25_34"] = pd.to_numeric(
        df["pct_independent_25_34"], errors="coerce"
    )
    df["pct_at_parent_home_25_34"] = pd.to_numeric(
        df["pct_at_parent_home_25_34"], errors="coerce"
    )
    df = df[["year", "pct_independent_25_34", "pct_at_parent_home_25_34"]].copy()
    df = df.sort_values("year").reset_index(drop=True)

    dest = out_dir / "census_living.parquet"
    df.to_parquet(dest, index=False)
    _report(dest, df)


# ---------------------------------------------------------------------------
# Census CPS: Marital status
# ---------------------------------------------------------------------------

def clean_census_marital(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "census_cps_marital_status.csv"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    df = pd.read_csv(src)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    df["pct_married_25_34"] = pd.to_numeric(df["pct_married_25_34"], errors="coerce")
    df = df[["year", "pct_married_25_34"]].copy()
    df = df.sort_values("year").reset_index(drop=True)

    dest = out_dir / "census_marital.parquet"
    df.to_parquet(dest, index=False)
    _report(dest, df)


# ---------------------------------------------------------------------------
# Census HVS: Homeownership by age
# ---------------------------------------------------------------------------

def clean_census_homeownership(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "census_hvs_homeownership.csv"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    df = pd.read_csv(src)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    df["homeownership_rate_under_35"] = pd.to_numeric(
        df["homeownership_rate_under_35"], errors="coerce"
    )
    df = df[["year", "homeownership_rate_under_35"]].copy()
    df = df.sort_values("year").reset_index(drop=True)

    dest = out_dir / "census_homeownership.parquet"
    df.to_parquet(dest, index=False)
    _report(dest, df)


# ---------------------------------------------------------------------------
# US TFR: extract from World Bank international data (USA country code)
# ---------------------------------------------------------------------------

def clean_us_tfr(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "world_bank_fertility_rate.json"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    records = json.loads(src.read_text())
    rows = []
    for r in records:
        iso3 = r.get("countryiso3code", "")
        if iso3 != "USA":
            continue
        year_str = r.get("date", "")
        value = r.get("value")
        if value is None:
            continue
        try:
            rows.append({"year": int(year_str), "total_fertility_rate": float(value)})
        except (ValueError, TypeError):
            continue

    if not rows:
        print("  WARN: no US TFR records found in World Bank data")
        return
    df = pd.DataFrame(rows).sort_values("year").reset_index(drop=True)
    dest = out_dir / "us_tfr.parquet"
    df.to_parquet(dest, index=False)
    _report(dest, df)


# ---------------------------------------------------------------------------
# World Bank: International indicators (all countries)
# ---------------------------------------------------------------------------

WORLD_BANK_FILES = {
    "world_bank_fertility_rate.json": "fertility_rate",
    "world_bank_population_growth_pct.json": "population_growth_pct",
    "world_bank_gdp_per_capita_growth_pct.json": "gdp_per_capita_growth_pct",
}

# Exclude aggregate/regional codes from World Bank (not real countries)
WB_AGGREGATE_PREFIXES = {
    "AFE", "AFW", "ARB", "CEB", "CSS", "EAP", "EAR", "EAS", "ECA", "ECR",
    "ECS", "EMU", "EUU", "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "IDB",
    "IDX", "INX", "LAC", "LCN", "LDC", "LIC", "LMC", "LMY", "LTE", "MEA",
    "MIC", "MNA", "NAC", "OED", "OSS", "PRE", "PSS", "PST", "SAS", "SSA",
    "SSF", "SST", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS", "UMC", "WLD",
}


def clean_world_bank(raw_dir: Path, out_dir: Path) -> None:
    frames = []
    for filename, col_name in WORLD_BANK_FILES.items():
        src = raw_dir / filename
        if not src.exists():
            print(f"  SKIP (missing): {src.name}")
            continue

        records = json.loads(src.read_text())
        rows = []
        for r in records:
            code = r.get("countryiso3code", "")
            name = r.get("country", {}).get("value", "")
            if not code or code in WB_AGGREGATE_PREFIXES:
                continue
            year_str = r.get("date", "")
            value = r.get("value")
            if value is None:
                continue
            try:
                rows.append({
                    "country_code": code,
                    "country_name": name,
                    "year": int(year_str),
                    col_name: float(value),
                })
            except (ValueError, TypeError):
                continue

        if rows:
            frames.append(pd.DataFrame(rows))

    if not frames:
        print("  WARN: no World Bank data to merge")
        return

    # Outer-join all indicators on (country_code, country_name, year)
    merged = frames[0]
    for f in frames[1:]:
        merged = merged.merge(
            f, on=["country_code", "country_name", "year"], how="outer"
        )

    merged = merged.sort_values(["country_code", "year"]).reset_index(drop=True)

    dest = out_dir / "world_bank_intl.parquet"
    merged.to_parquet(dest, index=False)
    _report(dest, merged)


# ---------------------------------------------------------------------------
# FRED housing economics + CPI
# ---------------------------------------------------------------------------

FRED_SERIES_MAP = {
    "MSPUS": ("median_home_price", "quarterly"),
    "MSPNHSUS": ("median_new_home_price", "monthly"),
    "MEHOINUSA646N": ("median_household_income", "annual"),
    "MORTGAGE30US": ("mortgage_rate_30yr", "weekly"),
    "COMPSFLAM1FQ": ("median_sqft_new", "quarterly"),
    "MDSP": ("mortgage_debt_service_pct", "quarterly"),
    "CPIAUCSL": ("cpi_u", "monthly"),
    "CUSR0000SAH1": ("cpi_shelter", "monthly"),
    "A792RC0A052NBEA": ("per_capita_income", "annual"),
    "MEPAINUSA646N": ("median_personal_income", "annual"),
}


def _load_fred_series(raw_dir: Path, series_id: str) -> pd.DataFrame | None:
    """Load a FRED CSV and return a DataFrame with (date, value) columns."""
    src = raw_dir / f"fred_{series_id}.csv"
    if not src.exists():
        return None
    df = pd.read_csv(src)
    df.columns = [c.strip().lower() for c in df.columns]
    date_col = [c for c in df.columns if "date" in c][0]
    val_col = [c for c in df.columns if c != date_col][0]
    df = df.rename(columns={date_col: "date", val_col: "value"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"])
    return df


def clean_fred_housing(raw_dir: Path, out_dir: Path) -> None:
    frames: dict[str, pd.Series] = {}

    for series_id, (col_name, freq) in FRED_SERIES_MAP.items():
        df = _load_fred_series(raw_dir, series_id)
        if df is None:
            print(f"  SKIP (missing): fred_{series_id}.csv")
            continue

        df["year"] = df["date"].dt.year
        annual = df.groupby("year")["value"].mean().reset_index()
        annual = annual.rename(columns={"value": col_name})
        frames[col_name] = annual

    if not frames:
        print("  WARN: no FRED housing data to clean")
        return

    # Start from the union of all years
    all_years: set[int] = set()
    for annual_df in frames.values():
        all_years.update(annual_df["year"].tolist())
    result = pd.DataFrame({"year": sorted(all_years)})

    for col_name, annual_df in frames.items():
        result = result.merge(annual_df, on="year", how="left")

    # Add documented lot size
    lot_src = raw_dir / "census_median_lot_size.csv"
    if lot_src.exists():
        lot_df = pd.read_csv(lot_src)
        lot_df["year"] = pd.to_numeric(lot_df["year"], errors="coerce").astype(int)
        lot_df["median_lot_size_sqft"] = pd.to_numeric(
            lot_df["median_lot_size_sqft"], errors="coerce"
        )
        result = result.merge(
            lot_df[["year", "median_lot_size_sqft"]], on="year", how="left"
        )

    result = result.sort_values("year").reset_index(drop=True)
    dest = out_dir / "housing_economics.parquet"
    result.to_parquet(dest, index=False)
    _report(dest, result)


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def run(config: dict) -> None:
    raw_dir = get_data_raw_dir(config)
    out_dir = get_data_processed_dir(config)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[Generation Priced Out] Cleaning all sources...")
    clean_census_living(raw_dir, out_dir)
    clean_census_marital(raw_dir, out_dir)
    clean_census_homeownership(raw_dir, out_dir)
    clean_us_tfr(raw_dir, out_dir)
    clean_fred_housing(raw_dir, out_dir)
    clean_world_bank(raw_dir, out_dir)
    print("[Generation Priced Out] Cleaning complete.")
