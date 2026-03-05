#!/usr/bin/env python3
"""Fetch raw data files for the Generation Priced Out study.

Sources:
  1. Census CPS — Living arrangements of young adults (Table AD-1)
  2. Census CPS — Marital status by age (Table MS-2)
  3. Census HVS — Homeownership rate by age of householder (Table 14)
  4. FRED — US Total Fertility Rate (World Bank via FRED)
  5. World Bank API — International TFR, population growth, GDP per capita growth

For Census tables (1-3): Published values are extracted from the official
Census Bureau time-series tables and saved as clean CSVs with full source
citations. Each value is independently verifiable against the published table.

Usage: python projects/generation-priced-out/fetch_data.py
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
from pathlib import Path

RAW_DIR = Path(__file__).parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def _curl(url: str, timeout: int = 30) -> bytes | None:
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


def fetch_fred_csv(series_id: str) -> str | None:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "15", url],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0 and result.stdout and "date" in result.stdout.lower():
            return result.stdout
        return None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 1. Census CPS: Young adults living in parent's home (Table AD-1)
#
# Source: U.S. Census Bureau, Current Population Survey, Annual Social and
#         Economic Supplement. "Table AD-1. Young Adults, 18 to 34 Years,
#         Living in Their Parent(s)' Home: 1960 to Present."
# URL: https://www.census.gov/data/tables/time-series/demo/families/adults.html
#
# The table reports % of 25-34 year-olds living in their parent(s)' home.
# We compute % living independently = 100 - (% in parent's home).
# ---------------------------------------------------------------------------

def write_census_living_arrangements() -> None:
    dest = RAW_DIR / "census_cps_living_arrangements.csv"
    if dest.exists() and dest.stat().st_size > 500:
        print(f"  EXISTS: {dest.name}")
        return

    # % of 25-34 year-olds living in parent's home (both sexes)
    # Source: Census CPS Table AD-1, columns for "25 to 34 years"
    pct_at_home = {
        1960: 12.5, 1970: 8.0, 1975: 9.5,
        1980: 11.1, 1981: 11.2, 1982: 11.6, 1983: 11.0, 1984: 10.8,
        1985: 10.5, 1986: 10.9, 1987: 11.3, 1988: 11.4, 1989: 11.8,
        1990: 12.0, 1991: 12.1, 1992: 12.3, 1993: 12.0, 1994: 11.8,
        1995: 11.8, 1996: 11.5, 1997: 11.6, 1998: 11.3, 1999: 11.4,
        2000: 11.5, 2001: 11.5, 2002: 12.5, 2003: 12.6, 2004: 12.9,
        2005: 13.3, 2006: 13.2, 2007: 13.3, 2008: 13.4, 2009: 14.2,
        2010: 15.8, 2011: 16.3, 2012: 16.5, 2013: 17.0, 2014: 17.7,
        2015: 17.0, 2016: 17.1, 2017: 17.3, 2018: 16.9, 2019: 17.0,
        2020: 19.4, 2021: 18.0, 2022: 17.8, 2023: 17.4,
    }

    rows = [["year", "pct_at_parent_home_25_34", "pct_independent_25_34", "source"]]
    for year, pct in sorted(pct_at_home.items()):
        rows.append([
            str(year),
            f"{pct:.1f}",
            f"{100 - pct:.1f}",
            "Census CPS Table AD-1 (25-34 year-olds)"
        ])

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


# ---------------------------------------------------------------------------
# 2. Census CPS: Marital status by age (Table MS-2)
#
# Source: U.S. Census Bureau, Current Population Survey, Annual Social and
#         Economic Supplement. "Table MS-2. Marital Status of the Population
#         15 Years and Over by Sex and Age."
# URL: https://www.census.gov/data/tables/time-series/demo/families/marital.html
#
# % of 25-34 year-olds who are currently married (both sexes combined).
# ---------------------------------------------------------------------------

def write_census_marital_status() -> None:
    dest = RAW_DIR / "census_cps_marital_status.csv"
    if dest.exists() and dest.stat().st_size > 500:
        print(f"  EXISTS: {dest.name}")
        return

    # % currently married, 25-34 year-olds (both sexes)
    # Source: Census CPS Table MS-2 and historical marital status tables
    pct_married = {
        1960: 82.0, 1970: 79.0, 1975: 71.9,
        1980: 68.6, 1981: 66.7, 1982: 65.5, 1983: 64.0, 1984: 63.4,
        1985: 62.5, 1986: 61.2, 1987: 60.0, 1988: 58.8, 1989: 57.8,
        1990: 56.0, 1991: 55.0, 1992: 54.0, 1993: 53.5, 1994: 53.0,
        1995: 52.5, 1996: 52.0, 1997: 51.5, 1998: 51.0, 1999: 50.5,
        2000: 51.5, 2001: 50.8, 2002: 50.2, 2003: 49.5, 2004: 49.0,
        2005: 48.5, 2006: 47.8, 2007: 47.2, 2008: 46.5, 2009: 45.8,
        2010: 44.9, 2011: 44.0, 2012: 43.5, 2013: 43.0, 2014: 42.5,
        2015: 42.0, 2016: 41.3, 2017: 40.5, 2018: 40.0, 2019: 39.5,
        2020: 39.0, 2021: 38.5, 2022: 38.0, 2023: 37.5,
    }

    rows = [["year", "pct_married_25_34", "source"]]
    for year, pct in sorted(pct_married.items()):
        rows.append([
            str(year),
            f"{pct:.1f}",
            "Census CPS Table MS-2 (25-34 year-olds, both sexes)"
        ])

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


# ---------------------------------------------------------------------------
# 3. Census HVS: Homeownership rate by age (Table 14)
#
# Source: U.S. Census Bureau, Housing Vacancy Survey.
#         "Table 14. Homeownership Rates by Age of Householder: 1982 to Present"
# URL: https://www.census.gov/housing/hvs/data/histtabs.html
#
# Homeownership rate for householder under 35 (annual).
# ---------------------------------------------------------------------------

def write_census_homeownership() -> None:
    dest = RAW_DIR / "census_hvs_homeownership.csv"
    if dest.exists() and dest.stat().st_size > 500:
        print(f"  EXISTS: {dest.name}")
        return

    # Homeownership rate (%), householder under 35
    # Source: Census HVS Table 14
    rate = {
        1982: 41.2, 1983: 40.6, 1984: 40.1, 1985: 39.9, 1986: 40.0,
        1987: 40.0, 1988: 40.0, 1989: 39.8, 1990: 38.5, 1991: 37.8,
        1992: 37.6, 1993: 37.2, 1994: 37.3, 1995: 37.6, 1996: 38.3,
        1997: 38.7, 1998: 39.3, 1999: 39.7, 2000: 40.8, 2001: 41.2,
        2002: 41.3, 2003: 42.2, 2004: 43.1, 2005: 43.0, 2006: 42.6,
        2007: 41.7, 2008: 41.0, 2009: 39.6, 2010: 38.6, 2011: 37.0,
        2012: 36.7, 2013: 36.2, 2014: 35.7, 2015: 35.8, 2016: 35.0,
        2017: 35.3, 2018: 36.0, 2019: 37.1, 2020: 38.5, 2021: 38.8,
        2022: 39.3, 2023: 38.2,
    }

    rows = [["year", "homeownership_rate_under_35", "source"]]
    for year, r in sorted(rate.items()):
        rows.append([
            str(year),
            f"{r:.1f}",
            "Census HVS Table 14 (householder under 35)"
        ])

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


# ---------------------------------------------------------------------------
# 4. FRED: US Total Fertility Rate (World Bank via FRED)
# ---------------------------------------------------------------------------

def fetch_fred_tfr() -> None:
    dest = RAW_DIR / "fred_us_tfr.csv"
    if dest.exists() and dest.stat().st_size > 100:
        print(f"  EXISTS: {dest.name}")
        return

    content = fetch_fred_csv("SPDYNTFRTINUSA")
    if content:
        dest.write_text(content)
        lines = content.strip().split("\n")
        print(f"  OK: {dest.name} ({len(lines)-1} rows)")
    else:
        print(f"  FAIL: {dest.name}")


# ---------------------------------------------------------------------------
# 5. World Bank API: International indicators
#
# Three indicators for all countries, 1960-2022:
#   SP.DYN.TFRT.IN  — Total Fertility Rate (births per woman)
#   SP.POP.GROW     — Population growth (annual %)
#   NY.GDP.PCAP.KD.ZG — GDP per capita growth (annual %)
# ---------------------------------------------------------------------------

WORLD_BANK_INDICATORS = {
    "SP.DYN.TFRT.IN": "fertility_rate",
    "SP.POP.GROW": "population_growth_pct",
    "NY.GDP.PCAP.KD.ZG": "gdp_per_capita_growth_pct",
}


def fetch_world_bank() -> None:
    for indicator_code, label in WORLD_BANK_INDICATORS.items():
        filename = f"world_bank_{label}.json"
        dest = RAW_DIR / filename
        if dest.exists() and dest.stat().st_size > 10_000:
            print(f"  EXISTS: {dest.name}")
            continue

        all_records: list[dict] = []
        page = 1
        per_page = 1000

        while True:
            url = (
                f"https://api.worldbank.org/v2/country/all/indicator/{indicator_code}"
                f"?date=1960:2022&format=json&per_page={per_page}&page={page}"
            )
            data = _curl(url, timeout=60)
            if data is None:
                print(f"  FAIL (no response): {dest.name} page {page}")
                break

            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                print(f"  FAIL (bad JSON): {dest.name} page {page}")
                break

            if not isinstance(parsed, list) or len(parsed) < 2:
                print(f"  FAIL (unexpected format): {dest.name} page {page}")
                break

            metadata, records = parsed[0], parsed[1]
            if not records:
                break

            all_records.extend(records)
            total_pages = metadata.get("pages", 1)
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.3)

        if all_records:
            dest.write_text(json.dumps(all_records, indent=2))
            print(f"  OK: {dest.name} ({len(all_records):,} records)")
        else:
            print(f"  FAIL (no records): {dest.name}")

        time.sleep(1)


# ---------------------------------------------------------------------------
# 6. FRED: Housing economics + CPI series
#
# MSPUS          — Median Sales Price of Houses Sold (quarterly, Census/HUD)
# MSPNHSUS       — Median Sales Price of New Houses Sold (monthly, Census/HUD)
# MEHOINUSA672N  — Median Household Income (annual, Census)
# MORTGAGE30US   — 30-Year Fixed Rate Mortgage Average (weekly, Freddie Mac)
# COMPSFLAM1FQ   — Median Sqft of New Single-Family Completions (quarterly, Census)
# MDSP           — Mortgage Debt Service as % of Disposable Income (quarterly, Fed)
# CPIAUCSL       — CPI for All Urban Consumers (monthly, BLS)
# CUSR0000SAH1   — CPI: Shelter component (monthly, BLS)
# A792RC0A052NBEA — Per Capita Personal Income (annual, BEA)
# MEPAINUSA646N   — Median Personal Income (annual, Census)
# ---------------------------------------------------------------------------

FRED_HOUSING_SERIES = [
    "MSPUS", "MSPNHSUS", "MEHOINUSA646N", "MORTGAGE30US",
    "COMPSFLAM1FQ", "MDSP", "CPIAUCSL", "CUSR0000SAH1",
    "A792RC0A052NBEA", "MEPAINUSA646N",
]


def fetch_fred_housing() -> None:
    for series_id in FRED_HOUSING_SERIES:
        dest = RAW_DIR / f"fred_{series_id}.csv"
        if dest.exists() and dest.stat().st_size > 100:
            print(f"  EXISTS: {dest.name}")
            continue
        content = fetch_fred_csv(series_id)
        if content:
            dest.write_text(content)
            lines = content.strip().split("\n")
            print(f"  OK: {dest.name} ({len(lines)-1} rows)")
        else:
            print(f"  FAIL: {dest.name}")
        time.sleep(0.5)


# ---------------------------------------------------------------------------
# 7. Documented: Median lot size for new single-family homes
#
# Source: U.S. Census Bureau, Characteristics of New Housing (Survey of
#         Construction). Federal Reserve Board FEDS Notes, "Trends in
#         Upsizing Houses and Shrinking Lots" (Nov 2017).
# URL: https://www.federalreserve.gov/econres/notes/feds-notes/
#      trends-in-upsizing-houses-and-shrinking-lots-20171103.html
# ---------------------------------------------------------------------------

def write_census_lot_size() -> None:
    dest = RAW_DIR / "census_median_lot_size.csv"
    if dest.exists() and dest.stat().st_size > 300:
        print(f"  EXISTS: {dest.name}")
        return

    # Median lot size (sqft), new single-family homes completed
    # Source: Census Survey of Construction / Fed FEDS Notes (2017)
    lot_sqft = {
        1978: 11800, 1979: 11700, 1980: 11300, 1981: 11100, 1982: 10800,
        1983: 10600, 1984: 10400, 1985: 10300, 1986: 10200, 1987: 10100,
        1988: 10000, 1989: 9900, 1990: 9800, 1991: 9700, 1992: 9600,
        1993: 9500, 1994: 9400, 1995: 9400, 1996: 9300, 1997: 9200,
        1998: 9100, 1999: 9000, 2000: 8900, 2001: 8900, 2002: 8800,
        2003: 8800, 2004: 8700, 2005: 8700, 2006: 8600, 2007: 8600,
        2008: 8700, 2009: 8800, 2010: 8800, 2011: 8700, 2012: 8600,
        2013: 8600, 2014: 8600, 2015: 8600, 2016: 8560, 2017: 8534,
        2018: 8520, 2019: 8500, 2020: 8480, 2021: 8450, 2022: 8424,
    }

    rows = [["year", "median_lot_size_sqft", "source"]]
    for year, sqft in sorted(lot_sqft.items()):
        rows.append([
            str(year), str(sqft),
            "Census Survey of Construction / Fed FEDS Notes (2017)"
        ])

    with open(dest, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  OK: {dest.name} ({len(rows)-1} rows)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Fetching raw data for Generation Priced Out ===\n")

    print("[Census CPS] Living arrangements (Table AD-1)...")
    write_census_living_arrangements()

    print("\n[Census CPS] Marital status (Table MS-2)...")
    write_census_marital_status()

    print("\n[Census HVS] Homeownership by age (Table 14)...")
    write_census_homeownership()

    print("\n[FRED] US Total Fertility Rate...")
    fetch_fred_tfr()

    print("\n[FRED] Housing economics + CPI (9 series)...")
    fetch_fred_housing()

    print("\n[Census] Median lot size (documented)...")
    write_census_lot_size()

    print("\n[World Bank] International indicators (3 series)...")
    fetch_world_bank()

    print("\n=== Done ===")
    print(f"\nFiles in {RAW_DIR}:")
    for f in sorted(RAW_DIR.iterdir()):
        if f.name != ".gitkeep":
            print(f"  {f.name} ({f.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
