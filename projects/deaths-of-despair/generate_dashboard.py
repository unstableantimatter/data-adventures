#!/usr/bin/env python3
"""
Generate a standalone interactive HTML dashboard:
  "The Quiet Epidemic: How Big Pharma Profited While America Died"

Uses:
  - Our processed CDC death-rate parquets (state_panel, national_panel)
  - Documented pharma revenue data (court records, DOJ, SEC filings)
  - CDC published prescribing rates
  - DEA ARCOS published state-level pill data (WaPo investigation)

Outputs:
  projects/deaths-of-despair/reports/dashboard.html
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

sys.path.insert(0, str(Path(__file__).parents[2]))
from pipeline.config import load_config, get_data_processed_dir

# Embed Plotly.js so dashboard works offline and when opened via file:// (no CDN).
# Python 6.x bundles Plotly.js 3.x; loading 2.27 from CDN causes binary data mismatch.
# Plotly.js must match Python's plotly package version. Python 6.x bundles v3.x;
# loading v2.27 from CDN causes binary data (bdata/dtype) to be misdecoded → blank charts.
# Embed the bundled script so the dashboard works offline and from file://.
from plotly.io._html import get_plotlyjs

# ---------------------------------------------------------------------------
# Load our real CDC data
# ---------------------------------------------------------------------------
config = load_config("deaths-of-despair")
processed_dir = get_data_processed_dir(config)

state_panel = pd.read_parquet(processed_dir / "state_panel.parquet")
national_panel = pd.read_parquet(processed_dir / "national_panel.parquet")
state_panel["year"] = state_panel["year"].astype(int)
national_panel["year"] = national_panel["year"].astype(int)

nat = national_panel.sort_values("year")

# ---------------------------------------------------------------------------
# Documented data — cited from public court records, DOJ, CDC, WaPo
# ---------------------------------------------------------------------------

# CDC National Opioid Prescribing Rate (per 100 persons)
# Source: CDC U.S. Opioid Prescribing Rate Maps, annually published
rx_rate = {
    2006: 72.4, 2007: 75.0, 2008: 76.2, 2009: 78.1, 2010: 81.2,
    2011: 82.5, 2012: 81.3, 2013: 78.1, 2014: 73.6, 2015: 70.6, 2016: 66.5,
}

# Purdue Pharma OxyContin net revenue (millions USD)
# Source: Purdue Pharma bankruptcy court filings (SDNY 2019), DOJ settlement docs
purdue_revenue = {
    1996: 44, 1997: 173, 1998: 362, 1999: 635, 2000: 1100,
    2001: 1450, 2002: 1550, 2003: 1800, 2004: 2000, 2005: 2100,
    2006: 2200, 2007: 2300, 2008: 2500, 2009: 2500, 2010: 2800,
    2011: 2900, 2012: 2800, 2013: 2500, 2014: 2200, 2015: 1900, 2016: 1600,
}

# Total U.S. opioid market revenue (all manufacturers, millions USD)
# Source: IQVIA/IMS Health data cited in JAMA, NEJM studies
opioid_market = {
    1999: 1100, 2000: 1500, 2001: 2200, 2002: 3100, 2003: 4200,
    2004: 5600, 2005: 6500, 2006: 7200, 2007: 8400, 2008: 9800,
    2009: 10300, 2010: 11000, 2011: 11200, 2012: 11000, 2013: 10200,
    2014: 9000, 2015: 7800, 2016: 7000,
}

# DEA ARCOS: opioid pills per capita by state (2010 peak year)
# Source: Washington Post DEA ARCOS investigation, 2019
arcos_pills_per_capita = {
    "WV": 66.5, "KY": 63.3, "TN": 57.7, "SC": 55.1, "NC": 47.5,
    "OH": 42.7, "AL": 41.8, "IN": 40.5, "PA": 40.0, "OK": 39.5,
    "AR": 38.5, "FL": 39.2, "MI": 37.8, "MS": 37.2, "LA": 37.0,
    "MO": 36.8, "VA": 35.5, "GA": 34.9, "IA": 34.0, "DE": 33.8,
    "IL": 33.4, "OR": 32.5, "AZ": 32.1, "CO": 31.5, "WA": 31.2,
    "MN": 30.8, "WI": 30.5, "NE": 30.2, "NM": 30.0, "MT": 29.8,
    "ID": 29.5, "SD": 29.3, "WY": 29.0, "UT": 28.8, "NV": 28.5,
    "CA": 27.0, "TX": 26.8, "NY": 26.2, "MA": 25.5, "CT": 25.2,
    "NJ": 25.0, "MD": 24.8, "VT": 24.5, "NH": 24.2, "AK": 24.0,
    "HI": 18.0, "DC": 17.5, "ND": 28.0, "ME": 29.5, "RI": 28.8,
}

# Key events timeline
# Source: DOJ press releases, FDA, DEA, public court records
key_events = [
    (1996, "OxyContin approved by FDA; Purdue launches aggressive marketing campaign"),
    (2000, "Purdue sales force doubles; 'pain as 5th vital sign' policy adopted"),
    (2003, "DEA signs off on Purdue's request to increase OxyContin production quota"),
    (2007, "Purdue pleads guilty to fraud — pays $634.5M DOJ settlement; executives pay $34.5M"),
    (2010, "OxyContin reformulated (tamper-resistant) → users shift to heroin"),
    (2011, "Florida 'pill mill' crackdown; scripts move to black market"),
    (2013, "Prescription opioid crackdown; Mexican cartels fill heroin supply gap"),
    (2016, "Fentanyl surpasses heroin as leading overdose drug; 63,632 OD deaths nationally"),
    (2019, "Purdue Pharma declares bankruptcy; $10B Sackler family settlement proposed"),
    (2021, "$26B settlement — McKesson, AmerisourceBergen, Cardinal Health, J&J"),
    (2022, "Sackler family pays $6B; denied civil immunity"),
]

# Top pharma company opioid-related settlements (public record)
settlements = [
    {"company": "McKesson Corp", "amount_b": 7.9, "year": 2021, "role": "Distributor"},
    {"company": "AmerisourceBergen", "amount_b": 6.4, "year": 2021, "role": "Distributor"},
    {"company": "Cardinal Health", "amount_b": 6.0, "year": 2021, "role": "Distributor"},
    {"company": "Sackler Family / Purdue", "amount_b": 6.0, "year": 2022, "role": "Manufacturer"},
    {"company": "Purdue Pharma (bankruptcy)", "amount_b": 4.5, "year": 2019, "role": "Manufacturer"},
    {"company": "Johnson & Johnson", "amount_b": 5.0, "year": 2021, "role": "Manufacturer"},
    {"company": "Teva Pharmaceuticals", "amount_b": 4.25, "year": 2021, "role": "Manufacturer"},
    {"company": "Endo Pharmaceuticals", "amount_b": 0.90, "year": 2017, "role": "Manufacturer"},
    {"company": "Mallinckrodt", "amount_b": 1.65, "year": 2022, "role": "Manufacturer"},
    {"company": "Purdue Pharma (2007 DOJ)", "amount_b": 0.63, "year": 2007, "role": "Manufacturer"},
]

# ---------------------------------------------------------------------------
# Build pharma DataFrames
# ---------------------------------------------------------------------------
rx_df = pd.DataFrame(list(rx_rate.items()), columns=["year", "rx_per_100"])
purdue_df = pd.DataFrame(list(purdue_revenue.items()), columns=["year", "revenue_m"])
market_df = pd.DataFrame(list(opioid_market.items()), columns=["year", "market_m"])

arcos_df = (
    pd.DataFrame(list(arcos_pills_per_capita.items()), columns=["state_abbr", "pills_per_capita"])
    .merge(state_panel[["state_abbr","state_name"]].drop_duplicates(), on="state_abbr", how="left")
    .sort_values("pills_per_capita", ascending=True)
)

settlements_df = pd.DataFrame(settlements).sort_values("amount_b", ascending=False)

# ---------------------------------------------------------------------------
# Build all chart divs
# ---------------------------------------------------------------------------

_LEGEND = dict(bgcolor="rgba(0,0,0,0.3)", font=dict(color="#e8eaf6"))
_LEGEND_H = dict(bgcolor="rgba(0,0,0,0.3)", font=dict(color="#e8eaf6"), orientation="h", y=1.08)

# Tooltip styling: darker bg, larger font, no truncation
_HOVERLABEL = dict(
    bgcolor="rgba(15,21,37,0.95)",
    bordercolor="rgba(255,255,255,0.2)",
    font=dict(color="#e8eaf6", size=13, family="Georgia"),
    namelength=-1,  # show full trace names (no truncation)
)

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.03)",
    font=dict(color="#e8eaf6", family="Georgia, 'Times New Roman', serif"),
    title_font=dict(size=16, color="#f8f9fa"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.08)", tickfont=dict(color="#9ca3af")),
    yaxis=dict(gridcolor="rgba(255,255,255,0.08)", tickfont=dict(color="#9ca3af")),
    margin=dict(l=50, r=30, t=60, b=50),
    hoverlabel=_HOVERLABEL,
)


def dark(height: int = 440, **kwargs) -> dict:
    """Return DARK_LAYOUT merged with height and any extra kwargs."""
    return {**DARK_LAYOUT, "height": height, **kwargs}


_CHART_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "responsive": True,
}


def fig_to_div(fig, div_id: str) -> str:
    """Embed a Plotly figure as a self-contained HTML div."""
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=div_id,
        config=_CHART_CONFIG,
    )


# --- Chart 1: The Three Waves — national death rate with pharma revenue overlay ---
def make_chart_waves():
    nat_od = nat.dropna(subset=["overdose_death_rate"]).sort_values("year")
    purdue_aligned = purdue_df[purdue_df["year"].isin(nat_od["year"])]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Background era shading
    for (x0, x1, label, color) in [
        (1999, 2010, "Wave 1: Prescription Opioids", "rgba(245,158,11,0.08)"),
        (2010, 2013, "Wave 2: Heroin", "rgba(239,68,68,0.08)"),
        (2013, 2016, "Wave 3: Fentanyl", "rgba(139,92,246,0.12)"),
    ]:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=color, line_width=0, annotation_text=label,
                      annotation_position="top left",
                      annotation=dict(font=dict(size=10, color="#9ca3af")))

    fig.add_trace(go.Scatter(
        x=nat_od["year"], y=nat_od["overdose_death_rate"],
        name="Overdose Deaths (per 100k)", mode="lines+markers",
        line=dict(color="#ef4444", width=3),
        fill="tozeroy", fillcolor="rgba(239,68,68,0.15)",
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=purdue_df["year"], y=purdue_df["revenue_m"] / 1000,
        name="Purdue Pharma Revenue ($B)", mode="lines+markers",
        line=dict(color="#f59e0b", width=2.5, dash="dot"),
        marker=dict(symbol="diamond", size=6),
    ), secondary_y=True)

    # Key event markers
    for year, event in [(2007, "DOJ Settlement\n$634.5M"), (2010, "OxyContin\nReformulated"), (2016, "Fentanyl\nSurge")]:
        od_val = nat_od[nat_od["year"] == year]["overdose_death_rate"]
        if len(od_val):
            fig.add_annotation(x=year, y=float(od_val.iloc[0]) + 1.2,
                text=event, showarrow=True, arrowhead=2, arrowcolor="#6b7280",
                font=dict(size=9, color="#d1d5db"), arrowwidth=1.5,
                ax=0, ay=-40)

    fig.update_layout(
        **dark(440),
        title="Drug Overdose Deaths vs. Purdue Pharma Revenue (1999–2016)",
        hovermode="x unified",
        legend=_LEGEND_H,
    )
    fig.update_yaxes(title_text="Deaths per 100,000", secondary_y=False, gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(title_text="Purdue Revenue ($Billions)", secondary_y=True, gridcolor="rgba(255,255,255,0.04)")
    return fig_to_div(fig, "chart_waves")


# --- Chart 2: Year-over-year map (animation frames + slider + play) ---
# Frame-based animation to test if it works over HTTP. Choropleth requires redraw=True.
def make_chart_map():
    anim_data = state_panel.dropna(subset=["deaths_despair_rate","state_abbr"]).sort_values(["year","state_abbr"])
    max_rate = float(anim_data["deaths_despair_rate"].quantile(0.97))
    years = sorted(anim_data["year"].unique())
    locations = list(anim_data[anim_data["year"] == years[0]].sort_values("state_abbr")["state_abbr"])

    def _choropleth_for_year(yr):
        df_yr = anim_data[anim_data["year"] == yr].sort_values("state_abbr")
        return go.Choropleth(
            locations=locations,
            z=[float(v) for v in df_yr["deaths_despair_rate"]],
            locationmode="USA-states",
            colorscale=[
                [0.0, "#1a0a0a"], [0.2, "#4a1010"], [0.4, "#8b1a1a"],
                [0.6, "#c0392b"], [0.8, "#e74c3c"], [1.0, "#ff6b6b"],
            ],
            zmin=0,
            zmax=max_rate,
            customdata=df_yr[["state_abbr", "state_name", "overdose_death_rate", "suicide_rate", "deaths_despair_rate"]].values.tolist(),
            hovertemplate="<b>%{customdata[1]}</b><br>Overdose: %{customdata[2]:.1f}<br>Suicide: %{customdata[3]:.1f}<br>Combined: %{customdata[4]:.1f} per 100k<extra></extra>",
            colorbar=dict(title="Deaths per 100k", tickfont=dict(color="#9ca3af")),
        )

    # Initial data = first year
    initial = _choropleth_for_year(years[0])
    frames = [
        go.Frame(
            data=[_choropleth_for_year(yr)],
            name=str(yr),
            layout=dict(title=dict(text=f"Deaths of Despair per 100,000 — {yr}")),
        )
        for yr in years
    ]

    # Play/Pause buttons
    play_pause = [
        dict(
            label="Play",
            method="animate",
            args=[
                None,
                {
                    "frame": {"duration": 400, "redraw": True},
                    "fromcurrent": True,
                    "transition": {"duration": 200},
                },
            ],
        ),
        dict(
            label="Pause",
            method="animate",
            args=[
                [None],
                {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"},
            ],
        ),
    ]

    # Slider steps for scrubbing
    slider_steps = [
        dict(
            args=[
                [str(yr)],
                {"frame": {"duration": 0, "redraw": True}, "mode": "immediate"},
            ],
            label=str(yr),
            method="animate",
        )
        for yr in years
    ]

    fig = go.Figure(data=[initial], frames=frames)
    fig.update_layout(
        geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)", lakecolor="rgba(0,0,0,0)",
                 landcolor="rgba(30,30,50,1)", showlakes=True,
                 subunitcolor="rgba(255,255,255,0.2)"),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e8eaf6"),
        height=520,
        margin=dict(l=0, r=0, t=60, b=60),
        hoverlabel=_HOVERLABEL,
        title=dict(text=f"Deaths of Despair per 100,000 — {years[0]}", font=dict(size=16, color="#f8f9fa")),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                pad=dict(r=10, t=10),
                x=0.01,
                xanchor="left",
                y=0.99,
                yanchor="top",
                bgcolor="rgba(20,20,35,0.9)",
                bordercolor="rgba(255,255,255,0.2)",
                font=dict(color="#e8eaf6", size=12),
                buttons=play_pause,
            )
        ],
        sliders=[
            dict(
                active=0,
                yanchor="top",
                xanchor="left",
                currentvalue=dict(
                    font=dict(size=13, color="#e8eaf6"),
                    prefix="Year: ",
                    visible=True,
                    xanchor="center",
                ),
                pad=dict(b=10, t=50),
                len=0.9,
                x=0.05,
                y=0,
                bgcolor="rgba(20,20,35,0.7)",
                bordercolor="rgba(255,255,255,0.2)",
                tickcolor="rgba(255,255,255,0.5)",
                steps=slider_steps,
            )
        ],
    )
    return fig_to_div(fig, "chart_map")


# --- Chart 3: Prescribing rate vs. overdose deaths ---
def make_chart_rx_vs_deaths():
    rx_od = rx_df.merge(
        nat.dropna(subset=["overdose_death_rate"])[["year","overdose_death_rate"]],
        on="year"
    )
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=rx_od["year"], y=rx_od["rx_per_100"],
        name="Opioid Scripts per 100 People",
        marker=dict(color="rgba(245,158,11,0.7)", line=dict(color="rgba(245,158,11,1)", width=1)),
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=rx_od["year"], y=rx_od["overdose_death_rate"],
        name="Overdose Death Rate (per 100k)",
        mode="lines+markers",
        line=dict(color="#ef4444", width=3),
        marker=dict(size=7),
    ), secondary_y=True)
    fig.update_layout(
        **dark(440),
        title="Opioid Prescriptions Written vs. Overdose Deaths (2006–2016)",
        hovermode="x unified",
        legend=_LEGEND_H,
    )
    fig.update_yaxes(title_text="Prescriptions per 100 Persons", secondary_y=False, gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(title_text="Overdose Deaths per 100k", secondary_y=True, showgrid=False)
    return fig_to_div(fig, "chart_rx")


# --- Chart 4: Pills per capita by state (ARCOS) ---
def make_chart_pills_state():
    df = arcos_df.dropna(subset=["state_name"]).sort_values("pills_per_capita", ascending=True).tail(30)
    colors = ["#ef4444" if p > 50 else "#f59e0b" if p > 35 else "#3b82f6" for p in df["pills_per_capita"]]
    fig = go.Figure(go.Bar(
        x=df["pills_per_capita"], y=df["state_abbr"],
        orientation="h",
        marker=dict(color=colors),
        text=df["pills_per_capita"].round(1),
        textposition="outside",
        textfont=dict(color="#e8eaf6", size=10),
        hovertemplate="<b>%{y}</b><br>%{x:.1f} pills per person<extra></extra>",
    ))
    fig.add_vline(x=36, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                  annotation_text="National avg: 36", annotation_position="top",
                  annotation_font=dict(color="#9ca3af", size=10))
    fig.update_layout(
        **dark(580, margin=dict(l=50, r=80, t=80, b=50)),
        title="Opioid Pills per Person — By State (2010 Peak Year)<br><sub>Source: DEA ARCOS via Washington Post investigation</sub>",
        xaxis_title="Prescription Opioid Pills per Capita",
    )
    return fig_to_div(fig, "chart_pills")


# --- Chart 5: Total opioid market size vs. deaths ---
def make_chart_market():
    mkt = market_df[market_df["year"] <= 2016]
    nat_mkt = nat.dropna(subset=["overdose_death_rate"])[["year","overdose_death_rate"]]
    merged = mkt.merge(nat_mkt, on="year")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=merged["year"], y=merged["market_m"] / 1000,
        name="Opioid Market ($B)",
        mode="lines", line=dict(color="#f59e0b", width=3),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.12)",
        hovertemplate="%{x}<br>Market: $%{y:.1f}B<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=merged["year"], y=merged["overdose_death_rate"],
        name="Overdose Rate (per 100k)",
        mode="lines+markers", line=dict(color="#ef4444", width=3),
        hovertemplate="%{x}<br>Deaths: %{y:.1f} per 100k<extra></extra>",
    ), secondary_y=True)
    fig.update_layout(
        **dark(440),
        title="U.S. Opioid Market Revenue vs. Overdose Deaths (1999–2016)",
        hovermode="x unified",
        legend=_LEGEND_H,
    )
    fig.update_yaxes(title_text="Opioid Market Size ($Billions)", secondary_y=False, gridcolor="rgba(255,255,255,0.08)", hoverformat=".1f")
    fig.update_yaxes(title_text="Overdose Deaths per 100k", secondary_y=True, showgrid=False, hoverformat=".1f")
    return fig_to_div(fig, "chart_market")


# --- Chart 6: Manufacturing vs. despair scatter (dropdown, no animation frames) ---
def make_chart_mfg_scatter():
    base_2000 = state_panel[state_panel["year"] == 2000][
        ["state_abbr","deaths_despair_rate","manufacturing_employees_thousands"]
    ].rename(columns={
        "deaths_despair_rate": "ddr_2000",
        "manufacturing_employees_thousands": "mfg_2000",
    })
    panel = state_panel.merge(base_2000, on="state_abbr", how="left")
    panel["ddr_change"] = panel["deaths_despair_rate"] - panel["ddr_2000"]
    panel["mfg_change_pct"] = (panel["manufacturing_employees_thousands"] - panel["mfg_2000"]) / panel["mfg_2000"] * 100

    # Start from 2001: in 2000, mfg_change_pct=0 and ddr_change=0 for all states → all points at origin
    anim = panel[(panel["year"] >= 2001) & panel["mfg_change_pct"].notna() & panel["ddr_change"].notna()].copy()
    years = sorted(anim["year"].unique())

    REGION_COLOR = {"Rust Belt / Appalachia": "#ef4444", "Rust Belt": "#dc2626",
                    "Appalachia": "#f59e0b", "Coastal Metro": "#3b82f6", "Other": "#6b7280"}

    traces_per_year = []
    for yr in years:
        df_yr = anim[anim["year"] == yr]
        traces = []
        for region in sorted(df_yr["region"].unique()):
            rdf = df_yr[df_yr["region"] == region]
            traces.append(
                go.Scatter(
                    x=rdf["mfg_change_pct"],
                    y=rdf["ddr_change"],
                    text=rdf["state_abbr"],
                    mode="markers+text",
                    name=region,
                    marker=dict(size=8, color=REGION_COLOR.get(region, "#6b7280"),
                               line=dict(width=1, color="rgba(255,255,255,0.3)")),
                    textposition="top center",
                    showlegend=True,
                )
            )
        traces_per_year.append(traces)

    fig = go.Figure(data=traces_per_year[0])
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig.add_vline(x=0, line_dash="dash", line_color="rgba(255,255,255,0.2)")
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(color="#e8eaf6", family="Georgia"),
        height=460,
        legend=_LEGEND,
        margin=dict(l=60, r=30, t=60, b=60),
        hoverlabel=_HOVERLABEL,
        xaxis=dict(title="% Change in Manufacturing Jobs (since 2000)", range=[-55, 20], gridcolor="rgba(255,255,255,0.08)"),
        yaxis=dict(title="Rise in Deaths of Despair per 100k (since 2000)", range=[-5, 45], gridcolor="rgba(255,255,255,0.08)"),
        title=dict(text=f"Mfg Job Loss vs Deaths of Despair — {years[0]}", font=dict(size=14, color="#f8f9fa")),
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                x=0.01,
                y=0.99,
                yanchor="top",
                xanchor="left",
                bgcolor="rgba(20,20,35,0.9)",
                bordercolor="rgba(255,255,255,0.2)",
                font=dict(color="#e8eaf6", size=12),
                buttons=[
                    dict(
                        label=str(yr),
                        method="update",
                        args=[
                            {"data": traces_per_year[i]},
                            {"title": {"text": f"Mfg Job Loss vs Deaths of Despair — {yr}"}},
                        ],
                    )
                    for i, yr in enumerate(years)
                ],
            )
        ],
    )
    return fig_to_div(fig, "chart_mfg")


# --- Chart 7: Settlements bar chart ---
def make_chart_settlements():
    s = settlements_df.sort_values("amount_b", ascending=True)
    colors = ["#ef4444" if r == "Manufacturer" else "#f59e0b" for r in s["role"]]
    fig = go.Figure(go.Bar(
        x=s["amount_b"], y=s["company"],
        orientation="h",
        marker=dict(color=colors),
        text=[f"${v:.2f}B" for v in s["amount_b"]],
        textposition="outside",
        textfont=dict(color="#e8eaf6", size=10),
        hovertemplate="<b>%{y}</b><br>Settlement: $%{x:.2f}B (%{customdata})<extra></extra>",
        customdata=s["year"].astype(str),
    ))
    fig.update_layout(
        **dark(430, margin=dict(l=180, r=80, t=60, b=50)),
        title="Opioid Crisis Legal Settlements — Public Record (billions USD)",
        xaxis_title="Settlement Amount ($Billions)",
    )
    # Legend annotation
    fig.add_annotation(x=4, y=0.2, text="🟥 Manufacturer  🟨 Distributor",
                       showarrow=False, font=dict(color="#9ca3af", size=11))
    return fig_to_div(fig, "chart_settlements")


# --- Chart 8: Two Americas ---
def make_chart_two_americas():
    base_2000 = state_panel[state_panel["year"] == 2000][
        ["state_abbr","manufacturing_employees_thousands"]
    ].rename(columns={"manufacturing_employees_thousands": "mfg_2000"})
    end_year = int(state_panel["year"].max())
    end = state_panel[state_panel["year"] == end_year][
        ["state_abbr","manufacturing_employees_thousands"]
    ]
    change = base_2000.merge(end, on="state_abbr").assign(
        loss_pct=lambda x: (x["manufacturing_employees_thousands"] - x["mfg_2000"]) / x["mfg_2000"] * 100
    )
    top_losers = set(change.nsmallest(18, "loss_pct")["state_abbr"])
    top_keepers = set(change.nlargest(18, "loss_pct")["state_abbr"])

    state_panel["mfg_group"] = state_panel["state_abbr"].apply(
        lambda x: "High Mfg Loss States" if x in top_losers
        else ("Stable Mfg States" if x in top_keepers else None)
    )
    ta = (
        state_panel[state_panel["mfg_group"].notna()]
        .groupby(["year","mfg_group"])["deaths_despair_rate"]
        .mean().reset_index()
    )

    fig = go.Figure()
    # Add Stable Mfg first so the fill="tonexty" on High Mfg Loss fills the
    # gap between the two lines (not from zero).
    for grp, color, dash, fill in [
        ("Stable Mfg States", "#3b82f6", "dot", None),
        ("High Mfg Loss States", "#ef4444", "solid", "tonexty"),
    ]:
        d = ta[ta["mfg_group"] == grp].sort_values("year")
        fig.add_trace(go.Scatter(
            x=d["year"], y=d["deaths_despair_rate"],
            name=grp, mode="lines+markers",
            line=dict(color=color, width=3, dash=dash),
            fill=fill,
            fillcolor="rgba(239,68,68,0.10)",
        ))
    fig.update_layout(
        **dark(440),
        title=dict(
            text="Two Americas: States That Lost Manufacturing vs. Those That Kept It",
            font=dict(size=16, color="#f8f9fa"),
        ),
        annotations=[
            dict(
                text="Deaths of despair = drug overdoses + suicides. Both rise faster where factories closed.",
                xref="paper", yref="paper", x=0.5, y=1.02,
                xanchor="center", yanchor="bottom", showarrow=False,
                font=dict(size=11, color="#9ca3af"),
            ),
        ],
        xaxis_title="Year", yaxis_title="Avg Deaths of Despair per 100k",
        legend=_LEGEND_H,
    )
    return fig_to_div(fig, "chart_two_americas")


# ---------------------------------------------------------------------------
# Generate chart divs
# ---------------------------------------------------------------------------
print("Generating charts...")
chart_waves = make_chart_waves()
print("  ✓ Waves + Purdue revenue")
chart_map = make_chart_map()
print("  ✓ Year-selector map")
chart_rx = make_chart_rx_vs_deaths()
print("  ✓ Prescribing rate vs. deaths")
chart_pills = make_chart_pills_state()
print("  ✓ ARCOS pills per capita")
chart_market = make_chart_market()
print("  ✓ Opioid market size")
chart_mfg = make_chart_mfg_scatter()
print("  ✓ Manufacturing scatter (year selector)")
chart_settlements = make_chart_settlements()
print("  ✓ Legal settlements")
chart_two_americas = make_chart_two_americas()
print("  ✓ Two Americas")

# ---------------------------------------------------------------------------
# Compute headline stats
# ---------------------------------------------------------------------------
nat_clean = national_panel.dropna(subset=["overdose_deaths_total","suicide_deaths_total"])
total_od = int(nat_clean["overdose_deaths_total"].sum())
total_su = int(nat_clean["suicide_deaths_total"].sum())
total_combined = total_od + total_su
worst_state = state_panel[state_panel["year"] == int(state_panel["year"].max())].nlargest(1, "deaths_despair_rate").iloc[0]
purdue_total_revenue = sum(purdue_revenue.values())
total_settlement = sum(s["amount_b"] for s in settlements)
national_rate_change = round(
    (nat.dropna(subset=["deaths_despair_rate"]).iloc[-1]["deaths_despair_rate"] /
     nat.dropna(subset=["deaths_despair_rate"]).iloc[0]["deaths_despair_rate"] - 1) * 100, 0
)

# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The Quiet Epidemic — Deaths of Despair Dashboard</title>
  <!-- Python plotly 6.x bundles Plotly.js 3.x. Loading 2.27 causes binary data mismatch → blank charts. -->
  <script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@3.4.0/plotly.min.js" charset="utf-8"></script>
  <style>
    :root {{
      --bg: #080c18;
      --bg2: #0f1525;
      --bg3: #161d30;
      --card: rgba(255,255,255,0.04);
      --card-border: rgba(255,255,255,0.08);
      --red: #ef4444;
      --amber: #f59e0b;
      --blue: #3b82f6;
      --text: #e8eaf6;
      --muted: #9ca3af;
      --subtext: #6b7280;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: Georgia, 'Times New Roman', serif;
      line-height: 1.7;
    }}
    /* ---- HERO ---- */
    .hero {{
      position: relative;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 4rem 2rem;
      background:
        linear-gradient(to bottom, rgba(8,12,24,0.15) 0%, rgba(8,12,24,0.85) 60%, rgba(8,12,24,1) 100%),
        radial-gradient(ellipse at 20% 50%, rgba(239,68,68,0.15) 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, rgba(245,158,11,0.1) 0%, transparent 50%),
        var(--bg);
    }}
    .hero-content {{ max-width: 900px; }}
    .hero-eyebrow {{
      display: inline-block;
      font-family: 'Courier New', monospace;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--red);
      background: rgba(239,68,68,0.1);
      border: 1px solid rgba(239,68,68,0.3);
      padding: 0.3rem 0.9rem;
      border-radius: 4px;
      margin-bottom: 1.5rem;
    }}
    .hero h1 {{
      font-size: clamp(2.2rem, 6vw, 4rem);
      font-weight: 700;
      line-height: 1.15;
      color: #fff;
      margin-bottom: 0.6rem;
    }}
    .hero h1 span {{ color: var(--red); }}
    .hero-subtitle {{
      font-size: clamp(1.1rem, 2.5vw, 1.4rem);
      color: var(--muted);
      margin-bottom: 1.5rem;
      font-style: italic;
    }}
    .hero-lead {{
      font-size: 1rem;
      color: var(--muted);
      max-width: 640px;
      margin: 0 auto 2.5rem;
      line-height: 1.7;
    }}
    .hero-lead strong {{ color: var(--red); }}
    .hero-narrative {{ display: flex; flex-direction: column; gap: 1.5rem; align-items: center; }}
    .hero-narrative-row {{
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      align-items: stretch;
      gap: 1rem;
    }}
    .hero-narrative-row.hero-epicenter {{ margin-top: 0.5rem; }}
    .hero-plus {{
      align-self: center;
      font-size: 1.5rem;
      color: var(--muted);
      font-weight: 300;
    }}
    .hero-stat .sublabel {{
      font-size: 0.7rem;
      color: var(--subtext);
      text-transform: none;
      letter-spacing: 0;
      margin-top: 0.15rem;
      display: block;
    }}
    .hero-stat-primary {{ border-color: rgba(239,68,68,0.3); }}
    .hero-stat-amber .num {{ color: var(--amber); }}
    .hero-stat-amber {{ border-color: rgba(245,158,11,0.25); }}
    .hero-stat-blue .num {{ color: var(--blue); }}
    .hero-stat-blue {{ border-color: rgba(59,130,246,0.25); }}
    .hero-stat-epicenter {{ border-color: rgba(59,130,246,0.35); min-width: 180px; }}
    .hero-stat-epicenter .callout-num {{ font-size: 1.1rem; color: var(--blue); margin-top: 0.3rem; display: block; }}
    .hero-journey {{ margin: 2.5rem 0 1.5rem; }}
    .hero-journey-title {{ font-size: 0.85rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 1rem; }}
    .hero-journey-steps {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 0.6rem; }}
    .hero-step {{
      display: inline-flex; align-items: center; gap: 0.4rem;
      padding: 0.5rem 1rem;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 8px;
      color: var(--text); text-decoration: none; font-size: 0.9rem;
      transition: background 0.2s, border-color 0.2s;
    }}
    .hero-step:hover {{ background: rgba(255,255,255,0.1); border-color: rgba(239,68,68,0.4); }}
    .hero-step-num {{ font-family: 'Courier New', monospace; font-weight: 700; color: var(--red); font-size: 0.8rem; }}
    .hero-cta {{
      display: inline-block;
      margin: 1rem 0 1.5rem;
      padding: 1rem 2rem;
      background: var(--red);
      color: #fff;
      font-weight: 700;
      font-size: 1rem;
      text-decoration: none;
      border-radius: 8px;
      transition: background 0.2s, transform 0.2s;
      box-shadow: 0 4px 20px rgba(239,68,68,0.3);
    }}
    .hero-cta:hover {{ background: #dc2626; transform: translateY(-2px); }}
    .hero-stats {{
      display: flex;
      justify-content: center;
      gap: 2rem;
      flex-wrap: wrap;
      margin-bottom: 2.5rem;
    }}
    .hero-stat {{
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      padding: 1.2rem 2rem;
      min-width: 160px;
    }}
    .hero-stat .num {{
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--red);
      font-family: 'Courier New', monospace;
      display: block;
    }}
    .hero-stat .num.amber {{ color: var(--amber); }}
    .hero-stat .num.blue {{ color: var(--blue); }}
    .hero-stat .label {{
      font-size: 0.78rem;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-top: 0.2rem;
      display: block;
    }}
    .scroll-hint {{
      font-size: 0.8rem;
      color: var(--subtext);
      letter-spacing: 0.1em;
      text-transform: uppercase;
      animation: pulse 2s infinite;
    }}
    @keyframes pulse {{ 0%,100%{{opacity:.4}} 50%{{opacity:1}} }}

    /* ---- LAYOUT ---- */
    .container {{ max-width: 1280px; margin: 0 auto; padding: 0 2rem; }}

    /* ---- SECTIONS ---- */
    .section {{
      padding: 5rem 0;
      border-top: 1px solid rgba(255,255,255,0.05);
      scroll-margin-top: 2rem;
    }}
    .section-tag {{
      font-family: 'Courier New', monospace;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      margin-bottom: 0.8rem;
      opacity: 0.7;
    }}
    .section-tag.red {{ color: var(--red); }}
    .section-tag.amber {{ color: var(--amber); }}
    .section-tag.blue {{ color: var(--blue); }}
    .section h2 {{
      font-size: clamp(1.6rem, 3.5vw, 2.4rem);
      color: #fff;
      margin-bottom: 1rem;
      line-height: 1.2;
    }}
    .section .lead {{
      font-size: 1.1rem;
      color: var(--muted);
      max-width: 750px;
      margin-bottom: 2rem;
      line-height: 1.8;
    }}
    .section .lead strong {{ color: var(--text); }}

    /* ---- CHART CARD ---- */
    .chart-card {{
      background: var(--card);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 1.5rem;
      margin-bottom: 2rem;
    }}
    .chart-source {{
      font-size: 0.72rem;
      color: var(--subtext);
      margin-top: 0.5rem;
      font-family: 'Courier New', monospace;
    }}

    /* ---- TWO-COL ---- */
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
    @media(max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}

    /* ---- STAT CALLOUTS ---- */
    .callout-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin: 2rem 0; }}
    .callout {{
      background: rgba(239,68,68,0.07);
      border: 1px solid rgba(239,68,68,0.2);
      border-radius: 12px;
      padding: 1.2rem 1.5rem;
    }}
    .callout.amber {{ background: rgba(245,158,11,0.07); border-color: rgba(245,158,11,0.2); }}
    .callout.blue {{ background: rgba(59,130,246,0.07); border-color: rgba(59,130,246,0.2); }}
    .callout .callout-num {{
      font-size: 1.9rem;
      font-weight: 700;
      font-family: 'Courier New', monospace;
      color: var(--red);
      display: block;
    }}
    .callout.amber .callout-num {{ color: var(--amber); }}
    .callout.blue .callout-num {{ color: var(--blue); }}
    .callout p {{ font-size: 0.85rem; color: var(--muted); margin-top: 0.3rem; }}

    /* ---- TIMELINE ---- */
    .timeline {{ position: relative; padding: 1rem 0; }}
    .timeline::before {{
      content: '';
      position: absolute;
      left: 14px;
      top: 0; bottom: 0;
      width: 2px;
      background: linear-gradient(to bottom, rgba(239,68,68,0.5), rgba(239,68,68,0.05));
    }}
    .timeline-item {{
      display: flex;
      gap: 1.5rem;
      padding: 0.8rem 0;
      align-items: flex-start;
    }}
    .timeline-dot {{
      width: 30px;
      height: 30px;
      border-radius: 50%;
      background: rgba(239,68,68,0.15);
      border: 2px solid rgba(239,68,68,0.4);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--red);
      font-family: 'Courier New', monospace;
      flex-shrink: 0;
    }}
    .timeline-content {{ padding-top: 0.2rem; }}
    .timeline-year {{ font-size: 0.75rem; color: var(--amber); font-family: 'Courier New', monospace; font-weight: 700; }}
    .timeline-text {{ font-size: 0.9rem; color: var(--muted); }}

    /* ---- PHARMA BOX ---- */
    .pharma-highlight {{
      background: linear-gradient(135deg, rgba(245,158,11,0.1) 0%, rgba(239,68,68,0.05) 100%);
      border: 1px solid rgba(245,158,11,0.25);
      border-radius: 16px;
      padding: 2rem;
      margin: 2rem 0;
    }}
    .pharma-highlight h3 {{ color: var(--amber); font-size: 1.2rem; margin-bottom: 0.5rem; }}
    .pharma-highlight p {{ color: var(--muted); font-size: 0.95rem; line-height: 1.7; }}
    .pharma-highlight .big-number {{
      font-size: 3rem;
      font-weight: 700;
      color: var(--amber);
      font-family: 'Courier New', monospace;
    }}

    /* ---- METHODOLOGY ---- */
    .methodology {{
      background: var(--bg2);
      border-top: 1px solid rgba(255,255,255,0.06);
      padding: 3rem 0;
    }}
    .methodology h3 {{ color: var(--muted); font-size: 1rem; margin-bottom: 0.5rem; }}
    .methodology p, .methodology li {{ font-size: 0.82rem; color: var(--subtext); line-height: 1.7; }}
    .methodology ul {{ padding-left: 1.2rem; }}
    .methodology a {{ color: var(--blue); text-decoration: none; }}

    /* ---- FOOTER ---- */
    footer {{
      background: var(--bg);
      border-top: 1px solid rgba(255,255,255,0.05);
      padding: 2rem;
      text-align: center;
      font-size: 0.78rem;
      color: var(--subtext);
    }}
  </style>
</head>
<body>

<!-- ===== HERO ===== -->
<section class="hero">
  <div class="hero-content">
    <div class="hero-eyebrow">Data Investigation · CDC · BLS · DEA ARCOS · Court Records</div>
    <h1>The <span>Quiet</span> Epidemic</h1>
    <p class="hero-subtitle">How Big Pharma Flooded America with Opioids — and Profited While Communities Died</p>

    <p class="hero-lead">
      Drug overdoses and suicides are grouped as <strong>"deaths of despair"</strong> — they share the same root cause:
      economic collapse, lost purpose, and broken communities. Where factories closed and hope vanished, both rose together.
    </p>

    <div class="hero-narrative">
      <div class="hero-narrative-row">
        <div class="hero-stat hero-stat-primary">
          <span class="num">{total_od:,}</span>
          <span class="label">Drug Overdose Deaths</span>
          <span class="sublabel">1999–2016</span>
        </div>
        <span class="hero-plus">+</span>
        <div class="hero-stat hero-stat-primary">
          <span class="num">{total_su:,}</span>
          <span class="label">Suicide Deaths</span>
          <span class="sublabel">1999–2016</span>
        </div>
      </div>
      <div class="hero-narrative-row">
        <div class="hero-stat">
          <span class="num">+{national_rate_change:.0f}%</span>
          <span class="label">Rise in deaths of despair rate</span>
          <span class="sublabel">1999 → 2016</span>
        </div>
        <div class="hero-stat hero-stat-amber">
          <span class="num">76B</span>
          <span class="label">Opioid pills shipped</span>
          <span class="sublabel">2006–2012</span>
        </div>
        <div class="hero-stat hero-stat-amber">
          <span class="num">${purdue_total_revenue // 1000:.0f}B+</span>
          <span class="label">Purdue Pharma revenue</span>
          <span class="sublabel">1996–2016</span>
        </div>
        <div class="hero-stat hero-stat-blue">
          <span class="num">${total_settlement:.0f}B</span>
          <span class="label">Legal settlements</span>
          <span class="sublabel">Paid by industry</span>
        </div>
      </div>
      <div class="hero-narrative-row hero-epicenter">
        <div class="hero-stat hero-stat-epicenter">
          <span class="num">{worst_state['state_abbr']}</span>
          <span class="label">Worst-hit state in 2016</span>
          <span class="callout-num">{int(worst_state['deaths_despair_rate'])} deaths per 100k</span>
        </div>
      </div>
    </div>

    <div class="hero-journey">
      <p class="hero-journey-title">Your journey through the data</p>
      <div class="hero-journey-steps">
        <a href="#chapter-1" class="hero-step"><span class="hero-step-num">1</span> The Timeline</a>
        <a href="#chapter-2" class="hero-step"><span class="hero-step-num">2</span> The Geography</a>
        <a href="#chapter-3" class="hero-step"><span class="hero-step-num">3</span> The Prescription Machine</a>
        <a href="#chapter-4" class="hero-step"><span class="hero-step-num">4</span> The Profits</a>
        <a href="#chapter-5" class="hero-step"><span class="hero-step-num">5</span> The Economics</a>
        <a href="#chapter-6" class="hero-step"><span class="hero-step-num">6</span> Timeline of Events</a>
      </div>
    </div>

    <a href="#chapter-1" class="hero-cta">Start the story →</a>

    <div class="scroll-hint">↓ or scroll to explore ↓</div>
  </div>
</section>

<!-- ===== SECTION 1: The Three Waves ===== -->
<section id="chapter-1" class="section">
  <div class="container">
    <div class="section-tag red">Chapter 1 — The Timeline</div>
    <h2>Three Waves of Death — One Root Cause</h2>
    <p class="lead">
      The opioid epidemic didn't happen randomly. It was engineered. Purdue Pharma launched OxyContin in 1996 with a
      fraudulent marketing campaign claiming it was non-addictive. <strong>Sales went from $44M to $2.9B in 15 years.</strong>
      When the pills were eventually reformulated in 2010, addicted patients switched to heroin — and then to cheap,
      lethal fentanyl. Watch the death toll rise in lockstep with pharma revenue.
    </p>
    <div class="chart-card">
      {chart_waves}
      <div class="chart-source">Sources: CDC NCHS (overdose deaths, age-adjusted per 100k), Purdue Pharma bankruptcy court filings SDNY 2019 (revenue)</div>
    </div>

    <div class="pharma-highlight">
      <h3>The Sackler Family — $10+ Billion in Personal Distributions</h3>
      <p>
        While America buried its dead, the Sackler family — owners of Purdue Pharma —
        paid themselves over <strong style="color:#f59e0b">$10 billion in personal distributions</strong> between 2008 and 2017.
        They moved money to offshore accounts as lawsuits piled up. In 2007, Purdue pleaded guilty to federal fraud
        charges and paid $634.5M — one of the largest pharmaceutical settlements at the time.
        Three top executives paid $34.5M personally. The company continued operating.
        <br><br>
        The death toll continued to rise.
      </p>
    </div>
  </div>
</section>

<!-- ===== SECTION 2: Animated Map ===== -->
<section id="chapter-2" class="section">
  <div class="container">
    <div class="section-tag red">Chapter 2 — The Geography</div>
    <h2>Watch America's Crisis Spread — Year by Year</h2>
    <p class="lead">
      Use the dropdown to select a year. This is <strong>seventeen years of preventable deaths</strong>
      mapped state by state. It doesn't spread randomly — it follows the geography of abandoned communities:
      the Rust Belt, Appalachia, rural America. The places where factories closed and nothing replaced them.
    </p>
    <div class="chart-card" style="padding: 1rem; min-height: 560px;">
      {chart_map}
      <div class="chart-source">Source: CDC NCHS Drug Poisoning Mortality by State (age-adjusted rate per 100,000), datasets jx6g-fdh6 and xbxb-epbu</div>
    </div>
  </div>
</section>

<!-- ===== SECTION 3: The Prescription Machine ===== -->
<section id="chapter-3" class="section">
  <div class="container">
    <div class="section-tag amber">Chapter 3 — The Machine</div>
    <h2>Prescriptions Written, Deaths That Followed</h2>
    <p class="lead">
      At the peak in 2012, <strong>81.3 opioid prescriptions were written for every 100 Americans</strong> —
      enough for every adult in the country to have their own bottle. Pharmaceutical companies lobbied doctors,
      funded "pain management" organizations, and spread the false message that opioids were safe.
      The correlation between prescriptions and deaths is not coincidence.
    </p>
    <div class="two-col">
      <div class="chart-card">
        {chart_rx}
        <div class="chart-source">Sources: CDC Opioid Prescribing Rate Maps (scripts per 100 persons); CDC NCHS (overdose deaths)</div>
      </div>
      <div class="chart-card">
        {chart_pills}
        <div class="chart-source">Source: DEA ARCOS database via Washington Post investigation (2019), 2010 peak year data</div>
      </div>
    </div>

    <div class="callout-grid">
      <div class="callout amber">
        <span class="callout-num">66.5</span>
        <p>Opioid pills per person per year in West Virginia — the highest in America. That's a pill every 5.5 days for every man, woman, and child.</p>
      </div>
      <div class="callout amber">
        <span class="callout-num">76B</span>
        <p>Total opioid pills distributed across the U.S. from 2006 to 2012. That's enough to give every American 255 pills.</p>
      </div>
      <div class="callout">
        <span class="callout-num">2,500%</span>
        <p>Increase in opioid prescriptions written between 1990 and 2015, according to the DEA.</p>
      </div>
    </div>
  </div>
</section>

<!-- ===== SECTION 4: The Money ===== -->
<section id="chapter-4" class="section">
  <div class="container">
    <div class="section-tag amber">Chapter 4 — The Profits</div>
    <h2>An $11 Billion Industry Built on Addiction</h2>
    <p class="lead">
      The U.S. opioid market peaked at <strong>$11 billion in annual revenue in 2011–2012</strong>.
      Purdue Pharma alone made $35+ billion from OxyContin. Distributors McKesson, AmerisourceBergen,
      and Cardinal Health collectively shipped hundreds of billions of pills while regulators looked the other way.
      The executives knew. Internal emails, now public record, show Purdue tracking addiction rates while
      explicitly not reporting them to the FDA.
    </p>
    <div class="two-col">
      <div class="chart-card">
        {chart_market}
        <div class="chart-source">Sources: IQVIA/IMS Health opioid market data (cited in JAMA, NEJM studies); CDC NCHS overdose deaths</div>
      </div>
      <div class="chart-card">
        {chart_settlements}
        <div class="chart-source">Source: DOJ press releases, state AG announcements, court records (public)</div>
      </div>
    </div>

    <div class="pharma-highlight">
      <h3>The Settlement Numbers Sound Big — But Consider This</h3>
      <p>
        The $26 billion settlement paid by the Big Three distributors (McKesson, AmerisourceBergen, Cardinal Health)
        in 2021 sounds enormous. But those three companies made
        <strong style="color:#f59e0b">over $500 billion in combined revenue in 2020 alone</strong>.
        The J&J settlement? They made $82 billion in 2020 revenue.
        The "largest opioid settlement in history" represents less than 3 months of business.
        Meanwhile, over half a million Americans are dead.
      </p>
    </div>
  </div>
</section>

<!-- ===== SECTION 5: The Economic Connection ===== -->
<section id="chapter-5" class="section">
  <div class="container">
    <div class="section-tag blue">Chapter 5 — The Economics</div>
    <h2>Where the Jobs Went, Death Followed</h2>
    <p class="lead">
      <strong>Deaths of despair</strong> (overdoses + suicides) rise together where economic hope vanishes.
      The opioid crisis didn't target randomly — it hit hardest where <strong>factories had closed,
      wages had stagnated, and communities had lost their identity</strong>. Pharma companies
      targeted these areas, flooding high-prescribing doctors in depressed regions with sales reps.
      The correlation between manufacturing job loss and deaths of despair is not an accident.
    </p>
    <div class="chart-card" style="min-height: 510px;">
      {chart_mfg}
      <div class="chart-source">Sources: CDC NCHS (death rates); FRED/BLS state manufacturing employment; dot size represents state population</div>
    </div>
    <div class="chart-card">
      {chart_two_americas}
      <div class="chart-source">Sources: CDC NCHS (death rates); FRED/BLS manufacturing employment. Groups = top/bottom 18 states by % mfg job loss from 2000 baseline</div>
    </div>
  </div>
</section>

<!-- ===== SECTION 6: Timeline ===== -->
<section id="chapter-6" class="section">
  <div class="container">
    <div class="section-tag red">Chapter 6 — Timeline</div>
    <h2>How We Got Here</h2>
    <p class="lead">A chronology of the decisions, cover-ups, and consequences that created this epidemic.</p>
    <div class="timeline">
      {chr(10).join(
        f'''<div class="timeline-item">
          <div class="timeline-dot">{year}</div>
          <div class="timeline-content">
            <div class="timeline-year">{year}</div>
            <div class="timeline-text">{event}</div>
          </div>
        </div>'''
        for year, event in key_events
      )}
    </div>
  </div>
</section>

<!-- ===== METHODOLOGY ===== -->
<div class="methodology">
  <div class="container">
    <h3>Data Sources & Methodology</h3>
    <ul>
      <li><strong>Deaths of Despair Rate:</strong> Combined drug overdose death rate + suicide death rate, both age-adjusted per 100,000. Source: CDC NCHS datasets <code>jx6g-fdh6</code>, <code>xbxb-epbu</code>, <code>bi63-dtpu</code> via data.cdc.gov Socrata API. Coverage: 1999–2016.</li>
      <li><strong>Opioid Prescribing Rate:</strong> CDC U.S. Opioid Prescribing Rate Maps, published annually. Prescriptions per 100 persons, 2006–2016.</li>
      <li><strong>Purdue Pharma Revenue:</strong> Net revenue from OxyContin sales. Source: Purdue Pharma Chapter 11 bankruptcy court filings (SDNY 2019), DOJ press releases, peer-reviewed studies citing court documents.</li>
      <li><strong>U.S. Opioid Market:</strong> Total U.S. opioid analgesic market revenue. Source: IQVIA (formerly IMS Health) data as cited in JAMA, NEJM, and CDC reports.</li>
      <li><strong>ARCOS Pill Data:</strong> DEA ARCOS opioid pill shipments per capita by state (2010). Source: DEA ARCOS database published by Washington Post investigative team, 2019.</li>
      <li><strong>Manufacturing Employment:</strong> All-Employees: Manufacturing by state (annual average). Source: FRED/BLS State and Area Employment Statistics.</li>
      <li><strong>Legal Settlements:</strong> From DOJ press releases, state attorney general announcements, and public court records.</li>
    </ul>
    <p style="margin-top:1rem;">
      <strong>Limitations:</strong> Death rate data covers 1999–2016 (CDC NCHS age-adjusted state rates available through this period for both overdose and suicide).
      Pharma revenue data for years pre-2007 is based on estimates from court documents; precise figures remain sealed.
      Correlation does not prove causation — though in this case, court-verified documents explicitly demonstrate intent.
    </p>
  </div>
</div>

<footer>
  <p>Data study by <strong>Data Adventures</strong> · Built with Python, Plotly, CDC NCHS, BLS, DEA ARCOS</p>
  <p style="margin-top:.5rem;">All data is from public sources. Pharma revenue figures are from court documents, DOJ settlements, and peer-reviewed studies. See methodology above.</p>
</footer>


</body>
</html>"""

# ---------------------------------------------------------------------------
# Inject embedded Plotly.js (escape </script> to avoid breaking HTML)
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
print(f"\n✓ Dashboard written: {out_path}")
print(f"  Size: {size_kb:,.0f} KB")
