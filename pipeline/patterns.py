from __future__ import annotations

"""Narrative reframing patterns and Layer 3 deep-dive analysis functions.

Provides reusable analytical lenses (masking, displacement, divergence,
lag/lead, segmentation, threshold) and standard deep-dive types (regression,
lag analysis, segmented comparison, before/after).

Each function takes DataFrames and variable names, returns a dict with
'summary' (text) and optional 'figure'/'figures' (Plotly).
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

try:
    import statsmodels.api as sm
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_column(datasets: dict[str, pd.DataFrame], col: str) -> tuple[str, pd.DataFrame] | None:
    """Find which dataset contains a column. Returns (dataset_name, df) or None."""
    for name, df in datasets.items():
        if col in df.columns:
            return name, df
    return None


def _merge_indicators(
    datasets: dict[str, pd.DataFrame],
    columns: list[str],
    on: str | None = None,
) -> pd.DataFrame | None:
    """Attempt to merge needed columns from across datasets into one DataFrame."""
    # If all columns are in one dataset, use it directly
    for df in datasets.values():
        if all(c in df.columns for c in columns):
            return df[columns].dropna()

    # Otherwise try merging on a common column
    if on is None:
        common = None
        for df in datasets.values():
            if common is None:
                common = set(df.columns)
            else:
                common &= set(df.columns)
        candidates = [c for c in (common or []) if c not in columns]
        if not candidates:
            return None
        on = candidates[0]

    merged = None
    for df in datasets.values():
        relevant = [c for c in columns + [on] if c in df.columns]
        if len(relevant) <= 1:
            continue
        subset = df[relevant].dropna()
        if merged is None:
            merged = subset
        else:
            merged = merged.merge(subset, on=on, how="inner")

    if merged is not None and all(c in merged.columns for c in columns):
        return merged
    return None


# ===================================================================
# DEEP-DIVE ANALYSIS TYPES
# ===================================================================

def run_regression(
    datasets: dict[str, pd.DataFrame],
    outcome: str,
    predictor: str,
    controls: list[str] | None = None,
) -> dict:
    """OLS regression: outcome ~ predictor + controls."""
    needed = [outcome, predictor] + (controls or [])
    data = _merge_indicators(datasets, needed)
    if data is None:
        return {"summary": f"Could not find/merge columns: {needed}", "figure": None}

    if not HAS_STATSMODELS:
        r, p = stats.pearsonr(data[predictor], data[outcome])
        return {
            "summary": f"statsmodels not installed; simple Pearson: r={r:.4f}, p={p:.4f}",
            "figure": px.scatter(data, x=predictor, y=outcome, trendline="ols",
                                  title=f"{outcome} vs {predictor}"),
        }

    x_cols = [predictor] + (controls or [])
    X = sm.add_constant(data[x_cols])
    y = data[outcome]
    model = sm.OLS(y, X).fit()

    fig = px.scatter(data, x=predictor, y=outcome, trendline="ols",
                      title=f"{outcome} vs {predictor} (OLS)")

    return {
        "summary": model.summary().as_text(),
        "figure": fig,
        "model": model,
    }


def run_lag_analysis(
    datasets: dict[str, pd.DataFrame],
    predictor: str,
    outcome: str,
    time_col: str = "year",
    max_lag: int = 10,
) -> dict:
    """Cross-correlation at multiple lag values between predictor and outcome."""
    needed = [predictor, outcome, time_col]
    data = _merge_indicators(datasets, needed)
    if data is None:
        return {"summary": f"Could not find/merge columns: {needed}", "figure": None}

    data = data.sort_values(time_col).set_index(time_col)
    x = data[predictor]
    y = data[outcome]

    if len(x) < max_lag + 2:
        max_lag = max(1, len(x) - 2)

    lags = range(-max_lag, max_lag + 1)
    correlations = []
    for lag in lags:
        if lag >= 0:
            corr = x.iloc[:len(x) - lag].reset_index(drop=True).corr(
                y.iloc[lag:].reset_index(drop=True)
            )
        else:
            corr = x.iloc[-lag:].reset_index(drop=True).corr(
                y.iloc[:len(y) + lag].reset_index(drop=True)
            )
        correlations.append({"lag": lag, "correlation": round(corr, 4) if pd.notna(corr) else 0})

    lag_df = pd.DataFrame(correlations)
    best = lag_df.loc[lag_df["correlation"].abs().idxmax()]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=lag_df["lag"], y=lag_df["correlation"], name="correlation"))
    fig.update_layout(
        title=f"Cross-correlation: {predictor} → {outcome}",
        xaxis_title=f"Lag (years, positive = {predictor} leads)",
        yaxis_title="Correlation",
    )

    return {
        "summary": (
            f"Best correlation at lag={int(best['lag'])}: r={best['correlation']:.4f}\n"
            f"Positive lag means {predictor} leads {outcome} by that many years."
        ),
        "figure": fig,
        "lag_data": lag_df,
    }


def run_segmented_comparison(
    datasets: dict[str, pd.DataFrame],
    predictor: str,
    outcome: str,
    segment_var: str,
    n_segments: int = 2,
) -> dict:
    """Split data by segment_var quantiles and compare predictor-outcome relationship."""
    needed = [predictor, outcome, segment_var]
    data = _merge_indicators(datasets, needed)
    if data is None:
        return {"summary": f"Could not find/merge columns: {needed}", "figures": []}

    data["_segment"] = pd.qcut(data[segment_var], q=n_segments, labels=False, duplicates="drop")
    segment_labels = {i: f"Q{i+1}" for i in range(n_segments)}
    data["_segment_label"] = data["_segment"].map(segment_labels)

    figures = []
    summaries = []
    for seg in sorted(data["_segment"].unique()):
        seg_data = data[data["_segment"] == seg]
        label = segment_labels.get(seg, str(seg))
        if len(seg_data) < 3:
            continue
        r, p = stats.pearsonr(seg_data[predictor], seg_data[outcome])
        summaries.append(f"  {label} (n={len(seg_data)}): r={r:.4f}, p={p:.4f}")

    fig = px.scatter(data, x=predictor, y=outcome, color="_segment_label",
                      trendline="ols", title=f"{outcome} vs {predictor} by {segment_var} segment")
    figures.append(fig)

    return {
        "summary": f"Segmented by {segment_var} ({n_segments} groups):\n" + "\n".join(summaries),
        "figures": figures,
    }


def run_before_after(
    datasets: dict[str, pd.DataFrame],
    outcome: str,
    event_year: int,
    time_col: str = "year",
) -> dict:
    """Compare outcome metrics before vs after a specific event year."""
    needed = [outcome, time_col]
    data = _merge_indicators(datasets, needed)
    if data is None:
        return {"summary": f"Could not find/merge columns: {needed}", "figure": None}

    before = data[data[time_col] < event_year][outcome]
    after = data[data[time_col] >= event_year][outcome]

    if before.empty or after.empty:
        return {"summary": f"Not enough data on both sides of {event_year}.", "figure": None}

    t_stat, p_val = stats.ttest_ind(before, after, equal_var=False)
    before_mean = before.mean()
    after_mean = after.mean()
    diff = after_mean - before_mean

    fig = go.Figure()
    agg = data.groupby(time_col)[outcome].mean()
    fig.add_trace(go.Scatter(x=agg.index, y=agg.values, mode="lines+markers", name=outcome))
    fig.add_vline(x=event_year, line_dash="dash", line_color="red",
                   annotation_text=f"Event @ {event_year}")
    fig.add_hline(y=before_mean, line_dash="dot", line_color="blue", annotation_text="before mean")
    fig.add_hline(y=after_mean, line_dash="dot", line_color="green", annotation_text="after mean")
    fig.update_layout(title=f"{outcome} before/after {event_year}")

    return {
        "summary": (
            f"Before {event_year}: mean={before_mean:.4f} (n={len(before)})\n"
            f"After {event_year}: mean={after_mean:.4f} (n={len(after)})\n"
            f"Difference: {diff:+.4f}\n"
            f"t-test: t={t_stat:.4f}, p={p_val:.4f}"
        ),
        "figure": fig,
    }


# ===================================================================
# NARRATIVE REFRAMING PATTERNS
# ===================================================================

def run_pattern(
    datasets: dict[str, pd.DataFrame],
    pattern: str,
    outcome_var: str = "",
    predictor_var: str = "",
    hidden_var: str = "",
    segment_var: str = "",
    time_col: str = "year",
    event_year: int | None = None,
) -> dict:
    """Dispatch to the appropriate pattern analysis."""
    dispatch = {
        "masking": _pattern_masking,
        "displacement": _pattern_displacement,
        "divergence": _pattern_divergence,
        "lag_lead": _pattern_lag_lead,
        "segmentation": _pattern_segmentation,
        "threshold": _pattern_threshold,
    }
    fn = dispatch.get(pattern)
    if fn is None:
        return {"summary": f"Unknown pattern: {pattern}. Available: {list(dispatch.keys())}", "figures": []}

    return fn(
        datasets,
        outcome_var=outcome_var,
        predictor_var=predictor_var,
        hidden_var=hidden_var,
        segment_var=segment_var,
        time_col=time_col,
        event_year=event_year,
    )


def _pattern_masking(datasets, outcome_var, predictor_var, hidden_var, time_col="year", **kw):
    """Masking: does hidden_var absorb or hide the effect of predictor on outcome?

    Test: correlate predictor and outcome with and without controlling for hidden_var.
    """
    needed = [outcome_var, predictor_var, hidden_var]
    data = _merge_indicators(datasets, needed)
    if data is None:
        return {"summary": f"Could not merge: {needed}", "figures": []}

    r_raw, p_raw = stats.pearsonr(data[predictor_var], data[outcome_var])

    if HAS_STATSMODELS:
        X_no_ctrl = sm.add_constant(data[[predictor_var]])
        X_with_ctrl = sm.add_constant(data[[predictor_var, hidden_var]])
        y = data[outcome_var]

        model_no = sm.OLS(y, X_no_ctrl).fit()
        model_with = sm.OLS(y, X_with_ctrl).fit()

        coef_no = model_no.params[predictor_var]
        coef_with = model_with.params[predictor_var]
        change = ((coef_with - coef_no) / abs(coef_no) * 100) if coef_no != 0 else float("nan")

        summary = (
            f"Without controlling for {hidden_var}:\n"
            f"  {predictor_var} -> {outcome_var}: coef={coef_no:.4f}, p={model_no.pvalues[predictor_var]:.4f}\n"
            f"Controlling for {hidden_var}:\n"
            f"  {predictor_var} -> {outcome_var}: coef={coef_with:.4f}, p={model_with.pvalues[predictor_var]:.4f}\n"
            f"Coefficient change: {change:+.1f}%\n"
            f"{'MASKING DETECTED' if abs(change) > 20 else 'Weak or no masking effect'}: "
            f"{'The effect of ' + predictor_var + ' on ' + outcome_var + ' changes substantially when controlling for ' + hidden_var if abs(change) > 20 else 'Minimal change in coefficient.'}"
        )
    else:
        r_partial = _partial_corr(data, predictor_var, outcome_var, hidden_var)
        summary = (
            f"Raw correlation ({predictor_var}, {outcome_var}): r={r_raw:.4f}\n"
            f"Partial correlation controlling for {hidden_var}: r={r_partial:.4f}\n"
            f"{'MASKING DETECTED' if abs(r_raw - r_partial) > 0.15 else 'Weak or no masking effect'}"
        )

    fig1 = px.scatter(data, x=predictor_var, y=outcome_var, color=hidden_var,
                       title=f"{outcome_var} vs {predictor_var}, colored by {hidden_var}")

    if time_col in data.columns:
        agg = data.groupby(time_col)[[outcome_var, predictor_var, hidden_var]].mean()
        fig2 = go.Figure()
        for col in [outcome_var, predictor_var, hidden_var]:
            fig2.add_trace(go.Scatter(x=agg.index, y=agg[col], mode="lines+markers", name=col))
        fig2.update_layout(title=f"Masking check: {predictor_var}, {outcome_var}, {hidden_var} over time")
        return {"summary": summary, "figures": [fig1, fig2]}

    return {"summary": summary, "figures": [fig1]}


def _pattern_displacement(datasets, outcome_var, predictor_var, time_col="year", segment_var="", **kw):
    """Displacement: did a change in predictor push outcome from one bucket to another?"""
    needed = [outcome_var, predictor_var]
    if segment_var:
        needed.append(segment_var)
    data = _merge_indicators(datasets, needed)
    if data is None:
        return {"summary": f"Could not merge: {needed}", "figures": []}

    if segment_var and segment_var in data.columns:
        agg = data.groupby([time_col, segment_var])[[outcome_var]].mean().reset_index()
        fig = px.line(agg, x=time_col, y=outcome_var, color=segment_var,
                       title=f"Displacement check: {outcome_var} by {segment_var}")
        total = data.groupby(time_col)[outcome_var].sum()
        summary = (
            f"Total {outcome_var} over time (sum across {segment_var}):\n"
            f"  Start: {total.iloc[0]:.2f}, End: {total.iloc[-1]:.2f}, "
            f"Change: {total.iloc[-1] - total.iloc[0]:+.2f}\n"
            f"If the total is unchanged but segments shifted, displacement is likely."
        )
        return {"summary": summary, "figures": [fig]}

    return {"summary": "Displacement pattern requires a segment_var to compare buckets.", "figures": []}


def _pattern_divergence(datasets, outcome_var, predictor_var, time_col="year", **kw):
    """Divergence: two metrics that should move together are moving apart."""
    needed = [outcome_var, predictor_var, time_col]
    data = _merge_indicators(datasets, needed)
    if data is None:
        return {"summary": f"Could not merge: {needed}", "figures": []}

    agg = data.groupby(time_col)[[outcome_var, predictor_var]].mean()
    base = agg.iloc[0]
    normalized = agg / base * 100

    gap = (normalized[outcome_var] - normalized[predictor_var]).abs()
    max_gap_year = gap.idxmax()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=normalized.index, y=normalized[outcome_var],
                              mode="lines+markers", name=outcome_var))
    fig.add_trace(go.Scatter(x=normalized.index, y=normalized[predictor_var],
                              mode="lines+markers", name=predictor_var))
    fig.update_layout(title=f"Divergence: {outcome_var} vs {predictor_var} (indexed to 100)",
                       yaxis_title="Index (base year = 100)")

    return {
        "summary": (
            f"Normalized to base year = 100.\n"
            f"Maximum divergence at {max_gap_year}: gap = {gap[max_gap_year]:.1f} index points."
        ),
        "figures": [fig],
    }


def _pattern_lag_lead(datasets, outcome_var, predictor_var, time_col="year", **kw):
    """Lag/lead: wrapper around run_lag_analysis."""
    result = run_lag_analysis(datasets, predictor_var, outcome_var, time_col=time_col)
    figures = [result["figure"]] if result.get("figure") else []
    return {"summary": result["summary"], "figures": figures}


def _pattern_segmentation(datasets, outcome_var, predictor_var, segment_var, **kw):
    """Segmentation: wrapper around run_segmented_comparison."""
    if not segment_var:
        return {"summary": "Segmentation pattern requires segment_var.", "figures": []}
    result = run_segmented_comparison(datasets, predictor_var, outcome_var, segment_var)
    return {"summary": result["summary"], "figures": result.get("figures", [])}


def _pattern_threshold(datasets, outcome_var, predictor_var, **kw):
    """Threshold: is there a tipping point where the A-B relationship changes?"""
    needed = [outcome_var, predictor_var]
    data = _merge_indicators(datasets, needed)
    if data is None:
        return {"summary": f"Could not merge: {needed}", "figures": []}

    data_sorted = data.sort_values(predictor_var)
    n = len(data_sorted)
    if n < 10:
        return {"summary": "Not enough data for threshold analysis (need 10+ rows).", "figures": []}

    n_bins = min(10, n // 3)
    data_sorted["_bin"] = pd.qcut(data_sorted[predictor_var], q=n_bins, duplicates="drop")
    bin_means = data_sorted.groupby("_bin", observed=True).agg(
        x_mean=(predictor_var, "mean"),
        y_mean=(outcome_var, "mean"),
        count=(outcome_var, "count"),
    ).reset_index()

    diffs = bin_means["y_mean"].diff()
    sign_changes = (diffs.iloc[1:] * diffs.iloc[:-1].values)
    threshold_idx = sign_changes[sign_changes < 0].index
    threshold_note = ""
    if len(threshold_idx) > 0:
        idx = threshold_idx[0]
        threshold_note = (
            f"Possible threshold near {predictor_var} = {bin_means.loc[idx, 'x_mean']:.2f}: "
            f"relationship direction changes."
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bin_means["x_mean"], y=bin_means["y_mean"],
                              mode="lines+markers", name="binned means"))
    fig.add_trace(go.Scatter(x=data_sorted[predictor_var], y=data_sorted[outcome_var],
                              mode="markers", opacity=0.3, name="raw data"))
    fig.update_layout(title=f"Threshold check: {outcome_var} vs {predictor_var}",
                       xaxis_title=predictor_var, yaxis_title=outcome_var)

    return {
        "summary": (
            f"Binned analysis ({n_bins} bins):\n"
            f"{bin_means[['x_mean', 'y_mean', 'count']].to_string(index=False)}\n\n"
            f"{threshold_note or 'No clear threshold detected.'}"
        ),
        "figures": [fig],
    }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _partial_corr(data: pd.DataFrame, x: str, y: str, z: str) -> float:
    """Partial correlation between x and y controlling for z."""
    r_xy, _ = stats.pearsonr(data[x], data[y])
    r_xz, _ = stats.pearsonr(data[x], data[z])
    r_yz, _ = stats.pearsonr(data[y], data[z])
    numerator = r_xy - r_xz * r_yz
    denominator = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
    if denominator == 0:
        return 0.0
    return numerator / denominator
