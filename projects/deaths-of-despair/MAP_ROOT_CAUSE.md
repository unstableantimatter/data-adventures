# Choropleth Map Root Cause Analysis

## Summary

The deaths-of-despair choropleth heat map can fail for **two distinct reasons**:

1. **Dropdown `method="update"` with partial trace data** — risky merge behavior
2. **file:// + CDN fetch** — choropleth may need to fetch US state shapes from a CDN

---

## 1. Dropdown `method="update"` with Partial Data

**Current implementation** (generate_dashboard.py ~305–308):

```python
method="update",
args=[
    {"data": [{"z": z_by_year[i], "customdata": customdata_by_year[i]}]},
    {"title": {"text": f"Deaths of Despair per 100,000 — {yr}"}},
],
```

**Behavior:** `method="update"` is passed:
- A **data** update: `{"data": [{"z": ..., "customdata": ...}]}` for trace 0
- A **layout** update: title change

Plotly is supposed to **merge** that object into trace 0, leaving `locations`, `locationmode`, `type`, etc. intact. In practice, different Plotly.js versions can treat partial trace updates differently (shallow merge vs replace), which can break or invalidate the choropleth trace when you change years.

**Evidence:** The initial trace in the HTML includes `locations`, `locationmode`, `z`, `type:"choropleth"`, etc., so the first render is correct. The dropdown buttons only send `z` and `customdata`; if those updates are applied incorrectly, trace 0 can become invalid and the map can disappear or fail to render after the first year change.

---

## 2. Choropleth and CDN Fetch

**Choropleth with `locationmode="USA-states"`** typically uses:
- Either built‑in geometries bundled in Plotly.js, or
- Fetches of GeoJSON/TopoJSON from a CDN (e.g. `https://cdn.plot.ly/usa.geojson`)

**Impact of `file://`:** Opening `dashboard.html` via `file://` can cause:
- CORS restrictions when fetching from external CDNs
- Mixed-content issues

If the USA state shapes are loaded from a CDN and that request fails, the choropleth will stay blank even though the trace data is valid.

---

## 3. Recommended Fix: Multiple Traces + Visibility Toggle

Use **one trace per year** and toggle visibility instead of updating a single trace. This:
- Avoids partial `update` merges entirely
- Matches the [official pattern for choropleth dropdowns](https://stackoverflow.com/questions/61750811/dropdown-menu-for-plotly-choropleth-map-plots)
- Keeps layout updates (e.g. title) in the same button

**Pattern:**

```python
# One choropleth trace per year
traces = []
visible_template = [False] * len(years)
buttons = []

for i, yr in enumerate(years):
    df_yr = anim_data[anim_data["year"] == yr].sort_values("state_abbr")
    visible = visible_template.copy()
    visible[i] = True
    traces.append(go.Choropleth(
        locations=locations, z=z_by_year[i], customdata=customdata_by_year[i],
        locationmode="USA-states", ..., visible=(i == 0)
    ))
    buttons.append(dict(
        label=str(yr),
        method="update",
        args=[
            {"visible": [v for j, v in enumerate(visible) for _ in (1,)],  # one per trace
             ...},
            {"title": {"text": f"Deaths of Despair per 100,000 — {yr}"}},
        ],
    ))
```

**Trade-off:** More traces → larger HTML, but behavior is predictable and consistent across Plotly versions.

---

## 4. Alternative: Switch to `method="restyle"`

If you want to keep a **single trace** and only change data:

```python
method="restyle",
args=[
    {"z": [z_by_year[i]], "customdata": [customdata_by_year[i]]},
    [0],  # trace index
],
```

- **Restyle** updates only trace attributes (`z`, `customdata`), which avoids the partial trace merge issues with `update`.
- **Limitation:** A restyle-only button does not update the layout, so the title would not change when the user selects a different year.

---

## 5. Verifying file:// vs. HTTP

To test whether CDN loading is the problem:

1. Open the dashboard via `file://` and check:
   - Network tab for failed requests (e.g. to `cdn.plot.ly`)
   - Console for CORS or mixed-content errors
2. Serve the same file over HTTP (e.g. `python -m http.server`) and open the same dashboard. If the map appears over HTTP but not over `file://`, CDN loading under `file://` is likely the cause.
