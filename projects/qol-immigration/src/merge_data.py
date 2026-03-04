"""Build consolidated analytical panels from cleaned Parquet files.

Outputs three analysis-ready tables:

- ``state_panel.parquet`` — year × state with all state-level indicators.
- ``national_panel.parquet`` — year with all national indicators.
- ``district_crosssection.parquet`` — district-level political + demographic data.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from pipeline.config import get_data_processed_dir
from pipeline.geo import FIPS_TO_NAME, FIPS_TO_ABBR, add_state_ids


def run(config: dict) -> dict[str, pd.DataFrame]:
    """Build merged panels.  Returns dict of name → DataFrame."""
    proc = get_data_processed_dir(config)

    datasets: dict[str, pd.DataFrame] = {}

    state = _build_state_panel(proc)
    if state is not None:
        out = proc / "state_panel.parquet"
        state.to_parquet(out, index=False)
        datasets["state_panel"] = state
        print(f"  [merge] → state_panel.parquet  ({len(state):,} rows × {len(state.columns)} cols)")

    national = _build_national_panel(proc)
    if national is not None:
        out = proc / "national_panel.parquet"
        national.to_parquet(out, index=False)
        datasets["national_panel"] = national
        print(f"  [merge] → national_panel.parquet  ({len(national):,} rows × {len(national.columns)} cols)")

    district = _build_district_crosssection(proc)
    if district is not None:
        out = proc / "district_crosssection.parquet"
        district.to_parquet(out, index=False)
        datasets["district_crosssection"] = district
        print(f"  [merge] → district_crosssection.parquet  ({len(district):,} rows × {len(district.columns)} cols)")

    # Also load any remaining individual files so they're available
    for pf in sorted(proc.glob("*.parquet")):
        stem = pf.stem
        if stem not in datasets:
            datasets[stem] = pd.read_parquet(pf)

    print(f"  [merge] {len(datasets)} dataset(s) available for analysis.")
    return datasets


# ---------------------------------------------------------------------------
# State panel
# ---------------------------------------------------------------------------

def _build_state_panel(proc: Path) -> pd.DataFrame | None:
    """Outer-join all state-level indicators on (year, state_fips)."""

    specs: list[tuple[str, list[str] | None, dict | None]] = [
        # (filename, columns_to_keep (None = auto), pre-filter)
        ("acs_median_income.parquet", ["year", "state_fips", "median_household_income"], None),
        ("acs_poverty_rate.parquet", ["year", "state_fips", "poverty_pct"], None),
        ("acs_college_attainment.parquet", ["year", "state_fips", "bachelors_pct"], None),
        ("acs_foreign_born.parquet", ["year", "state_fips", "total_pop", "foreign_born", "foreign_born_pct"], None),
        ("bea_state_gdp.parquet", ["year", "state_fips", "real_gdp_millions", "current_dollar_gdp_millions", "compensation_millions"], None),
        ("cdc_life_expectancy.parquet", ["year", "state_fips", "life_expectancy"], {"sex": "Total"}),
        ("dhs_immigration.parquet", ["year", "state_fips", "population", "lpr_total", "refugees_total",
                                      "naturalizations_total", "asylees_total", "lpr_per_million",
                                      "refugees_per_million"], None),
        ("nces_graduation.parquet", ["year", "state_fips", "acgr_total"], None),
        ("census_voter_registration.parquet", ["year", "state_fips", "voter_reg_total_pct", "voter_reg_citizen_pct"], None),
    ]

    # FHFA HPI: compute annual state average from quarterly data
    fhfa_path = proc / "fhfa_hpi.parquet"
    fhfa_annual = None
    if fhfa_path.exists():
        fhfa = pd.read_parquet(fhfa_path)
        fhfa_annual = (
            fhfa.groupby(["year", "state_fips"], as_index=False)
            .agg(hpi_annual_avg=("hpi", "mean"))
        )

    panels: list[pd.DataFrame] = []

    for fname, cols, pre_filter in specs:
        path = proc / fname
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if pre_filter:
            for k, v in pre_filter.items():
                df = df[df[k] == v]
        if cols:
            available = [c for c in cols if c in df.columns]
            df = df[available]
        df = df.drop_duplicates(subset=["year", "state_fips"])
        panels.append(df)

    if fhfa_annual is not None:
        panels.append(fhfa_annual)

    if not panels:
        return None

    result = panels[0]
    for p in panels[1:]:
        result = result.merge(p, on=["year", "state_fips"], how="outer")

    result = add_state_ids(result, "state_fips", "fips")
    id_cols = ["year", "state_fips", "state_name", "state_abbr"]
    val_cols = [c for c in result.columns if c not in id_cols]
    result = result[id_cols + sorted(val_cols)]
    result = result.sort_values(["year", "state_fips"]).reset_index(drop=True)
    return result


# ---------------------------------------------------------------------------
# National panel
# ---------------------------------------------------------------------------

def _build_national_panel(proc: Path) -> pd.DataFrame | None:
    """Outer-join all national-level indicators on year."""

    specs = [
        ("fred_gini.parquet", ["year", "gini_coefficient"]),
        ("fred_median_income_national.parquet", ["year", "median_household_income_real"]),
        ("fred_poverty_rate_national.parquet", ["year", "poverty_rate"]),
    ]

    # BLS earnings: compute annual average from quarterly
    bls_path = proc / "bls_weekly_earnings.parquet"
    bls_annual = None
    if bls_path.exists():
        bls = pd.read_parquet(bls_path)
        bls_annual = (
            bls.groupby("year", as_index=False)
            .agg(median_weekly_earnings_real=("median_weekly_earnings_real", "mean"))
        )

    panels: list[pd.DataFrame] = []

    for fname, cols in specs:
        path = proc / fname
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        available = [c for c in cols if c in df.columns]
        panels.append(df[available].drop_duplicates(subset=["year"]))

    if bls_annual is not None:
        panels.append(bls_annual)

    if not panels:
        return None

    result = panels[0]
    for p in panels[1:]:
        result = result.merge(p, on="year", how="outer")

    result = result.sort_values("year").reset_index(drop=True)
    return result


# ---------------------------------------------------------------------------
# District cross-section
# ---------------------------------------------------------------------------

def _build_district_crosssection(proc: Path) -> pd.DataFrame | None:
    """Join Cook PVI and CIS noncitizen data by state + district."""

    cook_path = proc / "cook_pvi_districts.parquet"
    cis_path = proc / "cis_noncitizen_districts.parquet"

    if not cook_path.exists() and not cis_path.exists():
        return None

    if cook_path.exists() and cis_path.exists():
        cook = pd.read_parquet(cook_path)
        cis = pd.read_parquet(cis_path)

        # Standardise join keys
        if "district_label" in cook.columns and "district_label" in cis.columns:
            result = cook.merge(
                cis, on="district_label", how="outer",
                suffixes=("", "_cis"),
            )
        else:
            result = cook.merge(
                cis,
                on=["state_abbr", "district_number"],
                how="outer",
                suffixes=("", "_cis"),
            )
        return result

    if cook_path.exists():
        return pd.read_parquet(cook_path)
    return pd.read_parquet(cis_path)
