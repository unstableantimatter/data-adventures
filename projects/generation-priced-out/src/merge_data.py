"""Project-specific data merging for the Generation Priced Out study.

Produces:
  - national_panel.parquet      — US annual: milestones + housing economics + derived ratios
  - international_panel.parquet — All countries: TFR + pop growth + GDP/cap growth
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from pipeline.config import get_data_processed_dir

INDEX_BASE_YEAR = 1984


def _load(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        print(f"  [merge] MISSING: {path.name}")
        return None
    return pd.read_parquet(path)


def _monthly_payment(principal: float, annual_rate_pct: float,
                     years: int = 30) -> float:
    """Standard amortization: monthly payment for a fixed-rate mortgage."""
    if pd.isna(principal) or pd.isna(annual_rate_pct) or annual_rate_pct <= 0:
        return float("nan")
    r = annual_rate_pct / 100 / 12
    n = years * 12
    return principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def run(config: dict) -> None:
    processed = get_data_processed_dir(config)

    living = _load(processed / "census_living.parquet")
    marital = _load(processed / "census_marital.parquet")
    homeown = _load(processed / "census_homeownership.parquet")
    tfr = _load(processed / "us_tfr.parquet")
    housing = _load(processed / "housing_economics.parquet")

    # -------------------------------------------------------------------
    # national_panel: one row per year, all US metrics
    # -------------------------------------------------------------------
    all_years: set[int] = set()
    for df in [living, marital, homeown, tfr, housing]:
        if df is not None:
            all_years.update(df["year"].tolist())

    panel = pd.DataFrame({"year": sorted(all_years)})

    if living is not None:
        panel = panel.merge(
            living[["year", "pct_independent_25_34", "pct_at_parent_home_25_34"]],
            on="year", how="left"
        )
    if marital is not None:
        panel = panel.merge(
            marital[["year", "pct_married_25_34"]],
            on="year", how="left"
        )
    if homeown is not None:
        panel = panel.merge(
            homeown[["year", "homeownership_rate_under_35"]],
            on="year", how="left"
        )
    if tfr is not None:
        panel = panel.merge(
            tfr[["year", "total_fertility_rate"]],
            on="year", how="left"
        )
    if housing is not None:
        panel = panel.merge(housing, on="year", how="left")

    # -------------------------------------------------------------------
    # Derived affordability metrics
    # -------------------------------------------------------------------
    if "median_home_price" in panel.columns and "median_household_income" in panel.columns:
        panel["price_to_income_ratio"] = (
            panel["median_home_price"] / panel["median_household_income"]
        )

    if "median_home_price" in panel.columns and "per_capita_income" in panel.columns:
        panel["price_to_per_capita_income_ratio"] = (
            panel["median_home_price"] / panel["per_capita_income"]
        )

    if "median_home_price" in panel.columns and "mortgage_rate_30yr" in panel.columns:
        # Monthly payment assuming 20% down, 30-year fixed
        panel["monthly_payment_median"] = panel.apply(
            lambda r: _monthly_payment(
                r["median_home_price"] * 0.80,
                r["mortgage_rate_30yr"],
            ), axis=1,
        )

    if "monthly_payment_median" in panel.columns and "median_household_income" in panel.columns:
        panel["payment_to_income_pct"] = (
            panel["monthly_payment_median"] / (panel["median_household_income"] / 12) * 100
        )

    if "median_home_price" in panel.columns and "median_personal_income" in panel.columns:
        panel["price_to_personal_income_ratio"] = (
            panel["median_home_price"] / panel["median_personal_income"]
        )

    if "monthly_payment_median" in panel.columns and "median_personal_income" in panel.columns:
        panel["payment_to_personal_income_pct"] = (
            panel["monthly_payment_median"] / (panel["median_personal_income"] / 12) * 100
        )

    if "median_new_home_price" in panel.columns and "median_sqft_new" in panel.columns:
        panel["price_per_sqft_new"] = (
            panel["median_new_home_price"] / panel["median_sqft_new"]
        )

    # -------------------------------------------------------------------
    # CPI-indexed series (base INDEX_BASE_YEAR = 100)
    # -------------------------------------------------------------------
    for raw_col, idx_col in [
        ("median_home_price", "home_price_idx"),
        ("median_household_income", "income_idx"),
        ("per_capita_income", "per_capita_income_idx"),
        ("cpi_u", "cpi_u_idx"),
        ("cpi_shelter", "cpi_shelter_idx"),
    ]:
        if raw_col not in panel.columns:
            continue
        base_row = panel.loc[panel["year"] == INDEX_BASE_YEAR, raw_col]
        if base_row.empty or pd.isna(base_row.iloc[0]):
            continue
        base_val = float(base_row.iloc[0])
        panel[idx_col] = panel[raw_col] / base_val * 100

    # Real (CPI-adjusted) home price
    if "median_home_price" in panel.columns and "cpi_u" in panel.columns:
        cpi_base = panel.loc[panel["year"] == INDEX_BASE_YEAR, "cpi_u"]
        if not cpi_base.empty and not pd.isna(cpi_base.iloc[0]):
            deflator = panel["cpi_u"] / float(cpi_base.iloc[0])
            panel["real_home_price"] = panel["median_home_price"] / deflator

    panel = panel.sort_values("year").reset_index(drop=True)

    out = processed / "national_panel.parquet"
    panel.to_parquet(out, index=False)
    print(f"  [merge] -> national_panel.parquet  ({len(panel):,} rows x {len(panel.columns)} cols)")

    # -------------------------------------------------------------------
    # international_panel: pass-through from cleaned World Bank data
    # -------------------------------------------------------------------
    intl = _load(processed / "world_bank_intl.parquet")
    if intl is not None:
        out_intl = processed / "international_panel.parquet"
        intl.to_parquet(out_intl, index=False)
        print(f"  [merge] -> international_panel.parquet  ({len(intl):,} rows x {len(intl.columns)} cols)")
    else:
        print("  [merge] WARN: no international data to write")
