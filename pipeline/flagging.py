from __future__ import annotations

"""Layer 2 — Flagging engine.

Scores and ranks findings from Layer 1 to surface what's worth investigating.
Each function returns a DataFrame of flagged items sorted by strength.
"""

import numpy as np
import pandas as pd
from scipy import stats

from pipeline.analyze import (
    pairwise_correlations,
    detect_changepoints,
    time_series_trends,
)


# ---------------------------------------------------------------------------
# Correlation flags
# ---------------------------------------------------------------------------

def flag_correlations(
    df: pd.DataFrame,
    threshold: float = 0.5,
) -> pd.DataFrame:
    """Flag strongly correlated pairs above the threshold."""
    result = pairwise_correlations(df, threshold=threshold)
    summary = result["summary"]
    if summary.empty or "note" in summary.columns:
        return pd.DataFrame({"note": ["No strong correlations found."]})

    summary["flag_type"] = "correlation"
    summary["strength"] = summary["abs_max"].apply(_strength_label)
    summary["description"] = summary.apply(
        lambda r: f"{r['var_a']} and {r['var_b']}: "
                  f"Pearson r={r['pearson_r']}, Spearman r={r['spearman_r']}",
        axis=1,
    )
    return summary.sort_values("abs_max", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Changepoint clusters
# ---------------------------------------------------------------------------

def flag_changepoint_clusters(
    df: pd.DataFrame,
    time_col: str = "year",
    window: int = 2,
) -> pd.DataFrame:
    """Find years where multiple indicators have changepoints within ±window years."""
    cp = detect_changepoints(df, time_col=time_col)
    summary = cp["summary"]
    if summary.empty or "note" in summary.columns:
        return pd.DataFrame({"note": ["No changepoints to cluster."]})

    if "changepoint_at" not in summary.columns:
        return pd.DataFrame({"note": ["No changepoints detected."]})

    cp_years = summary[["indicator", "changepoint_at", "shift_magnitude"]].copy()

    clusters = []
    unique_years = sorted(cp_years["changepoint_at"].unique())
    for year in unique_years:
        nearby = cp_years[
            (cp_years["changepoint_at"] >= year - window) &
            (cp_years["changepoint_at"] <= year + window)
        ]
        if len(nearby) >= 2:
            indicators = ", ".join(nearby["indicator"].unique())
            clusters.append({
                "cluster_year": year,
                "num_indicators": len(nearby["indicator"].unique()),
                "indicators": indicators,
                "flag_type": "changepoint_cluster",
                "strength": "strong" if len(nearby["indicator"].unique()) >= 3 else "moderate",
                "description": f"{len(nearby['indicator'].unique())} indicators shifted near {year}: {indicators}",
            })

    if not clusters:
        return pd.DataFrame({"note": ["No changepoint clusters found."]})

    result = pd.DataFrame(clusters)
    return result.drop_duplicates(subset=["indicators"]).sort_values(
        "num_indicators", ascending=False
    ).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Divergence flags
# ---------------------------------------------------------------------------

def flag_divergences(
    df: pd.DataFrame,
    time_col: str = "year",
    config: dict | None = None,
) -> pd.DataFrame:
    """Flag pairs of indicators whose trends move in opposite directions.

    Optionally uses direction_of_good from config indicators to highlight
    pairs where one is improving while the other is worsening.
    """
    trends = time_series_trends(df, time_col=time_col)
    summary = trends["summary"]
    if summary.empty or "note" in summary.columns:
        return pd.DataFrame({"note": ["Not enough trend data."]})

    direction_map = {}
    if config:
        for ind in config.get("indicators", []):
            direction_map[ind["name"]] = ind.get("direction_of_good")

    rising = summary[summary["direction"] == "rising"]
    falling = summary[summary["direction"] == "falling"]

    rows = []
    for _, r in rising.iterrows():
        for _, f in falling.iterrows():
            r_good = direction_map.get(r["indicator"])
            f_good = direction_map.get(f["indicator"])
            narrative_note = ""
            if r_good == "lower":
                narrative_note += f"{r['indicator']} is rising but lower is better. "
            if f_good == "higher":
                narrative_note += f"{f['indicator']} is falling but higher is better. "

            rows.append({
                "rising_indicator": r["indicator"],
                "falling_indicator": f["indicator"],
                "rising_slope": r["slope_per_year"],
                "falling_slope": f["slope_per_year"],
                "flag_type": "divergence",
                "strength": "strong" if narrative_note else "moderate",
                "narrative_note": narrative_note.strip() if narrative_note else "Opposite trends detected.",
                "description": f"{r['indicator']} (rising) vs {f['indicator']} (falling)",
            })

    if not rows:
        return pd.DataFrame({"note": ["No divergences found."]})

    return pd.DataFrame(rows).sort_values("strength", ascending=True).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Outlier regions
# ---------------------------------------------------------------------------

def flag_outlier_regions(
    df: pd.DataFrame,
    geo_col: str = "state",
    z_threshold: float = 2.0,
) -> pd.DataFrame:
    """Flag geographic regions that are statistical outliers on any indicator."""
    if geo_col not in df.columns:
        return pd.DataFrame({"note": [f"No '{geo_col}' column."]})

    numeric_cols = [c for c in df.select_dtypes(include="number").columns if c != geo_col]
    geo_means = df.groupby(geo_col)[numeric_cols].mean()

    rows = []
    for col in numeric_cols:
        data = geo_means[col].dropna()
        if data.empty or data.std() == 0:
            continue
        z = ((data - data.mean()) / data.std())
        outliers = z[z.abs() > z_threshold]
        for region, z_val in outliers.items():
            rows.append({
                "indicator": col,
                "region": region,
                "value": round(data[region], 4),
                "z_score": round(z_val, 4),
                "direction": "high" if z_val > 0 else "low",
                "flag_type": "outlier_region",
                "strength": "strong" if abs(z_val) > 3.0 else "moderate",
                "description": f"{region} is a {('high' if z_val > 0 else 'low')} outlier on {col} (z={z_val:.2f})",
            })

    if not rows:
        return pd.DataFrame({"note": ["No outlier regions found."]})
    return pd.DataFrame(rows).sort_values("z_score", key=abs, ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Custom hypothesis tests
# ---------------------------------------------------------------------------

def test_hypotheses(
    datasets: dict[str, pd.DataFrame],
    hypotheses: list[dict],
    config: dict,
) -> list[dict]:
    """Run basic tests for custom hypotheses defined in config.yaml.

    For v1, this does a simple correlation check between the listed indicators.
    Full pattern-based testing is in pipeline/patterns.py.
    """
    results = []
    all_cols = set()
    for df in datasets.values():
        all_cols.update(df.columns)

    for hyp in hypotheses:
        name = hyp.get("name", "Unnamed")
        pattern = hyp.get("pattern", "unknown")
        indicators = hyp.get("indicators", [])

        missing = [i for i in indicators if i not in all_cols]
        if missing:
            results.append({
                "name": name,
                "pattern": pattern,
                "summary": f"Missing indicators in data: {missing}",
                "figure": None,
            })
            continue

        # Find a dataset that contains the needed indicators
        target_df = None
        for df in datasets.values():
            if all(i in df.columns for i in indicators):
                target_df = df
                break

        if target_df is None:
            results.append({
                "name": name,
                "pattern": pattern,
                "summary": "Indicators span multiple datasets. Merge needed.",
                "figure": None,
            })
            continue

        corr = target_df[indicators].corr()
        results.append({
            "name": name,
            "pattern": pattern,
            "summary": f"Correlation matrix for hypothesis indicators:\n{corr.round(3).to_string()}",
            "figure": None,
        })

    return results


# ---------------------------------------------------------------------------
# Compiled findings summary
# ---------------------------------------------------------------------------

def compile_findings_summary(
    datasets: dict[str, pd.DataFrame],
    config: dict,
    correlation_threshold: float = 0.5,
    time_col: str = "year",
    geo_col: str = "state",
) -> pd.DataFrame:
    """Compile all flags into a single ranked findings summary."""
    all_flags = []

    for name, df in datasets.items():
        corr_flags = flag_correlations(df, threshold=correlation_threshold)
        if "note" not in corr_flags.columns:
            corr_flags["dataset"] = name
            all_flags.append(corr_flags[["dataset", "flag_type", "strength", "description"]])

        cp_flags = flag_changepoint_clusters(df, time_col=time_col)
        if "note" not in cp_flags.columns:
            cp_flags["dataset"] = name
            all_flags.append(cp_flags[["dataset", "flag_type", "strength", "description"]])

        div_flags = flag_divergences(df, time_col=time_col, config=config)
        if "note" not in div_flags.columns:
            div_flags["dataset"] = name
            all_flags.append(div_flags[["dataset", "flag_type", "strength", "description"]])

        outlier_flags = flag_outlier_regions(df, geo_col=geo_col)
        if "note" not in outlier_flags.columns:
            outlier_flags["dataset"] = name
            all_flags.append(outlier_flags[["dataset", "flag_type", "strength", "description"]])

    if not all_flags:
        return pd.DataFrame({"note": ["No findings flagged."]})

    combined = pd.concat(all_flags, ignore_index=True)
    strength_order = {"strong": 0, "moderate": 1, "weak": 2}
    combined["_sort"] = combined["strength"].map(strength_order).fillna(3)
    combined = combined.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)
    combined.index.name = "rank"
    return combined


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strength_label(abs_val: float) -> str:
    if abs_val >= 0.8:
        return "strong"
    elif abs_val >= 0.5:
        return "moderate"
    return "weak"
