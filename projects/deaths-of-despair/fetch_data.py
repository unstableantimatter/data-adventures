#!/usr/bin/env python3
"""Fetch raw data files for the Deaths of Despair study.

Sources fetched programmatically:
  - CDC NCHS Drug Overdose Mortality by State (Socrata API)
  - CDC NCHS Leading Causes of Death — Suicide filter (Socrata API)
  - FRED: State manufacturing employment + unemployment rates
  - Census ACS API: Median income + poverty by state

Usage: python projects/deaths-of-despair/fetch_data.py
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
import urllib.parse
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# State reference tables
# ---------------------------------------------------------------------------

STATE_ABBRS = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
    "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
    "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
    "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC",
]

STATE_FIPS = {
    "AL":"01","AK":"02","AZ":"04","AR":"05","CA":"06","CO":"08","CT":"09",
    "DE":"10","FL":"12","GA":"13","HI":"15","ID":"16","IL":"17","IN":"18",
    "IA":"19","KS":"20","KY":"21","LA":"22","ME":"23","MD":"24","MA":"25",
    "MI":"26","MN":"27","MS":"28","MO":"29","MT":"30","NE":"31","NV":"32",
    "NH":"33","NJ":"34","NM":"35","NY":"36","NC":"37","ND":"38","OH":"39",
    "OK":"40","OR":"41","PA":"42","RI":"44","SC":"45","SD":"46","TN":"47",
    "TX":"48","UT":"49","VT":"50","VA":"51","WA":"53","WV":"54","WI":"55",
    "WY":"56","DC":"11",
}


# ---------------------------------------------------------------------------
# Helpers — all HTTP via curl subprocess to avoid urllib rate-limit issues
# ---------------------------------------------------------------------------

def _curl(url: str, timeout: int = 30) -> bytes | None:
    """Fetch URL bytes via curl. Returns None on failure."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), "-L", url],
            capture_output=True, timeout=timeout + 5
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
        return None
    except Exception as e:
        print(f"  curl error: {e}")
        return None


def fetch_url(url: str, dest: Path) -> bool:
    data = _curl(url)
    if data is None:
        print(f"  FAIL: {dest.name}")
        return False
    if data[:15].lstrip().startswith(b"<!DOCTYPE") or data[:6].lstrip().startswith(b"<html"):
        print(f"  SKIP (got HTML): {dest.name}")
        return False
    dest.write_bytes(data)
    print(f"  OK: {dest.name} ({len(data):,} bytes)")
    return True


def fetch_socrata(dataset_id: str, dest: Path, query_params: dict | None = None,
                  limit: int = 50000) -> bool:
    """Fetch a CDC Socrata dataset as JSON and save."""
    params = {"$limit": str(limit)}
    if query_params:
        params.update(query_params)
    qs = urllib.parse.urlencode(params)
    url = f"https://data.cdc.gov/resource/{dataset_id}.json?{qs}"
    data = _curl(url, timeout=60)
    if data is None:
        print(f"  FAIL: {dest.name}")
        return False
    try:
        records = json.loads(data)
        dest.write_text(json.dumps(records, indent=2))
        print(f"  OK: {dest.name} ({len(records):,} records)")
        return True
    except Exception as e:
        print(f"  FAIL parse: {dest.name} — {e}")
        return False


def fetch_fred_csv(series_id: str) -> str | None:
    """Fetch a FRED CSV series via curl (avoids Python urllib rate-limiting)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", url],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout and "observation_date" in result.stdout:
            return result.stdout
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# CDC: Drug overdose deaths by state
# ---------------------------------------------------------------------------

def fetch_cdc_overdose() -> None:
    """CDC NCHS: Drug Poisoning Mortality by State, 1999-2021.

    Uses dataset jx6g-fdh6 which already has totals (Both Sexes, All Ages,
    All Races-All Origins) per state per year.
    """
    dest = RAW_DIR / "cdc_overdose_by_state.json"
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"  EXISTS: {dest.name}")
        return
    fetch_socrata("jx6g-fdh6", dest, query_params={
        "sex": "Both Sexes",
        "age": "All Ages",
        "race_hispanic_origin": "All Races-All Origins",
        "$where": "state!='United States'",
    })


# ---------------------------------------------------------------------------
# CDC: Suicide deaths by state (Leading Causes of Death dataset)
# ---------------------------------------------------------------------------

def fetch_cdc_suicide() -> None:
    """CDC NCHS: Suicide deaths by state, 1999-2020.

    Uses NCHS Leading Causes of Death dataset (bi63-dtpu).
    The 'aadr' column is the age-adjusted death rate per 100k.
    """
    dest = RAW_DIR / "cdc_suicide_by_state.json"
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"  EXISTS: {dest.name}")
        return
    fetch_socrata("bi63-dtpu", dest, query_params={
        "cause_name": "Suicide",
        "$where": "state!='United States'",
    })


# ---------------------------------------------------------------------------
# FRED: State manufacturing employment
# ---------------------------------------------------------------------------

def fetch_fred_manufacturing() -> None:
    """FRED: All-employee manufacturing by state (thousands)."""
    dest = RAW_DIR / "fred_manufacturing_by_state.csv"
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"  EXISTS: {dest.name}")
        return

    rows: list[list] = [["state_abbr", "date", "manufacturing_employees_thousands"]]

    # A subset of states known to have this FRED series; others have low coverage
    # Series: {ABBR}MFG — All Employees: Manufacturing in [State] (thousands)
    for abbr in STATE_ABBRS:
        series_id = f"{abbr}MFG"
        content = fetch_fred_csv(series_id)
        if content:
            lines = content.strip().split("\n")
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) == 2 and parts[1].strip() not in (".", ""):
                    rows.append([abbr, parts[0].strip(), parts[1].strip()])
        else:
            print(f"  FRED {series_id}: no data")
        time.sleep(0.1)

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1:,} rows)")
    time.sleep(3)  # Pause before next batch of FRED calls


# ---------------------------------------------------------------------------
# FRED: State unemployment rates
# ---------------------------------------------------------------------------

def fetch_fred_unemployment() -> None:
    """FRED: State unemployment rates (seasonally adjusted)."""
    dest = RAW_DIR / "fred_unemployment_by_state.csv"
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"  EXISTS: {dest.name}")
        return

    rows: list[list] = [["state_abbr", "date", "unemployment_rate"]]

    # Series: {ABBR}UR — Unemployment Rate in [State]
    for abbr in STATE_ABBRS:
        series_id = f"{abbr}UR"
        content = fetch_fred_csv(series_id)
        if content:
            lines = content.strip().split("\n")
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) == 2 and parts[1].strip() not in (".", ""):
                    rows.append([abbr, parts[0].strip(), parts[1].strip()])
        else:
            print(f"  FRED {series_id}: no data")
        time.sleep(0.1)

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1:,} rows)")


# ---------------------------------------------------------------------------
# Census ACS: Income and poverty by state
# ---------------------------------------------------------------------------

def fetch_census_income() -> None:
    """Census ACS 1-year: Median household income by state, 2005-2023."""
    dest = RAW_DIR / "acs_median_income_by_state.csv"
    if dest.exists() and dest.stat().st_size > 5_000:
        print(f"  EXISTS: {dest.name}")
        return

    rows = [["year", "state_fips", "state_name", "median_household_income"]]
    for year in range(2005, 2024):
        if year == 2020:
            continue
        url = f"https://api.census.gov/data/{year}/acs/acs1?get=NAME,B19013_001E&for=state:*"
        data = _curl(url, timeout=30)
        if data is None:
            print(f"  Census income {year}: no response")
            continue
        try:
            records = json.loads(data)
            for row in records[1:]:
                name, income, fips = row
                if income and income not in ("null", "-1"):
                    rows.append([str(year), fips, name, income])
        except Exception as e:
            print(f"  Census income {year}: {e}")

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


def fetch_census_poverty() -> None:
    """Census ACS 1-year: Poverty rate by state, 2005-2023."""
    dest = RAW_DIR / "acs_poverty_by_state.csv"
    if dest.exists() and dest.stat().st_size > 5_000:
        print(f"  EXISTS: {dest.name}")
        return

    rows = [["year", "state_fips", "state_name", "poverty_pct"]]
    for year in range(2005, 2024):
        if year == 2020:
            continue
        url = (f"https://api.census.gov/data/{year}/acs/acs1?"
               f"get=NAME,B17001_001E,B17001_002E&for=state:*")
        data = _curl(url, timeout=30)
        if data is None:
            print(f"  Census poverty {year}: no response")
            continue
        try:
            records = json.loads(data)
            for row in records[1:]:
                name, total, below, fips = row
                if total and below and total not in ("null", "-1"):
                    pct = round(int(below) / int(total) * 100, 2)
                    rows.append([str(year), fips, name, str(pct)])
        except Exception as e:
            print(f"  Census poverty {year}: {e}")

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


# ---------------------------------------------------------------------------
# FRED: National series
# ---------------------------------------------------------------------------

def fetch_fred_national() -> None:
    """FRED: national median income and poverty rate."""
    series = {
        "MEHOINUSA672N": "fred_median_income_national.csv",
        "PPAAUS00000A156NCEN": "fred_poverty_rate_national.csv",
    }
    for series_id, filename in series.items():
        dest = RAW_DIR / filename
        if dest.exists() and dest.stat().st_size > 100:
            print(f"  EXISTS: {dest.name}")
            continue
        content = fetch_fred_csv(series_id)
        if content:
            dest.write_text(content)
            print(f"  OK: {dest.name} ({len(content):,} bytes)")
        else:
            print(f"  FAIL: {dest.name}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Fetching raw data for Deaths of Despair study ===\n")

    print("[CDC NCHS] Drug overdose deaths by state...")
    fetch_cdc_overdose()

    print("\n[CDC NCHS] Suicide deaths by state...")
    fetch_cdc_suicide()

    print("\n[FRED] State manufacturing employment (this takes ~2 min, ~51 series)...")
    fetch_fred_manufacturing()

    print("\n[FRED] State unemployment rates (~51 series)...")
    fetch_fred_unemployment()

    print("\n[Census ACS] Median income by state...")
    fetch_census_income()

    print("\n[Census ACS] Poverty rate by state...")
    fetch_census_poverty()

    print("\n[FRED] National median income + poverty...")
    fetch_fred_national()

    print("\n=== Done ===")
    print(f"\nFiles in {RAW_DIR}:")
    for f in sorted(RAW_DIR.iterdir()):
        if f.name != ".gitkeep":
            print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
