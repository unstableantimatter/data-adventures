"""Project-specific data merging for the Deaths of Despair study.

Produces:
  - state_panel.parquet  — one row per (state × year), all indicators joined
  - national_panel.parquet — national annual averages/totals

The merge window is 1999–2021 (limited by CDC overdose data).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.config import get_data_processed_dir
from pipeline.geo import VALID_STATE_FIPS


# Appalachian + Rust Belt states for regional coding
RUST_BELT = {"OH", "PA", "MI", "IN", "WI", "IL", "MO", "NY"}
APPALACHIA = {"WV", "KY", "TN", "VA", "NC", "SC", "GA", "AL", "MS", "PA", "NY", "OH", "MD"}
SOUTH = {"TX", "FL", "GA", "NC", "SC", "VA", "TN", "AL", "MS", "LA", "AR", "OK", "KY", "WV"}


def _load(path: Path, key_cols: list[str]) -> pd.DataFrame | None:
    if not path.exists():
        print(f"  [merge] MISSING: {path.name}")
        return None
    df = pd.read_parquet(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    return df


def run(config: dict) -> None:
    processed = get_data_processed_dir(config)

    overdose = _load(processed / "cdc_overdose.parquet", ["state_fips", "year"])
    suicide = _load(processed / "cdc_suicide.parquet", ["state_fips", "year"])
    mfg = _load(processed / "fred_manufacturing.parquet", ["state_fips", "year"])
    unemp = _load(processed / "fred_unemployment.parquet", ["state_fips", "year"])
    income = _load(processed / "acs_income.parquet", ["state_fips", "year"])
    poverty = _load(processed / "acs_poverty.parquet", ["state_fips", "year"])

    # -----------------------------------------------------------------------
    # state_panel: outer-join all datasets on (state_fips, year)
    # -----------------------------------------------------------------------

    # Start from overdose as the primary frame (1999-2021)
    if overdose is None:
        print("  [merge] ERROR: overdose data required for state_panel. Aborting.")
        return

    panel = overdose[
        ["year", "state_fips", "state_name", "state_abbr",
         "overdose_death_rate", "overdose_deaths", "population"]
    ].copy()

    # Suicide
    if suicide is not None:
        panel = panel.merge(
            suicide[["year", "state_fips", "suicide_rate", "suicide_deaths"]],
            on=["year", "state_fips"], how="left"
        )

    # Manufacturing employment
    if mfg is not None:
        panel = panel.merge(
            mfg[["year", "state_fips", "manufacturing_employees_thousands"]],
            on=["year", "state_fips"], how="left"
        )

    # Unemployment rate
    if unemp is not None:
        panel = panel.merge(
            unemp[["year", "state_fips", "unemployment_rate"]],
            on=["year", "state_fips"], how="left"
        )

    # Income (ACS 2005+)
    if income is not None:
        panel = panel.merge(
            income[["year", "state_fips", "median_household_income"]],
            on=["year", "state_fips"], how="left"
        )

    # Poverty (ACS 2005+)
    if poverty is not None:
        panel = panel.merge(
            poverty[["year", "state_fips", "poverty_pct"]],
            on=["year", "state_fips"], how="left"
        )

    # -----------------------------------------------------------------------
    # Derived: deaths of despair = overdose + suicide (per 100k)
    # -----------------------------------------------------------------------
    panel["deaths_despair_rate"] = (
        panel["overdose_death_rate"].fillna(0)
        + panel["suicide_rate"].fillna(0)
    )
    # Set to NaN if both components are missing
    both_missing = panel["overdose_death_rate"].isna() & panel["suicide_rate"].isna()
    panel.loc[both_missing, "deaths_despair_rate"] = float("nan")

    # -----------------------------------------------------------------------
    # Regional classification
    # -----------------------------------------------------------------------
    panel["region"] = "Other"
    panel.loc[panel["state_abbr"].isin(RUST_BELT), "region"] = "Rust Belt"
    panel.loc[panel["state_abbr"].isin(APPALACHIA), "region"] = "Appalachia"
    # Rust Belt takes priority over Appalachia for overlapping states
    panel.loc[
        panel["state_abbr"].isin(RUST_BELT & APPALACHIA), "region"
    ] = "Rust Belt / Appalachia"
    panel.loc[
        panel["state_abbr"].isin({"CA", "NY", "MA", "WA", "OR", "CT", "NJ", "MD"}),
        "region"
    ] = "Coastal Metro"

    # -----------------------------------------------------------------------
    # Manufacturing change metrics
    # -----------------------------------------------------------------------
    # Year-over-year % change in manufacturing employment
    panel = panel.sort_values(["state_fips", "year"])
    panel["mfg_yoy_pct_change"] = (
        panel.groupby("state_fips")["manufacturing_employees_thousands"]
        .pct_change() * 100
    )

    # Manufacturing employment relative to 2000 baseline (index)
    baseline = (
        panel[panel["year"] == 2000]
        .set_index("state_fips")["manufacturing_employees_thousands"]
        .rename("mfg_baseline_2000")
    )
    panel = panel.join(baseline, on="state_fips")
    panel["mfg_index_2000"] = (
        panel["manufacturing_employees_thousands"] / panel["mfg_baseline_2000"] * 100
    )

    panel = panel.drop(columns=["mfg_baseline_2000"], errors="ignore")
    panel = panel.sort_values(["year", "state_fips"]).reset_index(drop=True)

    out = processed / "state_panel.parquet"
    panel.to_parquet(out, index=False)
    print(f"  [merge] → state_panel.parquet  ({len(panel):,} rows × {len(panel.columns)} cols)")

    # -----------------------------------------------------------------------
    # national_panel: annual averages across all states
    # -----------------------------------------------------------------------
    num_cols = [
        "overdose_death_rate", "suicide_rate", "deaths_despair_rate",
        "manufacturing_employees_thousands", "unemployment_rate",
        "median_household_income", "poverty_pct",
    ]
    available_num = [c for c in num_cols if c in panel.columns]

    # Total deaths (sum), rates (mean)
    agg = panel.groupby("year").agg(
        overdose_deaths_total=("overdose_deaths", "sum"),
        suicide_deaths_total=("suicide_deaths", "sum") if "suicide_deaths" in panel.columns else ("overdose_deaths", "sum"),
        **{col: (col, "mean") for col in available_num},
    ).reset_index()

    # Fix suicide_deaths_total if column didn't exist
    if "suicide_deaths" not in panel.columns:
        agg = agg.rename(columns={"suicide_deaths_total": "overdose_deaths_total_dup"})
        agg = agg.drop(columns=["overdose_deaths_total_dup"], errors="ignore")

    out_nat = processed / "national_panel.parquet"
    agg.to_parquet(out_nat, index=False)
    print(f"  [merge] → national_panel.parquet  ({len(agg):,} rows × {len(agg.columns)} cols)")
