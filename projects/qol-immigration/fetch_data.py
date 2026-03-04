#!/usr/bin/env python3
"""Fetch raw data files for the QoL vs. Immigration study.

Downloads from APIs and direct URLs where programmatic access is supported.
For sources that require manual download (FHFA, BLS, Cook PVI, etc.),
prints instructions.

Usage: python projects/qol-immigration/fetch_data.py
"""

import csv
import io
import json
import os
import urllib.request
import urllib.error
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def fetch_url(url: str, dest: Path, headers: dict | None = None) -> bool:
    """Download a URL to a file. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            if data[:15].startswith(b"<!DOCTYPE") or data[:6].startswith(b"<html"):
                print(f"  SKIP (got HTML instead of data): {dest.name}")
                return False
            dest.write_bytes(data)
            print(f"  OK: {dest.name} ({len(data):,} bytes)")
            return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"  FAIL: {dest.name} — {e}")
        return False


def fetch_fred_gini():
    """FRED: Gini coefficient (already downloaded, verify)."""
    dest = RAW_DIR / "gini_coefficient_usa.csv"
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  EXISTS: {dest.name}")
        return
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=GINIALLRF&cosd=1947-01-01&coed=2024-01-01"
    fetch_url(url, dest)


def fetch_fred_median_income():
    """FRED: Real Median Household Income (national, annual)."""
    dest = RAW_DIR / "median_household_income_usa.csv"
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MEHOINUSA672N&cosd=1984-01-01&coed=2024-01-01"
    fetch_url(url, dest)


def fetch_fred_poverty():
    """FRED: Poverty rate (national, annual)."""
    dest = RAW_DIR / "poverty_rate_usa.csv"
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PPAAUS00000A156NCEN&cosd=1960-01-01&coed=2024-01-01"
    fetch_url(url, dest)


def fetch_census_api_income_by_state():
    """Census ACS API: Median household income by state, 2005-2023."""
    dest = RAW_DIR / "acs_median_income_by_state.csv"
    rows = [["year", "state_fips", "state_name", "median_household_income"]]
    # ACS 1-year available 2005+
    for year in range(2005, 2024):
        if year == 2020:
            continue  # ACS 1-year not released for 2020 (COVID)
        url = f"https://api.census.gov/data/{year}/acs/acs1?get=NAME,B19013_001E&for=state:*"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                for row in data[1:]:
                    name, income, fips = row
                    if income and income != "null":
                        rows.append([str(year), fips, name, income])
        except Exception as e:
            print(f"  Census API {year}: {e}")

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


def fetch_census_api_poverty_by_state():
    """Census ACS API: Poverty rate by state, 2005-2023."""
    dest = RAW_DIR / "acs_poverty_rate_by_state.csv"
    rows = [["year", "state_fips", "state_name", "poverty_pct"]]
    for year in range(2005, 2024):
        if year == 2020:
            continue
        # B17001_002E = below poverty, B17001_001E = total for whom status determined
        url = f"https://api.census.gov/data/{year}/acs/acs1?get=NAME,B17001_001E,B17001_002E&for=state:*"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                for row in data[1:]:
                    name, total, below, fips = row
                    if total and below and total != "null" and below != "null":
                        pct = round(int(below) / int(total) * 100, 2)
                        rows.append([str(year), fips, name, str(pct)])
        except Exception as e:
            print(f"  Census API poverty {year}: {e}")

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


def fetch_census_api_foreign_born_by_state():
    """Census ACS API: Foreign-born population by state, 2005-2023."""
    dest = RAW_DIR / "acs_foreign_born_by_state.csv"
    rows = [["year", "state_fips", "state_name", "total_pop", "foreign_born", "foreign_born_pct"]]
    for year in range(2005, 2024):
        if year == 2020:
            continue
        # B05002_001E = total, B05002_013E = foreign born
        url = f"https://api.census.gov/data/{year}/acs/acs1?get=NAME,B05002_001E,B05002_013E&for=state:*"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                for row in data[1:]:
                    name, total, fb, fips = row
                    if total and fb and total != "null" and fb != "null":
                        pct = round(int(fb) / int(total) * 100, 2)
                        rows.append([str(year), fips, name, total, fb, str(pct)])
        except Exception as e:
            print(f"  Census API foreign-born {year}: {e}")

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


def fetch_census_api_education_by_state():
    """Census ACS API: Bachelor's degree attainment (25+) by state, 2005-2023."""
    dest = RAW_DIR / "acs_college_attainment_by_state.csv"
    rows = [["year", "state_fips", "state_name", "pop_25plus", "bachelors_or_higher", "bachelors_pct"]]
    for year in range(2005, 2024):
        if year == 2020:
            continue
        # B15003_001E = total 25+, B15003_022E thru B15003_025E = bachelors, masters, professional, doctorate
        url = (f"https://api.census.gov/data/{year}/acs/acs1?"
               f"get=NAME,B15003_001E,B15003_022E,B15003_023E,B15003_024E,B15003_025E&for=state:*")
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                for row in data[1:]:
                    name, total, bach, mast, prof, doct, fips = row
                    if all(v and v != "null" for v in [total, bach, mast, prof, doct]):
                        higher = int(bach) + int(mast) + int(prof) + int(doct)
                        pct = round(higher / int(total) * 100, 2)
                        rows.append([str(year), fips, name, total, str(higher), str(pct)])
        except Exception as e:
            print(f"  Census API education {year}: {e}")

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


def fetch_bea_state_gdp():
    """BEA API: Real GDP by state."""
    dest = RAW_DIR / "bea_state_gdp.csv"
    # BEA has a public API — key not required for basic queries
    url = ("https://apps.bea.gov/api/data/"
           "?UserID=X&method=GetData&datasetname=Regional"
           "&TableName=SAGDP9N&LineCode=1&GeoFips=STATE&Year=ALL&ResultFormat=JSON")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = json.loads(resp.read())
            if "BEAAPI" in raw and "Results" in raw["BEAAPI"]:
                data = raw["BEAAPI"]["Results"].get("Data", [])
                if data:
                    rows = [["year", "geo_fips", "geo_name", "real_gdp"]]
                    for d in data:
                        rows.append([d.get("TimePeriod"), d.get("GeoFips"),
                                     d.get("GeoName"), d.get("DataValue")])
                    with open(dest, "w", newline="") as f:
                        csv.writer(f).writerows(rows)
                    print(f"  OK: {dest.name} ({len(rows)-1} rows)")
                    return
    except Exception as e:
        print(f"  BEA API: {e}")

    print("  MANUAL: BEA state GDP — download from https://apps.bea.gov/regional/downloadzip.cfm (SAGDP tables)")


def fetch_census_voting():
    """Census: Historical voting rates by state."""
    dest = RAW_DIR / "census_voter_turnout.csv"
    # The Census provides XLS files; try a direct CSV
    url = "https://www2.census.gov/programs-surveys/cps/tables/time-series/voting-historical-time-series/A1_timeseries.xlsx"
    headers = {"User-Agent": "Mozilla/5.0 (data-adventures research project)"}
    if fetch_url(url, RAW_DIR / "census_voter_turnout.xlsx", headers):
        return
    print("  MANUAL: Census voter turnout — download from https://census.gov/data/tables/time-series/demo/voting-and-registration/voting-historical-time-series.html")


def print_manual_instructions():
    """Print instructions for sources that need manual download."""
    print("\n=== MANUAL DOWNLOADS NEEDED ===\n")
    print("The following sources require manual download (browser-only or registration):\n")
    print("1. FHFA House Price Index by state:")
    print("   https://www.fhfa.gov/hpi/download")
    print("   -> Download 'States (Seasonally Adjusted)' CSV")
    print(f"   -> Save as: {RAW_DIR}/fhfa_hpi_state.csv\n")
    print("2. BLS Median Weekly Earnings (real, constant dollars):")
    print("   https://data.bls.gov/timeseries/LEU0252881600")
    print("   -> Click 'More Formatting Options' -> select 1990-2024 -> CSV download")
    print(f"   -> Save as: {RAW_DIR}/bls_median_weekly_earnings.csv\n")
    print("3. Cook PVI by congressional district:")
    print("   https://www.cookpolitical.com/cook-pvi/2021-pvi-full-downloadable-state-and-district-list")
    print("   -> Download the state + district spreadsheet")
    print(f"   -> Save as: {RAW_DIR}/cook_pvi.csv\n")
    print("4. DHS Yearbook — LPRs and refugees by state:")
    print("   https://ohss.dhs.gov/topics/immigration/state-immigration-data")
    print("   -> Download state data sheets (Excel)")
    print(f"   -> Save as: {RAW_DIR}/dhs_lpr_by_state.xlsx and dhs_refugees_by_state.xlsx\n")
    print("5. NCES High School Graduation Rates by state:")
    print("   https://nces.ed.gov/ccd/drpcompstatelvl.asp")
    print("   -> Download completion data files")
    print(f"   -> Save as: {RAW_DIR}/nces_graduation_rates.xlsx\n")
    print("6. CDC Life Expectancy by state:")
    print("   https://wonder.cdc.gov/ -> Compressed Mortality query")
    print("   -> Or download state life tables from https://www.cdc.gov/nchs/products/life_tables.htm")
    print(f"   -> Save as: {RAW_DIR}/cdc_life_expectancy_by_state.csv\n")
    print("7. MPI Foreign-born by state (1990, 2000 decennial):")
    print("   https://www.migrationpolicy.org/programs/data-hub/charts/immigrant-population-state-1990-present")
    print("   -> Copy/download the 1990 and 2000 data points (ACS 2005+ covered by Census API above)")
    print(f"   -> Save as: {RAW_DIR}/mpi_foreign_born_1990_2000.csv\n")


def main():
    print("=== Fetching raw data for QoL vs. Immigration study ===\n")

    print("[FRED] Gini coefficient...")
    fetch_fred_gini()

    print("[FRED] Median household income (national)...")
    fetch_fred_median_income()

    print("[FRED] Poverty rate (national)...")
    fetch_fred_poverty()

    print("[Census API] Median income by state...")
    fetch_census_api_income_by_state()

    print("[Census API] Poverty rate by state...")
    fetch_census_api_poverty_by_state()

    print("[Census API] Foreign-born population by state...")
    fetch_census_api_foreign_born_by_state()

    print("[Census API] College attainment by state...")
    fetch_census_api_education_by_state()

    print("[BEA] State GDP...")
    fetch_bea_state_gdp()

    print("[Census] Voter turnout...")
    fetch_census_voting()

    print_manual_instructions()

    print("\n=== Done ===")
    print(f"\nFiles in {RAW_DIR}:")
    for f in sorted(RAW_DIR.iterdir()):
        if f.name != ".gitkeep":
            print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
