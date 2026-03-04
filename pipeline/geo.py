"""Geographic lookup tables for US states and territories.

Provides consistent mapping between FIPS codes, full names, and postal
abbreviations for all 50 states plus the District of Columbia.
"""

from __future__ import annotations

_STATES: list[tuple[str, str, str]] = [
    ("01", "Alabama", "AL"),
    ("02", "Alaska", "AK"),
    ("04", "Arizona", "AZ"),
    ("05", "Arkansas", "AR"),
    ("06", "California", "CA"),
    ("08", "Colorado", "CO"),
    ("09", "Connecticut", "CT"),
    ("10", "Delaware", "DE"),
    ("11", "District of Columbia", "DC"),
    ("12", "Florida", "FL"),
    ("13", "Georgia", "GA"),
    ("15", "Hawaii", "HI"),
    ("16", "Idaho", "ID"),
    ("17", "Illinois", "IL"),
    ("18", "Indiana", "IN"),
    ("19", "Iowa", "IA"),
    ("20", "Kansas", "KS"),
    ("21", "Kentucky", "KY"),
    ("22", "Louisiana", "LA"),
    ("23", "Maine", "ME"),
    ("24", "Maryland", "MD"),
    ("25", "Massachusetts", "MA"),
    ("26", "Michigan", "MI"),
    ("27", "Minnesota", "MN"),
    ("28", "Mississippi", "MS"),
    ("29", "Missouri", "MO"),
    ("30", "Montana", "MT"),
    ("31", "Nebraska", "NE"),
    ("32", "Nevada", "NV"),
    ("33", "New Hampshire", "NH"),
    ("34", "New Jersey", "NJ"),
    ("35", "New Mexico", "NM"),
    ("36", "New York", "NY"),
    ("37", "North Carolina", "NC"),
    ("38", "North Dakota", "ND"),
    ("39", "Ohio", "OH"),
    ("40", "Oklahoma", "OK"),
    ("41", "Oregon", "OR"),
    ("42", "Pennsylvania", "PA"),
    ("44", "Rhode Island", "RI"),
    ("45", "South Carolina", "SC"),
    ("46", "South Dakota", "SD"),
    ("47", "Tennessee", "TN"),
    ("48", "Texas", "TX"),
    ("49", "Utah", "UT"),
    ("50", "Vermont", "VT"),
    ("51", "Virginia", "VA"),
    ("53", "Washington", "WA"),
    ("54", "West Virginia", "WV"),
    ("55", "Wisconsin", "WI"),
    ("56", "Wyoming", "WY"),
]

FIPS_TO_NAME: dict[str, str] = {f: n for f, n, _ in _STATES}
FIPS_TO_ABBR: dict[str, str] = {f: a for f, _, a in _STATES}
NAME_TO_FIPS: dict[str, str] = {n: f for f, n, _ in _STATES}
NAME_TO_ABBR: dict[str, str] = {n: a for _, n, a in _STATES}
ABBR_TO_FIPS: dict[str, str] = {a: f for f, _, a in _STATES}
ABBR_TO_NAME: dict[str, str] = {a: n for _, n, a in _STATES}

VALID_STATE_FIPS: set[str] = set(FIPS_TO_NAME)


def add_state_ids(
    df: "pd.DataFrame",
    source_col: str,
    source_type: str,
) -> "pd.DataFrame":
    """Add ``state_fips``, ``state_name``, ``state_abbr`` from an existing column.

    Parameters
    ----------
    source_col : str
        Column in *df* that contains the identifier.
    source_type : ``"fips"`` | ``"name"`` | ``"abbr"``
        What kind of identifier *source_col* holds.
    """
    if source_type == "fips":
        df["state_fips"] = df[source_col].astype(str).str.zfill(2)
        df["state_name"] = df["state_fips"].map(FIPS_TO_NAME)
        df["state_abbr"] = df["state_fips"].map(FIPS_TO_ABBR)
    elif source_type == "name":
        cleaned = df[source_col].str.strip()
        df["state_fips"] = cleaned.map(NAME_TO_FIPS)
        df["state_name"] = cleaned
        df["state_abbr"] = cleaned.map(NAME_TO_ABBR)
    elif source_type == "abbr":
        cleaned = df[source_col].str.strip().str.upper()
        df["state_fips"] = cleaned.map(ABBR_TO_FIPS)
        df["state_name"] = cleaned.map(ABBR_TO_NAME)
        df["state_abbr"] = cleaned
    else:
        raise ValueError(f"Unknown source_type: {source_type!r}")
    return df
