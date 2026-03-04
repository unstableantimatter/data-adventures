"""Project-specific data cleaning for the Deaths of Despair study.

Standards (same as pipeline-wide):
- Tidy format — one observation per row.
- Column naming — lowercase_snake_case.
- Geographic IDs — state_fips (zero-padded 2-digit str), state_name, state_abbr.
- Time — year (int).
- Data types — measurements as float64, identifiers as str.
- Missing values — NaN only.
- Sort order — year, then state_fips.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from pipeline.config import get_data_raw_dir, get_data_processed_dir
from pipeline.geo import (
    ABBR_TO_FIPS, ABBR_TO_NAME as GEO_ABBR_TO_NAME,
    FIPS_TO_NAME, FIPS_TO_ABBR,
    NAME_TO_FIPS, VALID_STATE_FIPS, add_state_ids,
)

_SENTINELS = frozenset({"N", "(X)", "-", "---", "‡", "(L)", "(NA)", "nan", ".", "Unreliable", ""})



def _to_float(val) -> float:
    if pd.isna(val):
        return float("nan")
    s = str(val).strip()
    if s in _SENTINELS:
        return float("nan")
    s = re.sub(r"\\+\d+\\*", "", s).strip()
    s = s.replace("%", "").replace("$", "").replace(",", "").strip()
    if not s:
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def _report(path: Path, df: pd.DataFrame) -> None:
    print(f"  [clean] → {path.name}  ({len(df):,} rows × {len(df.columns)} cols)")


# ---------------------------------------------------------------------------
# CDC overdose deaths
# ---------------------------------------------------------------------------

def _parse_overdose_records(records: list[dict]) -> list[dict]:
    """Parse CDC drug overdose records into a normalized row dict."""
    rows = []
    for r in records:
        state_name = r.get("state", "").strip()
        if not state_name or state_name == "United States":
            continue
        year_str = r.get("year", "")
        rate = _to_float(r.get("age_adjusted_rate") or r.get("crude_death_rate"))
        crude = _to_float(r.get("crude_death_rate"))
        deaths = _to_float(r.get("deaths"))
        population = _to_float(r.get("population"))
        try:
            year = int(float(year_str))
        except (ValueError, TypeError):
            continue
        rows.append({
            "year": year,
            "state_name": state_name,
            "overdose_death_rate": rate,
            "overdose_crude_rate": crude,
            "overdose_deaths": deaths,
            "population": population,
        })
    return rows


def clean_cdc_overdose(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "cdc_overdose_by_state.json"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    rows = _parse_overdose_records(json.loads(src.read_text()))

    # Supplement with 2016 data from xbxb-epbu if available
    src_2016 = raw_dir / "cdc_overdose_2016.json"
    if src_2016.exists():
        rows.extend(_parse_overdose_records(json.loads(src_2016.read_text())))

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["year", "state_name"])
    df = add_state_ids(df, source_col="state_name", source_type="name")
    df = df[df["state_fips"].isin(VALID_STATE_FIPS)].copy()
    df["overdose_death_rate"] = df["overdose_death_rate"].astype(float)
    df["overdose_deaths"] = df["overdose_deaths"].astype(float)
    df["population"] = df["population"].astype(float)
    df = df.sort_values(["year", "state_fips"]).reset_index(drop=True)

    dest = out_dir / "cdc_overdose.parquet"
    df.to_parquet(dest, index=False)
    _report(dest, df)


# ---------------------------------------------------------------------------
# CDC suicide deaths
# ---------------------------------------------------------------------------

def clean_cdc_suicide(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "cdc_suicide_by_state.json"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    records = json.loads(src.read_text())
    rows = []
    for r in records:
        state_name = r.get("state", "").strip()
        if not state_name or state_name == "United States":
            continue
        cause = r.get("cause_name", "").strip()
        if "Suicide" not in cause and "suicide" not in cause:
            continue
        year_str = r.get("year", "")
        rate = _to_float(r.get("aadr") or r.get("age_adjusted_death_rate"))
        deaths = _to_float(r.get("deaths"))
        try:
            year = int(float(year_str))
        except (ValueError, TypeError):
            continue
        rows.append({
            "year": year,
            "state_name": state_name,
            "suicide_rate": rate,
            "suicide_deaths": deaths,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        print("  WARN: cdc_suicide is empty after filtering")
        return
    df = add_state_ids(df, source_col="state_name", source_type="name")
    df = df[df["state_fips"].isin(VALID_STATE_FIPS)].copy()
    df["suicide_rate"] = df["suicide_rate"].astype(float)
    df = df.sort_values(["year", "state_fips"]).reset_index(drop=True)

    dest = out_dir / "cdc_suicide.parquet"
    df.to_parquet(dest, index=False)
    _report(dest, df)


# ---------------------------------------------------------------------------
# FRED manufacturing employment
# ---------------------------------------------------------------------------

def clean_fred_manufacturing(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "fred_manufacturing_by_state.csv"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    df = pd.read_csv(src)
    # Convert date column to year (annual average)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["year"] = df["date"].dt.year
    df["manufacturing_employees_thousands"] = pd.to_numeric(
        df["manufacturing_employees_thousands"], errors="coerce"
    )
    # Annual average from monthly data
    df = (
        df.groupby(["state_abbr", "year"])["manufacturing_employees_thousands"]
        .mean()
        .reset_index()
    )
    df = df.rename(columns={"state_abbr": "state_abbr"})
    # Add state identifiers
    df = add_state_ids(df, source_col="state_abbr", source_type="abbr")
    df = df.dropna(subset=["state_fips"])
    df = df[df["state_fips"].isin(VALID_STATE_FIPS)].copy()
    df = df.sort_values(["year", "state_fips"]).reset_index(drop=True)

    dest = out_dir / "fred_manufacturing.parquet"
    df.to_parquet(dest, index=False)
    _report(dest, df)


# ---------------------------------------------------------------------------
# FRED unemployment rates
# ---------------------------------------------------------------------------

def clean_fred_unemployment(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "fred_unemployment_by_state.csv"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    df = pd.read_csv(src)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["year"] = df["date"].dt.year
    df["unemployment_rate"] = pd.to_numeric(df["unemployment_rate"], errors="coerce")
    # Annual average
    df = (
        df.groupby(["state_abbr", "year"])["unemployment_rate"]
        .mean()
        .reset_index()
    )
    df = add_state_ids(df, source_col="state_abbr", source_type="abbr")
    df = df.dropna(subset=["state_fips"])
    df = df[df["state_fips"].isin(VALID_STATE_FIPS)].copy()
    df = df.sort_values(["year", "state_fips"]).reset_index(drop=True)

    dest = out_dir / "fred_unemployment.parquet"
    df.to_parquet(dest, index=False)
    _report(dest, df)


# ---------------------------------------------------------------------------
# Census ACS: income by state
# ---------------------------------------------------------------------------

def clean_census_income(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "acs_median_income_by_state.csv"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    df = pd.read_csv(src)
    df.columns = [c.strip().lower() for c in df.columns]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["median_household_income"] = pd.to_numeric(
        df["median_household_income"], errors="coerce"
    )
    df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    df = df.dropna(subset=["year", "median_household_income"])
    df = df[df["state_fips"].isin(VALID_STATE_FIPS)].copy()
    df = add_state_ids(df, source_col="state_fips", source_type="fips")
    df = df.sort_values(["year", "state_fips"]).reset_index(drop=True)

    dest = out_dir / "acs_income.parquet"
    df[["year", "state_fips", "state_name", "state_abbr", "median_household_income"]].to_parquet(
        dest, index=False
    )
    _report(dest, df)


# ---------------------------------------------------------------------------
# Census ACS: poverty by state
# ---------------------------------------------------------------------------

def clean_census_poverty(raw_dir: Path, out_dir: Path) -> None:
    src = raw_dir / "acs_poverty_by_state.csv"
    if not src.exists():
        print(f"  SKIP (missing): {src.name}")
        return

    df = pd.read_csv(src)
    df.columns = [c.strip().lower() for c in df.columns]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["poverty_pct"] = pd.to_numeric(df["poverty_pct"], errors="coerce")
    df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    df = df.dropna(subset=["year", "poverty_pct"])
    df = df[df["state_fips"].isin(VALID_STATE_FIPS)].copy()
    df = add_state_ids(df, source_col="state_fips", source_type="fips")
    df = df.sort_values(["year", "state_fips"]).reset_index(drop=True)

    dest = out_dir / "acs_poverty.parquet"
    df[["year", "state_fips", "state_name", "state_abbr", "poverty_pct"]].to_parquet(
        dest, index=False
    )
    _report(dest, df)


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------

def run(config: dict) -> None:
    raw_dir = get_data_raw_dir(config)
    out_dir = get_data_processed_dir(config)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[Deaths of Despair] Cleaning all sources...")
    clean_cdc_overdose(raw_dir, out_dir)
    clean_cdc_suicide(raw_dir, out_dir)
    clean_fred_manufacturing(raw_dir, out_dir)
    clean_fred_unemployment(raw_dir, out_dir)
    clean_census_income(raw_dir, out_dir)
    clean_census_poverty(raw_dir, out_dir)
    print("[Deaths of Despair] Cleaning complete.")
