#!/usr/bin/env python3
"""
Generate a standalone interactive HTML dashboard:
  "Generation Priced Out: How 30 Looks Nothing Like It Used To"

Uses:
  - Processed national_panel.parquet (US milestones + housing economics + CPI)

Outputs:
  projects/generation-priced-out/reports/dashboard.html
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).parents[2]))
from pipeline.config import load_config, get_data_processed_dir

from plotly.io._html import get_plotlyjs

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
config = load_config("generation-priced-out")
processed_dir = get_data_processed_dir(config)

national = pd.read_parquet(processed_dir / "national_panel.parquet")
national = national.sort_values("year")

# ---------------------------------------------------------------------------
# Modern color palette (dark theme, high contrast, accessible)
# ---------------------------------------------------------------------------
C_ROSE   = "#f43f5e"   # primary accent — warnings / declines
C_AMBER  = "#f59e0b"   # secondary warm
C_SKY    = "#38bdf8"   # cool informational
C_EMERALD = "#34d399"  # positive / historical
C_VIOLET = "#a78bfa"   # highlight / US marker
C_SLATE  = "#94a3b8"   # muted text
C_ZINC   = "#71717a"   # subtle text

_HOVERLABEL = dict(
    bgcolor="rgba(15,18,30,0.96)",
    bordercolor="rgba(255,255,255,0.12)",
    font=dict(color="#e2e8f0", size=13, family="'Inter', system-ui, sans-serif"),
    namelength=-1,
)

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.02)",
    font=dict(color="#e2e8f0", family="'Inter', system-ui, sans-serif"),
    title_font=dict(size=16, color="#f1f5f9"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)",
               tickfont=dict(color=C_SLATE, size=11)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)",
               tickfont=dict(color=C_SLATE, size=11)),
    margin=dict(l=60, r=30, t=55, b=55),
    hoverlabel=_HOVERLABEL,
)

_MARGIN_WITH_LEGEND = dict(l=60, r=30, t=115, b=55)

_LEGEND_H = dict(
    bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cbd5e1", size=12),
    orientation="h", y=1.06, x=0.5, xanchor="center",
    yanchor="bottom",
    itemsizing="constant",
    tracegroupgap=16,
)

_CHART_CONFIG = {
    "displayModeBar": "hover",
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "responsive": True,
}


def dark(height: int = 420, **kwargs) -> dict:
    d = {**DARK_LAYOUT, "height": height}
    for k, v in kwargs.items():
        if k in d and isinstance(d[k], dict) and isinstance(v, dict):
            d[k] = {**d[k], **v}
        else:
            d[k] = v
    return d


def fig_to_div(fig, div_id: str) -> str:
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=div_id,
        config=_CHART_CONFIG,
    )


# ---------------------------------------------------------------------------
# Compute headline stats
# ---------------------------------------------------------------------------
yr_1983 = national[national["year"] == 1983].iloc[0]
yr_latest = national[national["year"] >= 2022].dropna(
    subset=["pct_independent_25_34"]
).iloc[-1]
yr_latest_yr = int(yr_latest["year"])

tfr_latest = national.dropna(subset=["total_fertility_rate"]).iloc[-1]
tfr_latest_yr = int(tfr_latest["year"])

# Housing stats — use 1984 (first year with income data) and latest
yr_housing_base = national[national["year"] == 1984].iloc[0]
yr_housing_latest = national.dropna(subset=["price_to_income_ratio"]).iloc[-1]
yr_housing_latest_yr = int(yr_housing_latest["year"])

yr_pci_latest = national.dropna(subset=["price_to_per_capita_income_ratio"]).iloc[-1]

stats = {
    "indep_1983": yr_1983["pct_independent_25_34"],
    "indep_now": yr_latest["pct_independent_25_34"],
    "married_1983": yr_1983["pct_married_25_34"],
    "married_now": yr_latest["pct_married_25_34"],
    "homeown_1983": yr_1983["homeownership_rate_under_35"],
    "homeown_now": yr_latest["homeownership_rate_under_35"],
    "tfr_1983": yr_1983["total_fertility_rate"],
    "tfr_now": tfr_latest["total_fertility_rate"],
    "ratio_old": yr_housing_base["price_to_income_ratio"],
    "ratio_new": yr_housing_latest["price_to_income_ratio"],
    "pci_ratio_old": yr_housing_base.get("price_to_per_capita_income_ratio", float("nan")),
    "pci_ratio_new": yr_pci_latest.get("price_to_per_capita_income_ratio", float("nan")),
    "price_old": yr_housing_base["median_home_price"],
    "price_new": yr_housing_latest["median_home_price"],
    "income_old": yr_housing_base["median_household_income"],
    "income_new": yr_housing_latest["median_household_income"],
    "pi_ratio_old": yr_housing_base.get("price_to_personal_income_ratio", float("nan")),
    "pi_ratio_new": yr_housing_latest.get("price_to_personal_income_ratio", float("nan")),
    "pi_pmt_old": yr_housing_base.get("payment_to_personal_income_pct", float("nan")),
    "pi_pmt_new": yr_housing_latest.get("payment_to_personal_income_pct", float("nan")),
    "pmt_hh_old": yr_housing_base.get("payment_to_income_pct", float("nan")),
    "pmt_hh_new": yr_housing_latest.get("payment_to_income_pct", float("nan")),
}


pp_married = stats["married_now"] - stats["married_1983"]   # percentage points
pp_homeown = stats["homeown_now"] - stats["homeown_1983"]

_idx_row = national.dropna(subset=["home_price_idx", "income_idx", "cpi_shelter_idx"]).iloc[-1]
stats["hp_growth_x"] = _idx_row["home_price_idx"] / 100
stats["cpi_shelter_growth_x"] = _idx_row["cpi_shelter_idx"] / 100
stats["hh_income_growth_x"] = _idx_row["income_idx"] / 100

# Mortgage rate context
_rate_84_row = national[national["year"] == 1984].iloc[0]
_rate_latest_row = national.dropna(subset=["mortgage_rate_30yr"]).iloc[-1]
stats["rate_1984"] = _rate_84_row.get("mortgage_rate_30yr", float("nan"))
stats["rate_now"] = _rate_latest_row["mortgage_rate_30yr"]
stats["rate_now_yr"] = int(_rate_latest_row["year"])

# Per-earner effective homeownership: household rate adjusted by earners-per-household
national["earners_per_hh"] = (
    national["median_household_income"] / national["median_personal_income"]
)
national["homeownership_per_earner"] = (
    national["homeownership_rate_under_35"] / national["earners_per_hh"]
)

_ho_earner = national.dropna(subset=["homeownership_per_earner"])
if not _ho_earner.empty:
    _ho_first = _ho_earner.iloc[0]
    _ho_last = _ho_earner.iloc[-1]
    stats["ho_earner_old"] = _ho_first["homeownership_per_earner"]
    stats["ho_earner_old_yr"] = int(_ho_first["year"])
    stats["ho_earner_new"] = _ho_last["homeownership_per_earner"]
    stats["ho_earner_new_yr"] = int(_ho_last["year"])

# ===================================================================
# CHARTS
# ===================================================================

# --- Chart 1: Combined milestone overlay ---
def make_chart_overlay():
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_vline(x=1983, line_dash="dash", line_color="rgba(255,255,255,0.2)",
                  annotation_text="1983", annotation_position="top",
                  annotation_font=dict(color=C_SLATE, size=10))

    d = national[national["year"] >= 1960].copy()

    for col, name, color in [
        ("pct_independent_25_34", "Independent", C_ROSE),
        ("pct_married_25_34", "Married", C_AMBER),
        ("homeownership_rate_under_35", "Homeowner", C_SKY),
    ]:
        dd = d.dropna(subset=[col])
        fig.add_trace(go.Scatter(
            x=dd["year"], y=dd[col], name=name, mode="lines",
            line=dict(color=color, width=2.5),
            hovertemplate=f"%{{x}}: %{{y:.1f}}%<extra>{name}</extra>",
        ), secondary_y=False)

    dd = d.dropna(subset=["total_fertility_rate"])
    fig.add_trace(go.Scatter(
        x=dd["year"], y=dd["total_fertility_rate"],
        name="Fertility Rate", mode="lines",
        line=dict(color=C_EMERALD, width=2.5, dash="dot"),
        hovertemplate="%{x}: %{y:.2f}<extra>TFR</extra>",
    ), secondary_y=True)

    x_range = d["year"].dropna()
    fig.add_trace(go.Scatter(
        x=[int(x_range.min()), int(x_range.max())], y=[2.1, 2.1],
        name="Replacement (2.1)", mode="lines",
        line=dict(color=C_EMERALD, width=1.5, dash="dash"),
        hoverinfo="skip",
    ), secondary_y=True)

    fig.update_layout(
        **dark(560, margin=_MARGIN_WITH_LEGEND),
        title="Four Milestones of Adulthood — 1960 to Present",
        hovermode="x unified", legend=_LEGEND_H,
    )
    fig.update_yaxes(title_text="Percent (%)", secondary_y=False,
                     range=[30, 100], gridcolor="rgba(255,255,255,0.06)",
                     title_standoff=12)
    fig.update_yaxes(title_text="Fertility Rate", secondary_y=True,
                     range=[1.0, 3.8], gridcolor="rgba(255,255,255,0.03)",
                     title_standoff=12)
    return fig_to_div(fig, "chart_overlay")


# --- Chart 2: The Great Divergence (indexed to 1984=100) ---
def make_chart_divergence():
    d = national[national["year"] >= 1984].copy()
    fig = go.Figure()

    dd_hp = d.dropna(subset=["home_price_idx"])
    dd_cs = d.dropna(subset=["cpi_shelter_idx"])
    shared = sorted(set(dd_hp["year"]) & set(dd_cs["year"]))

    if shared:
        cs_vals = dd_cs.set_index("year").loc[shared, "cpi_shelter_idx"]
        fig.add_trace(go.Scatter(
            x=shared, y=cs_vals.values,
            mode="lines", line=dict(width=0), showlegend=False,
            hoverinfo="skip",
        ))
        hp_vals = dd_hp.set_index("year").loc[shared, "home_price_idx"]
        fig.add_trace(go.Scatter(
            x=shared, y=hp_vals.values,
            name="Median Home Price", mode="lines",
            line=dict(color=C_ROSE, width=3),
            fill="tonexty", fillcolor="rgba(244,63,94,0.10)",
            hovertemplate="%{x}: %{y:.0f}<extra>Median Home Price</extra>",
        ))

    dd_cs_full = d.dropna(subset=["cpi_shelter_idx"])
    fig.add_trace(go.Scatter(
        x=dd_cs_full["year"], y=dd_cs_full["cpi_shelter_idx"],
        name="CPI: Shelter (official measure)", mode="lines",
        line=dict(color=C_AMBER, width=2.5),
        hovertemplate="%{x}: %{y:.0f}<extra>CPI: Shelter</extra>",
    ))

    dd_inc = d.dropna(subset=["income_idx"])
    fig.add_trace(go.Scatter(
        x=dd_inc["year"], y=dd_inc["income_idx"],
        name="Household Income", mode="lines",
        line=dict(color=C_SKY, width=2, dash="dash"),
        hovertemplate="%{x}: %{y:.0f}<extra>Household Income</extra>",
    ))

    fig.add_hline(y=100, line_dash="dot", line_color="rgba(255,255,255,0.15)")

    fig.add_vline(x=1984, line_dash="dash", line_color="rgba(255,255,255,0.2)",
                  annotation_text="CPI methodology change (Jan 1983)",
                  annotation_position="top right",
                  annotation_font=dict(color=C_AMBER, size=9))

    layout = dark(560, margin=_MARGIN_WITH_LEGEND)
    layout["yaxis"] = dict(
        title="Index (1984 = 100)",
        gridcolor="rgba(255,255,255,0.06)",
        tickfont=dict(color=C_SLATE, size=11),
        title_standoff=12,
    )
    fig.update_layout(
        **layout,
        title="The Great Divergence: Home Prices vs. Official Measures",
        xaxis_title="Year", hovermode="x unified", legend=_LEGEND_H,
    )
    return fig_to_div(fig, "chart_divergence")


# --- Chart 3: Price-to-Income Ratio over time ---
def make_chart_affordability():
    d = national.dropna(subset=["price_to_income_ratio"]).copy()
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=d["year"], y=d["price_to_income_ratio"],
        mode="lines+markers", name="Household Income",
        line=dict(color=C_ROSE, width=3),
        marker=dict(size=4),
        fill="tozeroy", fillcolor="rgba(244,63,94,0.08)",
        hovertemplate="%{x}: %{y:.2f}× household income<extra></extra>",
    ))

    di = national.dropna(subset=["price_to_personal_income_ratio"]).copy()
    fig.add_trace(go.Scatter(
        x=di["year"], y=di["price_to_personal_income_ratio"],
        mode="lines+markers", name="Individual Income",
        line=dict(color=C_VIOLET, width=3),
        marker=dict(size=4),
        fill="tonexty", fillcolor="rgba(167,139,250,0.06)",
        hovertemplate="%{x}: %{y:.1f}× individual income<extra></extra>",
    ))

    fig.add_hline(y=3.0, line_dash="dash", line_color="rgba(56,189,248,0.35)",
                  annotation_text='3× threshold',
                  annotation_position="bottom left",
                  annotation_font=dict(color="rgba(56,189,248,0.6)", size=10))

    layout = dark(440, margin=_MARGIN_WITH_LEGEND)
    layout["yaxis"] = dict(
        title="Years of Income",
        gridcolor="rgba(255,255,255,0.06)",
        tickfont=dict(color=C_SLATE, size=11),
        range=[0, 12], title_standoff=10,
    )
    fig.update_layout(
        **layout, title="Home Price-to-Income Ratio",
        legend=_LEGEND_H, hovermode="x unified",
    )
    return fig_to_div(fig, "chart_affordability")


# --- Chart 4: Monthly payment as % of income ---
def make_chart_payment_burden():
    d = national.dropna(subset=["payment_to_income_pct"]).copy()
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=d["year"], y=d["payment_to_income_pct"],
        mode="lines+markers", name="Household Income",
        line=dict(color=C_AMBER, width=3),
        marker=dict(size=4),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.08)",
        hovertemplate="%{x}: %{y:.1f}% of household income<extra></extra>",
    ))

    di = national.dropna(subset=["payment_to_personal_income_pct"]).copy()
    fig.add_trace(go.Scatter(
        x=di["year"], y=di["payment_to_personal_income_pct"],
        mode="lines+markers", name="Individual Income",
        line=dict(color=C_VIOLET, width=3),
        marker=dict(size=4),
        fill="tonexty", fillcolor="rgba(167,139,250,0.06)",
        hovertemplate="%{x}: %{y:.1f}% of individual income<extra></extra>",
    ))

    fig.add_hline(y=30, line_dash="dash", line_color="rgba(244,63,94,0.4)",
                  annotation_text='30% threshold',
                  annotation_position="top left",
                  annotation_font=dict(color="rgba(244,63,94,0.6)", size=10))

    layout = dark(440, margin=_MARGIN_WITH_LEGEND)
    layout["yaxis"] = dict(
        title="% of Monthly Income",
        gridcolor="rgba(255,255,255,0.06)",
        tickfont=dict(color=C_SLATE, size=11),
        range=[0, 100], title_standoff=10,
    )
    fig.update_layout(
        **layout,
        title="Mortgage Burden: Payment vs. Income",
        legend=_LEGEND_H, hovermode="x unified",
    )
    return fig_to_div(fig, "chart_payment")


# --- Chart 5: What you get — price/sqft + lot size ---
def make_chart_what_you_get():
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    d = national[national["year"] >= 1987].copy()

    # Price per sqft
    dd = d.dropna(subset=["price_per_sqft_new"])
    fig.add_trace(go.Scatter(
        x=dd["year"], y=dd["price_per_sqft_new"],
        name="Price per Sqft (New Home)", mode="lines+markers",
        line=dict(color=C_ROSE, width=2.5),
        marker=dict(size=4),
        hovertemplate="$%{y:.0f}/sqft<extra>Price per Sqft</extra>",
    ), secondary_y=False)

    # Lot size
    dd2 = d.dropna(subset=["median_lot_size_sqft"])
    fig.add_trace(go.Scatter(
        x=dd2["year"], y=dd2["median_lot_size_sqft"],
        name="Median Lot Size (sqft)", mode="lines+markers",
        line=dict(color=C_EMERALD, width=2.5),
        marker=dict(size=4),
        hovertemplate="%{y:,.0f} sqft<extra>Lot Size</extra>",
    ), secondary_y=True)

    fig.update_layout(
        **dark(500, margin=_MARGIN_WITH_LEGEND),
        title="What Your Dollar Buys: Cost per Sqft vs. Land",
        hovermode="x unified", legend=_LEGEND_H,
    )
    fig.update_yaxes(title_text="Price per Sqft ($)", secondary_y=False,
                     gridcolor="rgba(255,255,255,0.06)", title_standoff=12)
    fig.update_yaxes(title_text="Median Lot Size (sqft)", secondary_y=True,
                     gridcolor="rgba(255,255,255,0.03)", title_standoff=12)
    return fig_to_div(fig, "chart_whatyouget")


# --- Chart 6: Individual milestone trends ---
def _make_single_trend(col, label, color, unit, y_range, div_id):
    d = national.dropna(subset=[col]).copy()
    fig = go.Figure()

    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fig.add_trace(go.Scatter(
        x=d["year"], y=d[col], mode="lines",
        line=dict(color=color, width=2.5),
        fill="tozeroy", fillcolor=f"rgba({r},{g},{b},0.08)",
        hovertemplate=f"%{{x}}: %{{y:.1f}}{unit}<extra></extra>",
        name=label,
    ))

    val_1983 = d[d["year"] == 1983]
    if not val_1983.empty:
        fig.add_annotation(
            x=1983, y=float(val_1983.iloc[0][col]),
            text=f"<b>1983</b>: {float(val_1983.iloc[0][col]):.1f}{unit}",
            showarrow=True, arrowhead=0, arrowwidth=1.5, arrowcolor=C_SLATE,
            font=dict(size=11, color="#cbd5e1"),
            ax=-55, ay=-35, bgcolor="rgba(11,15,26,0.8)",
            borderpad=4,
        )
    latest = d.iloc[-1]
    fig.add_annotation(
        x=int(latest["year"]), y=float(latest[col]),
        text=f"<b>{int(latest['year'])}</b>: {float(latest[col]):.1f}{unit}",
        showarrow=True, arrowhead=0, arrowwidth=1.5, arrowcolor=color,
        font=dict(size=11, color="#fff"),
        ax=55, ay=-35, bgcolor="rgba(11,15,26,0.8)",
        borderpad=4,
    )

    layout = dark(380)
    layout["xaxis"] = dict(
        dtick=10,
        gridcolor="rgba(255,255,255,0.06)",
        tickfont=dict(color=C_SLATE, size=11),
    )
    layout["yaxis"] = dict(
        title=label, range=y_range,
        gridcolor="rgba(255,255,255,0.06)",
        tickfont=dict(color=C_SLATE, size=11),
        title_standoff=10,
    )
    fig.update_layout(**layout, title=label, showlegend=False)
    return fig_to_div(fig, div_id)


# --- Chart 6b: Per-earner homeownership ---
def make_chart_homeownership_per_earner():
    d = national.dropna(subset=["homeownership_per_earner"]).copy()
    d_reported = national.dropna(subset=["homeownership_rate_under_35"]).copy()
    d_reported = d_reported[d_reported["year"] >= d["year"].min()]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=d_reported["year"], y=d_reported["homeownership_rate_under_35"],
        name="Reported (per household)", mode="lines",
        line=dict(color=C_SKY, width=2.5),
        hovertemplate="%{x}: %{y:.1f}%<extra>Reported</extra>",
    ))

    fig.add_trace(go.Scatter(
        x=d["year"], y=d["homeownership_per_earner"],
        name="Effective (per earner)", mode="lines",
        line=dict(color=C_ROSE, width=3),
        fill="tonexty", fillcolor="rgba(244,63,94,0.08)",
        hovertemplate="%{x}: %{y:.1f}%<extra>Per Earner</extra>",
    ))

    first = d.iloc[0]
    last = d.iloc[-1]
    fig.add_annotation(
        x=int(first["year"]), y=float(first["homeownership_per_earner"]),
        text=f"<b>{int(first['year'])}</b>: {float(first['homeownership_per_earner']):.1f}%",
        showarrow=True, arrowhead=0, arrowwidth=1.5, arrowcolor=C_SLATE,
        font=dict(size=11, color="#cbd5e1"),
        ax=-60, ay=-30, bgcolor="rgba(11,15,26,0.8)", borderpad=4,
    )
    fig.add_annotation(
        x=int(last["year"]), y=float(last["homeownership_per_earner"]),
        text=f"<b>{int(last['year'])}</b>: {float(last['homeownership_per_earner']):.1f}%",
        showarrow=True, arrowhead=0, arrowwidth=1.5, arrowcolor=C_ROSE,
        font=dict(size=11, color="#fff"),
        ax=60, ay=-30, bgcolor="rgba(11,15,26,0.8)", borderpad=4,
    )

    layout = dark(420, margin=_MARGIN_WITH_LEGEND)
    layout["yaxis"] = dict(
        title="Homeownership Rate (%)",
        gridcolor="rgba(255,255,255,0.06)",
        tickfont=dict(color=C_SLATE, size=11),
        range=[0, 50], title_standoff=10,
    )
    fig.update_layout(
        **layout,
        title="Homeownership: Reported vs. Per-Earner Effective Rate",
        legend=_LEGEND_H, hovermode="x unified",
    )
    return fig_to_div(fig, "chart_ho_earner")


# --- Chart 7: International TFR comparison ---
def make_chart_intl_tfr():
    intl_path = processed_dir / "international_panel.parquet"
    if not intl_path.exists():
        return ""
    intl = pd.read_parquet(intl_path)

    peers = {
        "USA": ("United States", C_ROSE, 2.5),
        "GBR": ("United Kingdom", C_SKY, 1.5),
        "FRA": ("France", C_EMERALD, 1.5),
        "DEU": ("Germany", C_AMBER, 1.5),
        "JPN": ("Japan", C_VIOLET, 1.5),
        "KOR": ("South Korea", C_ZINC, 1.5),
    }

    fig = go.Figure()
    for code, (name, color, width) in peers.items():
        d = intl[(intl["country_code"] == code) & (intl["fertility_rate"].notna())].copy()
        d = d.sort_values("year")
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["year"], y=d["fertility_rate"],
            name=name, mode="lines",
            line=dict(color=color, width=width),
            hovertemplate=f"%{{x}}: %{{y:.2f}}<extra>{name}</extra>",
        ))

    fig.add_hline(y=2.1, line_dash="dash", line_color="rgba(255,255,255,0.15)",
                  annotation_text="Replacement (2.1)",
                  annotation_position="bottom right",
                  annotation_font=dict(color=C_SLATE, size=10))

    layout = dark(440, margin=_MARGIN_WITH_LEGEND)
    layout["yaxis"] = dict(
        title="Births per Woman", range=[0.5, 4.5],
        gridcolor="rgba(255,255,255,0.06)",
        tickfont=dict(color=C_SLATE, size=11),
    )
    fig.update_layout(
        **layout,
        title="Fertility Rates: US vs. Peer Nations (1960–Present)",
        hovermode="x unified", legend=_LEGEND_H,
    )
    return fig_to_div(fig, "chart_intl_tfr")


# ---------------------------------------------------------------------------
# Generate all chart divs
# ---------------------------------------------------------------------------
print("Generating charts...")
chart_overlay = make_chart_overlay()
print("  + Milestone overlay")
chart_divergence = make_chart_divergence()
print("  + Great Divergence (CPI indexed)")
chart_affordability = make_chart_affordability()
print("  + Price-to-Income ratio")
chart_payment = make_chart_payment_burden()
print("  + Payment burden")
chart_whatyouget = make_chart_what_you_get()
print("  + Price/sqft + lot size")
chart_living = _make_single_trend(
    "pct_independent_25_34", "Living Independently (%)", C_ROSE, "%", [70, 100], "chart_living")
chart_marriage = _make_single_trend(
    "pct_married_25_34", "Currently Married (%)", C_AMBER, "%", [30, 90], "chart_marriage")
chart_homeownership = _make_single_trend(
    "homeownership_rate_under_35", "Homeownership Rate (%)", C_SKY, "%", [30, 50], "chart_homeownership")
chart_tfr = _make_single_trend(
    "total_fertility_rate", "Total Fertility Rate", C_EMERALD, "", [1.0, 3.8], "chart_tfr")
print("  + 4 individual trends")
chart_ho_earner = make_chart_homeownership_per_earner()
print("  + Per-earner homeownership")
chart_intl_tfr = make_chart_intl_tfr()
print("  + International TFR comparison")


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Generation Priced Out</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL@20,400,0" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@3.4.0/plotly.min.js" charset="utf-8"></script>
  <style>
    :root {{
      --bg:    #0b0f1a;
      --bg2:   #10141f;
      --border: rgba(255,255,255,0.06);
      --card:  rgba(255,255,255,0.02);
      --rose:  #f43f5e;
      --amber: #f59e0b;
      --sky:   #38bdf8;
      --emerald: #34d399;
      --violet: #a78bfa;
      --text:  #e2e8f0;
      --muted: #94a3b8;
      --dim:   #64748b;
    }}
    *{{ box-sizing:border-box; margin:0; padding:0; }}
    html{{ scroll-behavior:smooth; }}
    body{{
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      line-height: 1.7;
      -webkit-font-smoothing: antialiased;
    }}

    /* ---- PROGRESS BAR ---- */
    .progress-bar{{
      position:fixed; top:0; left:0; height:3px; z-index:1000;
      background:var(--rose); width:0%;
      transition: width 60ms linear;
    }}

    /* ---- SCROLL REVEAL ---- */
    .reveal{{
      opacity:0; transform:translateY(24px);
      transition: opacity .45s ease-out, transform .45s ease-out;
    }}
    .reveal.visible{{
      opacity:1; transform:translateY(0);
    }}
    .stat{{ transition-delay: calc(var(--i, 0) * 100ms); }}
    @media(prefers-reduced-motion:reduce){{
      .reveal{{ opacity:1; transform:none; transition:none; }}
      .stat{{ transition-delay:0ms; }}
    }}

    /* ---- HERO ---- */
    .hero{{
      position:relative; min-height:100vh;
      display:flex; align-items:center; justify-content:center;
      text-align:center; padding:4rem 2rem;
      background: var(--bg);
    }}
    .hero-inner{{ max-width:960px; }}
    .hero-tag{{
      display:inline-block; font-size:.68rem; font-weight:500;
      letter-spacing:.12em; text-transform:uppercase;
      color:var(--dim); margin-bottom:1.5rem;
    }}
    .hero h1{{
      font-size:clamp(2rem,5.5vw,3.6rem); font-weight:700;
      line-height:1.1; color:#fff; margin-bottom:.5rem;
    }}
    .hero h1 em{{ font-style:normal; color:var(--rose); }}
    .hero-sub{{
      font-size:clamp(1rem,2.2vw,1.25rem); color:var(--muted);
      margin-bottom:2.5rem; font-weight:400;
    }}
    .hero-lede{{
      font-size:1.05rem; color:var(--muted); max-width:640px;
      margin:0 auto 2.5rem; line-height:1.85; text-align:center;
    }}
    .hero-lede strong{{ color:#fff; font-weight:600; }}

    /* ---- SCORECARD ---- */
    .sc-context{{
      max-width:700px; margin:0 auto .8rem;
      font-size:.72rem; font-weight:500; letter-spacing:.08em;
      text-transform:uppercase; color:var(--dim); text-align:center;
    }}
    .scorecard{{
      max-width:700px; margin:0 auto 2.5rem; text-align:left;
      border:1px solid var(--border);
      border-radius:8px; overflow:hidden;
    }}
    .sc-head{{
      display:grid; grid-template-columns:2.2fr 1fr 2rem 1fr;
      padding:.75rem 1.8rem; gap:.5rem;
      border-bottom:1px solid rgba(255,255,255,0.08);
      background:rgba(255,255,255,0.025);
    }}
    .sc-head span{{
      font-size:.72rem; font-weight:600; letter-spacing:.1em;
      text-transform:uppercase; color:var(--dim);
    }}
    .sc-head span:not(:first-child){{ text-align:right; }}
    .sc-row{{
      display:grid; grid-template-columns:2.2fr 1fr 2rem 1fr;
      padding:.85rem 1.8rem; gap:.5rem;
      align-items:center;
      border-bottom:1px solid rgba(255,255,255,0.04);
    }}
    .sc-row:last-child{{ border-bottom:none; }}
    .sc-metric{{ font-size:.95rem; font-weight:600; color:var(--text); line-height:1.3; }}
    .sc-desc{{ font-size:.75rem; color:var(--dim); margin-top:.15rem; line-height:1.4; font-weight:400; }}
    .sc-val{{ font-size:1.35rem; font-weight:700; text-align:right; }}
    .sc-val.old{{ color:var(--muted); }}
    .sc-val.now{{ color:#fff; }}
    .sc-delta{{
      display:flex; align-items:center; justify-content:center;
      color:var(--rose);
    }}
    .sc-delta .material-symbols-outlined{{
      font-size:20px;
      font-variation-settings:'wght' 500;
    }}
    @media(max-width:560px){{
      .scorecard{{ margin:0 -1rem 2.5rem; border-radius:0; }}
      .sc-head,.sc-row{{ padding:.7rem 1rem; }}
      .sc-metric{{ font-size:.85rem; }}
      .sc-desc{{ font-size:.68rem; }}
      .sc-val{{ font-size:1.1rem; }}
      .sc-delta .material-symbols-outlined{{ font-size:16px; }}
    }}

    .hero-body{{
      font-size:.95rem; color:var(--muted); max-width:620px;
      margin:0 auto 2.5rem; line-height:1.85; text-align:center;
    }}
    .hero-body strong{{ color:#fff; font-weight:600; }}
    .hero-cta{{
      display:inline-block; padding:.65rem 1.6rem;
      background:rgba(255,255,255,0.08); color:#fff; font-weight:500; font-size:.88rem;
      text-decoration:none; border-radius:6px; border:1px solid var(--border);
      transition: background .15s;
    }}
    .hero-cta:hover{{ background:rgba(255,255,255,0.12); }}
    .scroll-cue{{
      margin-top:1.5rem; font-size:.68rem; color:var(--dim);
      letter-spacing:.1em; text-transform:uppercase;
      animation: pulse 2.5s ease-in-out infinite;
    }}
    @keyframes pulse{{ 0%,100%{{opacity:.3}} 50%{{opacity:.8}} }}

    /* ---- LAYOUT ---- */
    .container{{ max-width:960px; margin:0 auto; padding:0 2rem; }}

    /* ---- SECTION ---- */
    .sec{{
      padding:5rem 0;
      border-top:1px solid var(--border);
      scroll-margin-top:2rem;
    }}
    .sec-num{{
      font-size:.7rem; font-weight:600; letter-spacing:.12em;
      text-transform:uppercase; color:var(--dim); margin-bottom:.6rem;
    }}
    .sec h2{{
      font-size:clamp(1.5rem,3.2vw,2rem); color:#fff;
      margin-bottom:.8rem; line-height:1.25; font-weight:700;
    }}
    .sec .lead{{
      font-size:.98rem; color:var(--muted); max-width:700px;
      margin-bottom:2.5rem; line-height:1.85;
    }}
    .sec .lead strong{{ color:var(--text); font-weight:600; }}

    /* ---- ASIDE ---- */
    .aside{{
      border-left:2px solid rgba(255,255,255,0.08);
      padding:.9rem 0 .9rem 1.4rem; margin-bottom:1.8rem;
      font-size:.9rem; color:var(--muted); line-height:1.75;
    }}
    .aside strong{{ color:var(--text); font-weight:600; }}
    .aside em{{ color:var(--text); }}
    .aside h4{{
      font-size:.9rem; font-weight:600; color:var(--text);
      margin-bottom:.35rem;
    }}

    /* ---- CHART ---- */
    .chart{{
      border:1px solid var(--border); border-radius:8px;
      padding:1.2rem 1.2rem .8rem; margin-bottom:2rem;
      background:var(--card);
    }}
    .chart-src{{
      font-size:.68rem; color:var(--dim); margin-top:.5rem;
      padding-top:.5rem; border-top:1px solid rgba(255,255,255,0.04);
    }}

    /* ---- TWO COL ---- */
    .two{{ display:grid; grid-template-columns:1fr 1fr; gap:1.8rem; }}
    @media(max-width:880px){{ .two{{ grid-template-columns:1fr; }} }}

    /* ---- PAIRED GRID ---- */
    .paired{{
      display:grid; grid-template-columns:1fr 1fr;
      gap:0 1.8rem;
    }}
    .paired .aside{{ align-self:end; margin-bottom:0; }}
    .paired .chart{{ align-self:start; }}
    @media(max-width:880px){{ .paired{{ grid-template-columns:1fr; }} }}

    /* ---- STATS ROW ---- */
    .stats{{
      display:grid; grid-template-columns:repeat(3, 1fr);
      gap:2rem; margin:2.5rem 0; padding:2rem 0;
      border-top:1px solid var(--border);
      border-bottom:1px solid var(--border);
    }}
    @media(max-width:700px){{ .stats{{ grid-template-columns:1fr; }} }}
    .stat{{ padding:.4rem 0; }}
    .stat .stat-n{{
      font-size:clamp(1.3rem, 2.2vw, 1.7rem); font-weight:700; display:block; color:#fff;
      line-height:1.2; margin-bottom:.5rem; white-space:nowrap;
    }}
    .stat p{{ font-size:.85rem; color:var(--muted); line-height:1.65; }}

    /* ---- CLOSING / FINAL STATEMENT ---- */
    .closing{{
      margin-top:3rem; padding:2.5rem 0 3rem;
      border-top:1px solid var(--border);
    }}
    .closing .lead{{
      font-size:1.05rem; color:var(--text); line-height:1.9; max-width:700px;
      margin-bottom:2rem; font-weight:500;
    }}
    .closing .lead strong{{ font-weight:600; }}
    .key-stats-inline{{
      font-size:.95rem; color:var(--muted); line-height:2;
      margin-bottom:2.5rem; max-width:680px;
    }}
    .key-stats-inline strong{{ color:var(--text); font-weight:600; }}
    .questions-block{{
      padding:2rem 2rem 2rem 2.2rem;
      border-left:3px solid rgba(255,255,255,0.12);
      background:rgba(255,255,255,0.02);
      border-radius:0 8px 8px 0;
      font-size:.92rem; color:var(--muted); line-height:1.9;
    }}
    .questions-block h4{{
      font-size:.9rem; font-weight:600; color:var(--text);
      margin-bottom:1rem; letter-spacing:.02em;
    }}
    .questions-block ul{{
      margin:0; padding-left:1.2rem; list-style:disc;
    }}
    .questions-block li{{ margin-bottom:.6rem; }}
    .questions-block li:last-child{{ margin-bottom:0; }}

    /* ---- TRANSITION CONNECTOR ---- */
    .connector{{
      display:flex; flex-direction:column; align-items:center;
      padding:2.5rem 2rem;
    }}
    .connector-line{{
      width:1px; height:2.5rem;
      background:linear-gradient(to bottom, transparent, var(--dim));
    }}
    .connector-dot{{
      width:6px; height:6px; border-radius:50%;
      background:var(--dim); margin:.6rem 0;
    }}
    .connector p{{
      font-size:.92rem; color:var(--dim); max-width:520px;
      text-align:center; line-height:1.85; font-style:italic;
    }}
    .connector-line-b{{
      width:1px; height:2.5rem;
      background:linear-gradient(to bottom, var(--dim), transparent);
    }}

    /* ---- NUMBERED SHIFT BLOCKS (Act 2) ---- */
    .shift-blocks{{ counter-reset:shift; }}
    .shift-block{{
      position:relative;
      padding:1.5rem 0 1.5rem 3.5rem;
      border-bottom:1px solid var(--border);
    }}
    .shift-block:last-child{{ border-bottom:none; }}
    .shift-block::before{{
      content:counter(shift);
      counter-increment:shift;
      position:absolute; left:0; top:1.5rem;
      width:2.2rem; height:2.2rem; border-radius:50%;
      border:1px solid rgba(255,255,255,0.12);
      display:flex; align-items:center; justify-content:center;
      font-size:.85rem; font-weight:700; color:var(--rose);
    }}
    .shift-block h4{{
      font-size:1rem; font-weight:600; color:#fff;
      margin-bottom:.5rem;
    }}
    .shift-block p{{
      font-size:.9rem; color:var(--muted); line-height:1.8;
      max-width:680px;
    }}
    .shift-block p strong{{ color:var(--text); font-weight:600; }}

    /* ---- POLICY TIMELINE ---- */
    .timeline{{ max-width:700px; margin:2rem 0; }}
    .tl-item{{
      position:relative;
      padding:0 0 2rem 2.8rem;
      border-left:1px solid rgba(255,255,255,0.08);
    }}
    .tl-item:last-child{{ padding-bottom:0; border-left-color:transparent; }}
    .tl-item::before{{
      content:'';
      position:absolute; left:-4px; top:.45rem;
      width:7px; height:7px; border-radius:50%;
      background:var(--rose);
    }}
    .tl-year{{
      font-size:.78rem; font-weight:700; color:var(--rose);
      letter-spacing:.04em; margin-bottom:.25rem;
    }}
    .tl-item h4{{
      font-size:.92rem; font-weight:600; color:#fff;
      margin-bottom:.3rem; line-height:1.35;
    }}
    .tl-item p{{
      font-size:.85rem; color:var(--muted); line-height:1.75;
    }}
    .tl-item p strong{{ color:var(--text); font-weight:600; }}

    /* ---- INCENTIVE BLOCK ---- */
    .incentive-block{{
      padding:1.8rem 2rem;
      border:1px solid rgba(244,63,94,0.2);
      border-radius:8px;
      background:rgba(244,63,94,0.04);
      margin:2rem 0;
      max-width:700px;
    }}
    .incentive-block h4{{
      font-size:.92rem; font-weight:600; color:var(--rose);
      margin-bottom:.8rem;
    }}
    .incentive-block p{{
      font-size:.88rem; color:var(--muted); line-height:1.8;
    }}
    .incentive-block p strong{{ color:var(--text); font-weight:600; }}

    /* ---- METHODOLOGY ---- */
    .methodology{{
      background:var(--bg2); border-top:1px solid var(--border);
      padding:4rem 0;
    }}
    .methodology h3{{ color:var(--muted); font-size:.95rem; margin-bottom:.8rem; font-weight:600; }}
    .methodology p,.methodology li{{ font-size:.82rem; color:var(--dim); line-height:1.75; }}
    .methodology ul{{ padding-left:1.2rem; }}
    .methodology li{{ margin-bottom:.35rem; }}
    .methodology a{{ color:var(--sky); text-decoration:none; }}

    footer{{
      background:var(--bg); border-top:1px solid var(--border);
      padding:2rem; text-align:center; font-size:.72rem; color:var(--dim);
    }}
  </style>
</head>
<body>

<div class="progress-bar" id="progressBar"></div>

<!-- ===== HERO ===== -->
<section class="hero">
  <div class="hero-inner">
    <div class="hero-tag">Data Investigation &nbsp;&middot;&nbsp; Census &nbsp;&middot;&nbsp; FRED &nbsp;&middot;&nbsp; BLS</div>
    <h1>Generation <em>Priced Out</em></h1>
    <p class="hero-sub">How 30 Looks Nothing Like It Used To</p>

    <p class="hero-lede">
      In 1983, a single income could buy a home, most 30-year-olds were married,
      and starting a family was the default. Four decades later, every one of those
      milestones has moved further out of reach &mdash; and the metrics used to track
      them were quietly redesigned in ways that make the decline look smaller than it is.
    </p>

    <div class="sc-context">Life milestones for Americans aged 25&ndash;34</div>
    <div class="scorecard">
      <div class="sc-head">
        <span></span>
        <span>1983</span>
        <span></span>
        <span>{yr_latest_yr}</span>
      </div>
      <div class="sc-row">
        <div class="sc-label">
          <div class="sc-metric">Living Independently</div>
          <div class="sc-desc">Not living in a parent&rsquo;s or relative&rsquo;s home</div>
        </div>
        <div class="sc-val old">{stats['indep_1983']:.0f}%</div>
        <div class="sc-delta"><span class="material-symbols-outlined">trending_down</span></div>
        <div class="sc-val now">{stats['indep_now']:.0f}%</div>
      </div>
      <div class="sc-row">
        <div class="sc-label">
          <div class="sc-metric">Married</div>
          <div class="sc-desc">Currently married, Census CPS</div>
        </div>
        <div class="sc-val old">{stats['married_1983']:.0f}%</div>
        <div class="sc-delta"><span class="material-symbols-outlined">trending_down</span></div>
        <div class="sc-val now">{stats['married_now']:.0f}%</div>
      </div>
      <div class="sc-row">
        <div class="sc-label">
          <div class="sc-metric">Homeownership</div>
          <div class="sc-desc">Per household &mdash; looks flat, but now requires two earners. Per-earner effective rate: ~{stats['ho_earner_new']:.0f}%</div>
        </div>
        <div class="sc-val old">{stats['homeown_1983']:.1f}%</div>
        <div class="sc-delta"><span class="material-symbols-outlined">trending_down</span></div>
        <div class="sc-val now">{stats['homeown_now']:.1f}%</div>
      </div>
      <div class="sc-row">
        <div class="sc-label">
          <div class="sc-metric">Home Price / Income</div>
          <div class="sc-desc">Years of <em>combined</em> household income to buy a median home &mdash; or {stats['pi_ratio_new']:.1f}&times; a single earner&rsquo;s income</div>
        </div>
        <div class="sc-val old">{stats['ratio_old']:.1f}&times;</div>
        <div class="sc-delta"><span class="material-symbols-outlined">trending_up</span></div>
        <div class="sc-val now">{stats['ratio_new']:.1f}&times;</div>
      </div>
      <div class="sc-row">
        <div class="sc-label">
          <div class="sc-metric">Fertility Rate</div>
          <div class="sc-desc">Births per woman; 2.1 needed to sustain population</div>
        </div>
        <div class="sc-val old">{stats['tfr_1983']:.2f}</div>
        <div class="sc-delta"><span class="material-symbols-outlined">trending_down</span></div>
        <div class="sc-val now">{stats['tfr_now']:.2f}</div>
      </div>
    </div>

    <p class="hero-body">
      Marriage fell <strong style="color:var(--amber)">{abs(pp_married):.0f} percentage points</strong>.
      A median home costs <strong style="color:var(--rose)">{stats['ratio_new']:.1f}&times; household income</strong>
      &mdash; or <strong style="color:var(--violet)">{stats['pi_ratio_new']:.1f}&times;</strong> on a single salary.
      The fertility rate sits <strong style="color:var(--emerald)">below replacement</strong> and falling.
      These are the official numbers. The real picture is worse.
    </p>
    <a href="#sec-decline" class="hero-cta">Explore the data &rarr;</a>
    <div class="scroll-cue">&darr; scroll to explore &darr;</div>
  </div>
</section>

<!-- ===== ACT 1: THE DECLINE ===== -->
<section id="sec-decline" class="sec">
  <div class="container">
    <div class="sec-num reveal">01 &mdash; The Decline</div>
    <h2 class="reveal">Four Decades, Four Milestones, One Direction</h2>
    <p class="lead reveal">
      Every indicator of independent adult life for 25-to-34-year-olds has moved in the same direction
      since the early 1980s &mdash; down. <strong>Marriage fell the hardest</strong>: from
      <strong style="color:var(--amber)">64%</strong> to
      <strong style="color:var(--amber)">38%</strong>,
      a generational shift from default to exception.
    </p>
    <div class="chart reveal">
      {chart_overlay}
      <div class="chart-src">Sources: Census CPS Tables AD-1, MS-2; Census HVS Table 14; World Bank</div>
    </div>

    <div class="two reveal" style="margin-bottom:.5rem">
      <div class="chart">{chart_living}</div>
      <div class="chart">{chart_marriage}</div>
    </div>
    <div class="two reveal">
      <div class="chart">{chart_homeownership}</div>
      <div class="chart">{chart_tfr}</div>
    </div>

    <div class="stats reveal">
      <div class="stat" style="--i:0">
        <span class="stat-n" style="color:var(--amber)">{stats['married_1983']:.0f}% &rarr; {stats['married_now']:.0f}%</span>
        <p>Marriage rate for 25-to-34-year-olds. A <strong style="color:var(--amber)">{abs(pp_married):.0f}-point</strong> collapse &mdash; once the norm, now a minority status.</p>
      </div>
      <div class="stat" style="--i:1">
        <span class="stat-n" style="color:var(--sky)">{stats['homeown_1983']:.1f}% &rarr; {stats['homeown_now']:.1f}%</span>
        <p>Homeownership rate, householder under 35. Even the bubble peak of <strong style="color:var(--sky)">43.1%</strong> in 2004 barely exceeded the 1982 level.</p>
      </div>
      <div class="stat" style="--i:2">
        <span class="stat-n" style="color:var(--emerald)">{stats['tfr_now']:.2f} births per woman</span>
        <p>US fertility rate in {tfr_latest_yr}. Below the <strong style="color:var(--emerald)">2.1</strong> replacement threshold and falling to record lows since 2007.</p>
      </div>
    </div>
  </div>
</section>

<!-- ---- Connector 1 ---- -->
<div class="connector">
  <div class="connector-line"></div>
  <div class="connector-dot"></div>
  <p class="reveal">Those are the official numbers. But the tools used to produce them have blind spots &mdash; some by design, some by economic drift &mdash; that make the decline look smaller than it is.</p>
  <div class="connector-dot"></div>
  <div class="connector-line-b"></div>
</div>

<!-- ===== ACT 2: THE YARDSTICK CHANGED ===== -->
<section id="sec-yardstick" class="sec">
  <div class="container">
    <div class="sec-num reveal">02 &mdash; The Blind Spots</div>
    <h2 class="reveal">One Methodology Change and Two Legacy Assumptions</h2>
    <p class="lead reveal">
      The numbers in Section 01 are bad. They are also <strong>measured with tools that no longer
      reflect the economic reality they were built for</strong>. One was a deliberate methodology change.
      The other two became misleading as the economy shifted around them.
    </p>

    <div class="shift-blocks">
      <div class="shift-block reveal">
        <h4>The Methodology Change: CPI &amp; Housing &mdash; January 1983</h4>
        <p>
          The Bureau of Labor Statistics stopped tracking the actual cost of buying a home &mdash;
          mortgage payments, property taxes, insurance, prices &mdash; and replaced it with
          <strong>Owners&rsquo; Equivalent Rent</strong> (OER): a survey asking homeowners what they
          <em>think</em> it would cost to rent their place. OER now accounts for roughly <strong>a quarter</strong> of
          headline CPI (26&ndash;27% depending on year), the single largest component.
        </p>
        <p style="margin-top:.8rem;">
          This matters because every government expenditure pegged to &ldquo;inflation&rdquo; &mdash;
          Social Security COLAs, tax bracket adjustments, federal pensions, SNAP benefits &mdash;
          now rises more slowly. A CPI that understates housing costs by even one percentage point
          saves the federal government tens of billions per year. In 1996, the
          <strong>Boskin Commission</strong> (appointed by the Senate Finance Committee) recommended
          further reductions, arguing CPI overstated inflation by 1.1 points. The CBO estimated those
          changes alone would save <strong>$1 trillion over 12 years</strong>.
        </p>
        <p style="margin-top:.8rem;">
          Since 1984: CPI-Shelter grew
          <strong style="color:var(--amber)">{stats['cpi_shelter_growth_x']:.1f}&times;</strong>.
          Actual home prices grew
          <strong style="color:var(--rose)">{stats['hp_growth_x']:.1f}&times;</strong>.
          The gap between those two numbers is the cost this methodology change hides.
        </p>
      </div>

      <div class="shift-block reveal">
        <h4>The Legacy Assumption: &ldquo;Household Income&rdquo; Means One Earner</h4>
        <p>
          Nobody changed how household income is reported &mdash; the economy changed what a household
          <em>is</em>. In 1984, &ldquo;household income&rdquo; typically meant <strong>one earner</strong>.
          Today it almost always means <strong>two</strong>. Average household size shrank from
          <strong>2.73</strong> to <strong>2.51</strong> people
          (Census Table HH-4). The standard charts show household income growing
          <strong style="color:var(--sky)">{stats['hh_income_growth_x']:.1f}&times;</strong> &mdash; but that growth
          came from <em>adding a second paycheck</em>, not from wages keeping up with prices.
        </p>
        <p style="margin-top:.8rem;">
          A single earner in 1984 needed
          <strong style="color:var(--violet)">{stats['pi_ratio_old']:.1f} years</strong>
          of their income to buy a median home. Today:
          <strong style="color:var(--violet)">{stats['pi_ratio_new']:.1f} years</strong>
          (FRED MEPAINUSA646N &mdash; measured, not estimated).
          The metric didn&rsquo;t change. The reality it describes did.
        </p>
      </div>

      <div class="shift-block reveal">
        <h4>The Consequence: Homeownership Is Counted Per Household, Not Per Person</h4>
        <p>
          This follows directly from the shift above. The homeownership rate is measured
          <em>per household</em>. When one income could buy a house, the household rate roughly
          approximated individual ownership. Now two earners pool their income to qualify for a
          single mortgage &mdash; and share one unit of &ldquo;homeownership.&rdquo;
        </p>
        <p style="margin-top:.8rem;">
          The reported rate for under-35 households:
          <strong style="color:var(--sky)">{stats['homeown_now']:.1f}%</strong>.
          Adjust for the number of earners per household and the effective per-person rate
          drops to roughly <strong style="color:var(--rose)">{stats['ho_earner_new']:.1f}%</strong>
          &mdash; nearly half the headline figure.
        </p>
      </div>
    </div>
  </div>
</section>

<!-- ---- Connector 2 ---- -->
<div class="connector">
  <div class="connector-line"></div>
  <div class="connector-dot"></div>
  <p class="reveal">Now see what the numbers look like when you account for these blind spots.</p>
  <div class="connector-dot"></div>
  <div class="connector-line-b"></div>
</div>

<!-- ===== ACT 3: THE REAL NUMBERS ===== -->
<section id="sec-real" class="sec">
  <div class="container">
    <div class="sec-num reveal">03 &mdash; The Real Numbers</div>
    <h2 class="reveal">Reported vs. Corrected</h2>
    <p class="lead reveal">
      Each chart below pairs the standard reported metric with the corrected version.
      The shaded gaps show what the reporting shifts hide.
    </p>

    <!-- Chart: Great Divergence -->
    <div class="aside reveal">
      <h4>Reading this chart</h4>
      <strong style="color:var(--amber)">CPI: Shelter</strong> and
      <strong style="color:var(--sky)">household income</strong> track each other closely &mdash;
      by official measures, housing looks manageable.<br>
      The <strong style="color:var(--rose)">shaded gap</strong> above the CPI line is the real cost
      the 1983 OER methodology change masks. All three series start at 100 in 1984.
    </div>
    <div class="chart reveal">
      {chart_divergence}
      <div class="chart-src">Sources: FRED MSPUS, MEHOINUSA646N, CUSR0000SAH1. All indexed to 1984 = 100.</div>
    </div>

    <!-- Charts: Affordability paired -->
    <div class="paired reveal">
      <div class="aside">
        <h4>Price-to-Income</h4>
        Years of gross income to buy a median home.<br>
        <strong style="color:var(--rose)">Household</strong> = industry standard (two earners).<br>
        <strong style="color:var(--violet)">Individual</strong> = what a single earner actually faces.
      </div>
      <div class="aside">
        <h4>Mortgage Burden</h4>
        Monthly payment as % of income (20% down, 30-yr fixed).<br>
        <strong style="color:var(--rose)">30% line</strong> = standard cost-burden threshold.<br>
        A single earner today: <strong style="color:var(--violet)">{stats['pi_pmt_new']:.0f}%</strong> of their paycheck.<br>
        <span style="color:var(--dim); font-size:.82rem;">
          Note: in 1984 mortgage rates averaged {stats['rate_1984']:.1f}%. Today: ~{stats['rate_now']:.1f}%.
          Despite much lower rates now, the raw price increase has made payments <em>less</em> affordable.
        </span>
      </div>
      <div class="chart">
        {chart_affordability}
        <div class="chart-src">Derived: FRED MSPUS / MEHOINUSA646N &amp; MEPAINUSA646N</div>
      </div>
      <div class="chart">
        {chart_payment}
        <div class="chart-src">Derived: FRED MSPUS, MORTGAGE30US / MEHOINUSA646N &amp; MEPAINUSA646N</div>
      </div>
    </div>

    <!-- Chart: Per-earner homeownership -->
    <div class="aside reveal">
      <h4>Reported vs. Per-Earner Homeownership</h4>
      <strong style="color:var(--sky)">Blue</strong> = reported rate (per household).<br>
      <strong style="color:var(--rose)">Red</strong> = effective rate per earner.<br>
      The shaded gap is ownership that exists only because two paychecks are pooled into one mortgage.
    </div>
    <div class="chart reveal">
      {chart_ho_earner}
      <div class="chart-src">Derived: Census HVS Table 14 / (FRED MEHOINUSA646N &divide; MEPAINUSA646N)</div>
    </div>

    <!-- Chart: What your dollar buys -->
    <div class="aside reveal">
      <h4>And You Get Less For It</h4>
      After paying more of your income for longer, the physical product has also shrunk.
      Cost per square foot has climbed steadily while the median lot size has fallen &mdash;
      more money for less house on less land.
    </div>
    <div class="chart reveal">
      {chart_whatyouget}
      <div class="chart-src">Sources: FRED MSPNHSUS / COMPSFLAM1FQ; Census SOC / Fed FEDS Notes</div>
    </div>

    <div class="closing reveal">
      <p class="lead" style="font-size:1.1rem; color:#fff; border-left:3px solid var(--rose); padding-left:1.4rem;">
        In 1984, a median home cost <strong style="color:var(--rose)">{stats['ratio_old']:.1f} years</strong>
        of household income. In {yr_housing_latest_yr}, it costs
        <strong style="color:var(--rose)">{stats['ratio_new']:.1f} years</strong>.
        But &ldquo;household income&rdquo; in 1984 usually meant one paycheck. Today it means two.
        Measured against a single earner&rsquo;s salary, a median home now costs
        <strong style="color:var(--violet)">{stats['pi_ratio_new']:.1f} years</strong> of gross income.
        The per-earner homeownership rate for under-35s is
        <strong style="color:var(--rose)">{stats['ho_earner_new']:.1f}%</strong> &mdash;
        not the <strong style="color:var(--sky)">{stats['homeown_now']:.1f}%</strong> the headlines report.
      </p>
      <p class="key-stats-inline" style="margin-top:1rem; font-style:italic;">
        Mortgage rates fell from <strong>{stats['rate_1984']:.0f}%</strong> in 1984 to
        <strong>{stats['rate_now']:.0f}%</strong> in {int(stats['rate_now_yr'])} &mdash;
        a historic collapse in borrowing costs. Yet the monthly payment as a share of household income
        barely budged (from ~<strong>{stats['pmt_hh_old']:.0f}%</strong> to
        ~<strong>{stats['pmt_hh_new']:.0f}%</strong>). Every point of rate relief
        was absorbed by rising prices.
        The crisis isn&rsquo;t just that housing got harder.
        It&rsquo;s that the standard metrics were not designed to show how much harder.
      </p>

      <h3 style="color:#fff; font-size:1.15rem; margin:3rem 0 .8rem; font-weight:700;">How We Got Here</h3>
      <p class="key-stats-inline" style="margin-bottom:1.5rem;">
        This didn&rsquo;t happen by accident. A series of policy decisions &mdash; each defensible in isolation &mdash;
        compounded over four decades to produce the affordability crisis documented above. Here are the inflection points.
      </p>

      <div class="timeline">
        <div class="tl-item">
          <div class="tl-year">1983</div>
          <h4>BLS replaces housing costs with Owners&rsquo; Equivalent Rent</h4>
          <p>
            The CPI stopped measuring what it actually costs to buy a home and switched to asking
            homeowners what they think they&rsquo;d pay in rent. The change was proposed during the
            Carter administration and implemented under Reagan. Every government expenditure tied to
            inflation &mdash; Social Security, tax brackets, the poverty line &mdash; has since risen
            more slowly than actual housing costs.
          </p>
        </div>
        <div class="tl-item">
          <div class="tl-year">1996</div>
          <h4>The Boskin Commission recommends further CPI reductions</h4>
          <p>
            Appointed by the Senate Finance Committee, the commission argued that CPI overstated
            inflation by <strong>1.1 percentage points per year</strong>. The Congressional Budget
            Office estimated adopting these changes would save the federal government
            <strong>roughly $1 trillion over 12 years</strong> through lower COLA payments.
            Many of the recommendations were adopted. Lower measured inflation meant lower
            government obligations &mdash; and a growing gap between official statistics and lived costs.
          </p>
        </div>
        <div class="tl-item">
          <div class="tl-year">1997</div>
          <h4>Taxpayer Relief Act: homes become tax-sheltered investments</h4>
          <p>
            Signed by President Clinton with bipartisan support, this law exempted up to
            <strong>$250K/$500K in capital gains</strong> on home sales from taxation.
            Overnight, a primary residence became the most tax-advantaged asset class available
            to ordinary Americans. Existing homeowners now had a direct financial incentive to
            support policies that raised property values &mdash; and oppose new construction that
            might lower them.
          </p>
        </div>
        <div class="tl-item">
          <div class="tl-year">2001&ndash;2006</div>
          <h4>The Fed holds rates near historic lows; lending standards collapse</h4>
          <p>
            The Greenspan and early Bernanke Fed kept rates exceptionally low after the dot-com
            bust. Loose monetary policy, combined with the relaxation of lending standards and the
            securitization of mortgages, inflated a housing bubble that priced a generation of
            first-time buyers into debt they couldn&rsquo;t sustain.
          </p>
        </div>
        <div class="tl-item">
          <div class="tl-year">2012&ndash;present</div>
          <h4>Institutional investors enter single-family housing</h4>
          <p>
            After the 2008 crash, private equity firms began purchasing foreclosed homes at scale.
            <strong>Blackstone&rsquo;s Invitation Homes</strong> became the largest single-family
            landlord in the United States. By 2023, institutional investors accounted for a significant
            share of home purchases in many metro areas, competing directly with first-time buyers
            and converting ownership stock into rental inventory.
          </p>
        </div>
        <div class="tl-item">
          <div class="tl-year">Ongoing</div>
          <h4>Local zoning blocks new supply; existing owners vote to protect values</h4>
          <p>
            Homeowners vote at higher rates than renters. Local zoning boards &mdash; elected by and
            accountable to existing homeowners &mdash; routinely block new housing that might increase
            supply and moderate prices. The result: a structural shortage that benefits those who
            already own property at the direct expense of those trying to buy in.
          </p>
        </div>
      </div>

      <div class="incentive-block">
        <h4>Why the official numbers stay quiet</h4>
        <p>
          Governments don&rsquo;t just <em>measure</em> inflation &mdash; they <em>pay</em> based on it.
          Social Security COLAs, military pay raises, SNAP benefits, federal pensions, and tax-bracket
          adjustments are all indexed to CPI. A CPI that runs even <strong>one percentage point below
          real housing costs</strong> saves the federal government tens of billions of dollars annually.
          No administration &mdash; regardless of party &mdash; has a fiscal incentive to make the
          number more accurate if accuracy means higher obligations. The Boskin Commission made this
          logic explicit: lower CPI = lower deficits. The cost is borne by the people whose wages,
          benefits, and purchasing power are benchmarked to a number that undercounts their largest expense.
        </p>
      </div>

      <!-- International context -->
      <h3 style="color:#fff; font-size:1.15rem; margin:2.5rem 0 .8rem; font-weight:700;">Global Context: This Is Not Just an American Story</h3>
      <p class="key-stats-inline" style="margin-bottom:1.5rem;">
        The fertility decline is real and widespread. But the depth varies by policy environment.
        Nations with aggressive pro-family investment (France) have maintained rates near replacement.
        Nations where housing costs have outpaced wages most severely (South Korea, Japan)
        show where the trend leads. The US sits in between &mdash; declining, and accelerating.
      </p>
      <div class="chart">
        {chart_intl_tfr}
        <div class="chart-src">Source: World Bank SP.DYN.TFRT.IN</div>
      </div>

      <div class="questions-block" style="margin-top:2.5rem;">
        <h4>The question this data raises</h4>
        <p style="font-size:.92rem; color:var(--muted); line-height:1.85; margin-bottom:1rem;">
          Every data point above comes from a public source. The Census, FRED, BLS, and the World Bank
          publish these numbers freely. The decline is not hidden &mdash; it&rsquo;s just measured with
          tools that were built for a different economy, and nobody in a position of authority has an
          incentive to update them.
        </p>
        <p style="font-size:.95rem; color:var(--text); line-height:1.85; font-weight:500;">
          The question is not whether young Americans are worse off. The data is unambiguous.
          The question is why the standard metrics were allowed to quietly drift out of alignment
          with reality &mdash; and who benefits from the gap.
        </p>
      </div>
    </div>
  </div>
</section>

<!-- ===== METHODOLOGY ===== -->
<div class="methodology">
  <div class="container">
    <h3>Data Sources &amp; Methodology</h3>
    <ul>
      <li><strong>Living Independently:</strong> % of 25-34 year-olds NOT in parent(s)' home. Census CPS Table AD-1. <a href="https://www.census.gov/data/tables/time-series/demo/families/adults.html">census.gov</a></li>
      <li><strong>Marriage Rate:</strong> % of 25-34 year-olds currently married. Census CPS Table MS-2. <a href="https://www.census.gov/data/tables/time-series/demo/families/marital.html">census.gov</a></li>
      <li><strong>Homeownership:</strong> Rate for householder under 35. Census HVS Table 14. <a href="https://www.census.gov/housing/hvs/data/histtabs.html">census.gov</a></li>
      <li><strong>Median Home Price:</strong> FRED series MSPUS (quarterly median sales price, Census/HUD). <a href="https://fred.stlouisfed.org/series/MSPUS">fred.stlouisfed.org</a></li>
      <li><strong>Median Household Income:</strong> FRED series MEHOINUSA646N (nominal annual, Census). <a href="https://fred.stlouisfed.org/series/MEHOINUSA646N">fred.stlouisfed.org</a></li>
      <li><strong>Per Capita Income:</strong> FRED series A792RC0A052NBEA (nominal annual, BEA). <a href="https://fred.stlouisfed.org/series/A792RC0A052NBEA">fred.stlouisfed.org</a></li>
      <li><strong>Median Personal Income:</strong> FRED series MEPAINUSA646N (nominal annual, Census). <a href="https://fred.stlouisfed.org/series/MEPAINUSA646N">fred.stlouisfed.org</a></li>
      <li><strong>30-Year Mortgage Rate:</strong> FRED series MORTGAGE30US (Freddie Mac PMMS). <a href="https://fred.stlouisfed.org/series/MORTGAGE30US">fred.stlouisfed.org</a></li>
      <li><strong>CPI (All Items):</strong> FRED series CPIAUCSL &mdash; Consumer Price Index for All Urban Consumers (BLS). <a href="https://fred.stlouisfed.org/series/CPIAUCSL">fred.stlouisfed.org</a></li>
      <li><strong>CPI: Shelter:</strong> FRED series CUSR0000SAH1 &mdash; uses &ldquo;Owners&rsquo; Equivalent Rent&rdquo; methodology (BLS). <a href="https://fred.stlouisfed.org/series/CUSR0000SAH1">fred.stlouisfed.org</a></li>
      <li><strong>New Home Sqft:</strong> FRED series COMPSFLAM1FQ (Census SOC). <a href="https://fred.stlouisfed.org/series/COMPSFLAM1FQ">fred.stlouisfed.org</a></li>
      <li><strong>Lot Size:</strong> Census Survey of Construction; Fed FEDS Notes (2017). <a href="https://www.federalreserve.gov/econres/notes/feds-notes/trends-in-upsizing-houses-and-shrinking-lots-20171103.html">federalreserve.gov</a></li>
      <li><strong>US TFR:</strong> World Bank SP.DYN.TFRT.IN. <a href="https://data.worldbank.org/">worldbank.org</a></li>
    </ul>
    <p style="margin-top:1rem;">
      <strong>Derived metrics:</strong> Price-to-Income (Household) = MSPUS / MEHOINUSA646N.
      Price-to-Income (Individual) = MSPUS / MEPAINUSA646N. Monthly payment uses
      standard amortization (80% LTV, 30-year term, annual average of MORTGAGE30US). Payment-to-Income
      (Household) = monthly payment / (MEHOINUSA646N / 12). Payment-to-Income (Individual) = monthly
      payment / (MEPAINUSA646N / 12). Per-earner homeownership = HVS rate / (MEHOINUSA646N / MEPAINUSA646N).
      All indexed series use 1984 as base year (= 100).
    </p>
    <p style="margin-top:.5rem;">
      <strong>Limitations:</strong> CPS and HVS data are survey-based. MSPUS is all housing types
      (not age-filtered). Mortgage calculation assumes 20% down &mdash; many first-time buyers put down less,
      making the burden higher. Lot size data post-2017 is extrapolated from Census SOC trends.
      Individual income charts use MEPAINUSA646N (median personal income for all workers with income,
      ages 15+), which slightly overstates individual earning power for 25-34 year-olds specifically.
      The earners-per-household proxy (household / personal income) is an approximation; it captures
      the macro shift from single- to dual-earner households but does not account for part-time vs.
      full-time composition.
    </p>

    <h3 style="margin-top:2rem;">Measurement Notes: How Government Reporting Has Changed</h3>
    <ul>
      <li><strong>CPI &amp; Shelter (1983):</strong> In January 1983, BLS replaced direct home-purchase
        cost tracking in the CPI with Owners&rsquo; Equivalent Rent (OER). OER measures what homeowners
        <em>would</em> pay to rent their home, not what it actually costs to buy one. OER now accounts
        for roughly a quarter of headline CPI (26&ndash;27%). As a result, CPI-U and all statistics adjusted by it (Social Security,
        tax brackets, poverty thresholds) structurally undercount housing cost inflation.</li>
      <li><strong>Household Income (composition drift):</strong> Average household size fell from 2.73 (1983)
        to 2.51 (2023). Single-person households rose from ~22% to 29%. Dual-income households became the
        norm. Median household income comparisons across decades therefore compare different-sized economic
        units &mdash; we include per capita income (FRED A792RC0A052NBEA) to control for this.</li>
      <li><strong>CPS Living Arrangements (2007):</strong> The Census Bureau expanded CPS relationship
        categories in 2007 to directly capture cohabitation. Our &ldquo;living at parents&rsquo; home&rdquo; metric
        (Table AD-1: child of householder) is robust to this change.</li>
      <li><strong>CPS Marriage (2015&ndash;2017):</strong> Same-sex married couples were not properly counted
        until 2015&ndash;2017 CPS revisions. The effect on our 25-34 marriage rate is negligible (~1% of
        marriages are same-sex).</li>
      <li><strong>HVS Homeownership (2020):</strong> Census suspended in-person HVS data collection
        in March 2020, dropping response rates from 82-83% to 73%. The Bureau acknowledged this likely
        inflated 2020 homeownership estimates. Post-2022 data returned to standard collection methods.</li>
    </ul>
  </div>
</div>

<footer>
  <p>Data study by <strong>Data Story</strong> &middot; Built with Python, Plotly, Census Bureau, FRED, BLS</p>
  <p style="margin-top:.4rem;">All data from public sources. Every figure linked to its original table above.</p>
</footer>

<script>
(function(){{
  /* Scroll progress bar */
  var bar = document.getElementById('progressBar');
  window.addEventListener('scroll', function(){{
    var h = document.documentElement;
    var pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
    bar.style.width = pct + '%';
  }}, {{passive:true}});

  /* IntersectionObserver for .reveal elements */
  var els = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {{
    var obs = new IntersectionObserver(function(entries){{
      entries.forEach(function(e){{
        if (e.isIntersecting) {{
          e.target.classList.add('visible');
          obs.unobserve(e.target);
        }}
      }});
    }}, {{threshold:0.12, rootMargin:'0px 0px -40px 0px'}});
    els.forEach(function(el){{ obs.observe(el); }});
  }} else {{
    els.forEach(function(el){{ el.classList.add('visible'); }});
  }}
}})();
</script>

</body>
</html>"""


# ---------------------------------------------------------------------------
# Inject embedded Plotly.js
# ---------------------------------------------------------------------------
plotly_js = get_plotlyjs().replace("</script>", "</scr" + "ipt>")
script_tag = f'<script charset="utf-8">{plotly_js}</script>'
HTML = HTML.replace(
    '<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@3.4.0/plotly.min.js" charset="utf-8"></script>',
    script_tag,
)

# ---------------------------------------------------------------------------
# Write output
# ---------------------------------------------------------------------------
out_path = Path(__file__).parent / "reports" / "dashboard.html"
out_path.parent.mkdir(exist_ok=True)
out_path.write_text(HTML)
size_kb = out_path.stat().st_size / 1024
print(f"\n+ Dashboard written: {out_path}")
print(f"  Size: {size_kb:,.0f} KB")
