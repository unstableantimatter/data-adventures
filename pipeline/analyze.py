"""Layer 1 — Automatic descriptive pass.

Provides functions for univariate profiles, time series trends, changepoint
detection, pairwise correlations, and geographic variation. Each function
takes a DataFrame and returns a dict with a summary DataFrame and optional
Plotly figures.
"""

import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats


# ---------------------------------------------------------------------------
# Univariate profiles
# ---------------------------------------------------------------------------

def univariate_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics for all numeric columns."""
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return pd.DataFrame({"note": ["No numeric columns found."]})

    profile = numeric.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T
    profile["missing_pct"] = (numeric.isnull().sum() / len(numeric) * 100).round(2)
    profile["zeros_pct"] = ((numeric == 0).sum() / len(numeric) * 100).round(2)

    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1
    outlier_low = numeric.lt(q1 - 1.5 * iqr).sum()
    outlier_high = numeric.gt(q3 + 1.5 * iqr).sum()
    profile["outliers_low"] = outlier_low
    profile["outliers_high"] = outlier_high

    return profile.round(4)


# ---------------------------------------------------------------------------
# Time series trends
# ---------------------------------------------------------------------------

def time_series_trends(
    df: pd.DataFrame,
    time_col: str = "year",
) -> dict:
    """Compute trend direction and rate of change for each numeric column over time.

    Returns dict with 'summary' DataFrame and 'figures' list of Plotly figures.
    """
    if time_col not in df.columns:
        return {"summary": pd.DataFrame(), "figures": []}

    numeric_cols = [c for c in df.select_dtypes(include="number").columns if c != time_col]
    if not numeric_cols:
        return {"summary": pd.DataFrame({"note": ["No numeric columns."]}), "figures": []}

    agg = df.groupby(time_col)[numeric_cols].mean().sort_index()

    rows = []
    figures = []
    for col in numeric_cols:
        series = agg[col].dropna()
        if len(series) < 3:
            continue
        x = series.index.astype(float).values
        y = series.values
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        direction = "rising" if slope > 0 else "falling" if slope < 0 else "flat"
        rows.append({
            "indicator": col,
            "direction": direction,
            "slope_per_year": round(slope, 6),
            "r_squared": round(r_value ** 2, 4),
            "p_value": round(p_value, 6),
            "start_value": round(y[0], 4),
            "end_value": round(y[-1], 4),
        })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=series.index, y=y, mode="lines+markers", name=col))
        trend_y = slope * x + intercept
        fig.add_trace(go.Scatter(x=series.index, y=trend_y, mode="lines",
                                  name=f"trend ({direction})", line=dict(dash="dash")))
        fig.update_layout(title=f"{col} over time", xaxis_title=time_col, yaxis_title=col)
        figures.append(fig)

    summary = pd.DataFrame(rows)
    return {"summary": summary, "figures": figures}


# ---------------------------------------------------------------------------
# Changepoint detection
# ---------------------------------------------------------------------------

def detect_changepoints(
    df: pd.DataFrame,
    time_col: str = "year",
    min_size: int = 3,
    pen: float = 3.0,
) -> dict:
    """Detect changepoints in each numeric column's time series.

    Uses the ruptures library (Pelt algorithm). Returns dict with 'summary'
    DataFrame and 'figures' list.
    """
    try:
        import ruptures as rpt
    except ImportError:
        return {
            "summary": pd.DataFrame({"error": ["ruptures not installed. pip install ruptures"]}),
            "figures": [],
        }

    if time_col not in df.columns:
        return {"summary": pd.DataFrame(), "figures": []}

    numeric_cols = [c for c in df.select_dtypes(include="number").columns if c != time_col]
    agg = df.groupby(time_col)[numeric_cols].mean().sort_index()

    rows = []
    figures = []
    for col in numeric_cols:
        series = agg[col].dropna()
        if len(series) < min_size * 2:
            continue

        signal = series.values
        algo = rpt.Pelt(model="rbf", min_size=min_size).fit(signal)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            breakpoints = algo.predict(pen=pen)

        # breakpoints are indices; map back to time values
        bp_indices = [b for b in breakpoints if b < len(series)]
        bp_times = [series.index[b] for b in bp_indices if b < len(series.index)]

        if bp_times:
            for bp_time in bp_times:
                bp_idx = list(series.index).index(bp_time)
                before_mean = series.iloc[:bp_idx].mean() if bp_idx > 0 else np.nan
                after_mean = series.iloc[bp_idx:].mean() if bp_idx < len(series) else np.nan
                rows.append({
                    "indicator": col,
                    "changepoint_at": bp_time,
                    "mean_before": round(before_mean, 4),
                    "mean_after": round(after_mean, 4),
                    "shift_magnitude": round(after_mean - before_mean, 4),
                })

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(series.index), y=signal, mode="lines+markers", name=col))
        for bp_time in bp_times:
            fig.add_vline(x=bp_time, line_dash="dash", line_color="red",
                          annotation_text=f"shift @ {bp_time}")
        fig.update_layout(title=f"{col} — changepoints", xaxis_title=time_col, yaxis_title=col)
        figures.append(fig)

    summary = pd.DataFrame(rows) if rows else pd.DataFrame({"note": ["No changepoints detected."]})
    return {"summary": summary, "figures": figures}


# ---------------------------------------------------------------------------
# Pairwise correlations
# ---------------------------------------------------------------------------

def pairwise_correlations(
    df: pd.DataFrame,
    threshold: float = 0.5,
) -> dict:
    """Compute Pearson and Spearman correlations for all numeric column pairs.

    Returns dict with 'summary' DataFrame of strong pairs and a 'heatmap' figure.
    """
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return {
            "summary": pd.DataFrame({"note": ["Need at least 2 numeric columns."]}),
            "heatmap": go.Figure(),
        }

    pearson = numeric.corr(method="pearson")
    spearman = numeric.corr(method="spearman")

    rows = []
    cols = list(numeric.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            p_val = pearson.loc[a, b]
            s_val = spearman.loc[a, b]
            if abs(p_val) >= threshold or abs(s_val) >= threshold:
                rows.append({
                    "var_a": a,
                    "var_b": b,
                    "pearson_r": round(p_val, 4),
                    "spearman_r": round(s_val, 4),
                    "abs_max": round(max(abs(p_val), abs(s_val)), 4),
                })

    summary = pd.DataFrame(rows)
    if not summary.empty:
        summary = summary.sort_values("abs_max", ascending=False).reset_index(drop=True)

    heatmap = px.imshow(
        pearson,
        text_auto=".2f",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title="Pearson correlation matrix",
    )

    return {"summary": summary, "heatmap": heatmap}


# ---------------------------------------------------------------------------
# Geographic variation
# ---------------------------------------------------------------------------

def geographic_variation(
    df: pd.DataFrame,
    geo_col: str = "state",
) -> dict:
    """Summarize numeric columns by geographic unit. Flags outlier regions.

    Returns dict with 'summary' DataFrame and 'figures' list.
    """
    if geo_col not in df.columns:
        return {"summary": pd.DataFrame(), "figures": []}

    numeric_cols = [c for c in df.select_dtypes(include="number").columns if c != geo_col]
    if not numeric_cols:
        return {"summary": pd.DataFrame({"note": ["No numeric columns."]}), "figures": []}

    geo_means = df.groupby(geo_col)[numeric_cols].mean()

    rows = []
    figures = []
    for col in numeric_cols:
        col_data = geo_means[col].dropna()
        if col_data.empty:
            continue
        overall_mean = col_data.mean()
        overall_std = col_data.std()
        if overall_std == 0:
            continue

        z_scores = ((col_data - overall_mean) / overall_std).round(4)
        outlier_regions = z_scores[z_scores.abs() > 2.0]

        for region, z in outlier_regions.items():
            rows.append({
                "indicator": col,
                "region": region,
                "value": round(col_data[region], 4),
                "z_score": z,
                "direction": "high" if z > 0 else "low",
            })

        fig = px.bar(
            x=col_data.index, y=col_data.values,
            title=f"{col} by {geo_col}",
            labels={"x": geo_col, "y": col},
        )
        fig.add_hline(y=overall_mean, line_dash="dash", annotation_text="mean")
        figures.append(fig)

    summary = pd.DataFrame(rows) if rows else pd.DataFrame({"note": ["No geographic outliers."]})
    return {"summary": summary, "figures": figures}
