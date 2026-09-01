"""Visuals for CosmosGenie.

Mirrors the shape of the bushfire app's map_view.py so it slots into app.py the
same way:

    import sky_view
    sky_view.render_sky_hero(run_sql, CATALOG, SCHEMA)      # hero next to chat
    sky_view.render_result_visual(df, CATALOG, SCHEMA)      # auto-visual for a result
    st.markdown(sky_view.current_moon_svg(), unsafe_allow_html=True)  # sidebar locator

Space data is mostly non-geographic, so instead of a map the hero is an asteroid
close-approach chart. The one genuinely geographic case (eclipse city totality)
is handled inside render_result_visual.

Column names are DEFENSIVE: each function looks for a few likely names and
degrades gracefully if the schema differs. Adjust the *_CANDIDATES lists to
match your actual gold/silver columns.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

log = logging.getLogger("cosmos.sky")

RunSql = Callable[[str], list[list[Any]]]

# Likely column names, in priority order. First match wins.
DATE_CANDIDATES = ["close_approach_date", "approach_date", "event_date", "date"]
MISS_LD_CANDIDATES = ["miss_distance_lunar", "miss_distance_ld", "miss_lunar"]
DIAMETER_CANDIDATES = ["diameter_m", "diameter", "size_estimate_m", "size_estimate", "est_diameter_m"]
THREAT_CANDIDATES = ["threat_level", "threat", "hazard_level"]
NAME_CANDIDATES = ["object_name", "asteroid_name", "name", "designation"]
CITY_CANDIDATES = ["city", "location", "place"]
CLARITY_CANDIDATES = ["sky_clarity_pct", "clear_sky_pct", "clarity_pct", "sky_clarity"]
DURATION_CANDIDATES = ["totality_duration_s", "duration_minutes", "duration_s", "totality_s", "duration"]
LAT_CANDIDATES = ["lat", "latitude"]
LON_CANDIDATES = ["lon", "lng", "longitude"]
DAYS_CANDIDATES = ["days_until", "days_to", "days"]
LABEL_CANDIDATES = ["event", "event_name", "name", "title", "label"]

THREAT_COLORS = {
    "HIGH": "#ff6b6b", "EXTREME": "#ff3b3b", "WATCH": "#ff9500",
    "MODERATE": "#ff9500", "SAFE": "#6bcb77", "LOW": "#6bcb77",
}
LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
              font=dict(color="#c3d5f2"), margin=dict(l=10, r=10, t=30, b=10))


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _first(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    lowered = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lowered:
            return lowered[cand]
    return None


def _rows_to_df(rows: list[list[Any]], columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)


# --------------------------------------------------------------------------
# 1. Hero visual — upcoming observable events timeline
# --------------------------------------------------------------------------
def render_sky_hero(run_sql: RunSql, catalog: str, schema: str) -> Optional[dict]:
    """Timeline of upcoming observable astronomical events: oppositions, conjunctions, 
    meteor showers. Returns clicked event details if user clicks on a point.
    """
    sql = f"""
        SELECT event_date, event_type, primary_body, secondary_body, 
               description, visibility
        FROM {catalog}.{schema}.planetary_events
        WHERE event_date BETWEEN current_date() 
              AND date_add(current_date(), 365)
        ORDER BY event_date
        LIMIT 100
    """
    try:
        rows = run_sql(sql)
    except Exception:
        log.exception("events timeline query failed")
        rows = []

    if not rows:
        st.info("No upcoming observable events to display yet.")
        return None

    df = _rows_to_df(rows, ["event_date", "event_type", "primary_body", 
                            "secondary_body", "description", "visibility"])
    df["event_date"] = pd.to_datetime(df["event_date"])
    df["days_until"] = (df["event_date"] - pd.Timestamp.now()).dt.days
    df["label"] = df.apply(
        lambda r: f"{r['primary_body']} {r['event_type']}" 
                  if pd.isna(r['secondary_body']) or r['secondary_body'] == '' 
                  else f"{r['primary_body']}-{r['secondary_body']} {r['event_type']}", 
        axis=1
    )
    
    if df.empty:
        st.info("No upcoming events to plot.")
        return None

    # Color map for event types
    event_colors = {
        "Opposition": "#ff9d5c",
        "Conjunction": "#b19cd9", 
        "Meteor Shower": "#6bcb77",
        "Alignment": "#4facfe",
    }

    fig = px.scatter(
        df, x="event_date", y="event_type",
        color="event_type", color_discrete_map=event_colors,
        size="days_until", size_max=40,
        hover_data={"label": True, "days_until": True, "visibility": True, 
                    "event_date": True, "event_type": False},
        labels={"event_date": "", "event_type": ""},
    )
    
    # Add prominent Earth/space background
    fig.update_layout(
        height=380, 
        legend_title_text="Event Type",
        plot_bgcolor="#0B1426",  # Match Aurora theme background
        paper_bgcolor="#0B1426",
        images=[dict(
            source="https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=1600&q=85",
            xref="paper", yref="paper",
            x=0, y=1, sizex=1, sizey=1,
            sizing="stretch", opacity=0.28, layer="below"
        )],
        font=dict(color="#E2E8F0"),  # Aurora text color
        margin=dict(l=10, r=10, t=30, b=10)
    )
    fig.update_yaxes(gridcolor="rgba(100,149,237,.12)")
    
    # Capture click events
    clicked = st.plotly_chart(fig, use_container_width=True, 
                              on_select="rerun", selection_mode="points", key="events_chart")
    
    # Return clicked event details if available
    if clicked and clicked.get("selection") and clicked["selection"].get("points"):
        point_idx = clicked["selection"]["points"][0]["point_index"]
        event_row = df.iloc[point_idx]
        return {
            "event_type": event_row["event_type"],
            "label": event_row["label"],
            "date": event_row["event_date"].strftime("%B %d, %Y"),
            "description": event_row["description"],
            "visibility": event_row["visibility"],
            "days_until": int(event_row["days_until"])
        }
    return None


# --------------------------------------------------------------------------
# 2. Auto-visual for a Genie result
# --------------------------------------------------------------------------
def render_result_visual(df: pd.DataFrame, catalog: str = "", schema: str = "") -> bool:
    """Look at a result's columns and draw the most useful chart. Returns True
    if it drew one; app.py falls back to a table/bar when this returns False."""
    if df is None or df.empty:
        return False

    city = _first(df, CITY_CANDIDATES)
    clarity = _first(df, CLARITY_CANDIDATES)
    if city and clarity:
        return _eclipse_travel(df, city, clarity)

    date_col = _first(df, DATE_CANDIDATES)
    miss = _first(df, MISS_LD_CANDIDATES)
    if date_col and miss:
        return _asteroid_scatter(df, date_col, miss)

    days = _first(df, DAYS_CANDIDATES)
    label = _first(df, LABEL_CANDIDATES)
    if days and label and len(df) <= 30:
        return _event_timeline(df, days, label)

    return False


def _eclipse_travel(df: pd.DataFrame, city: str, clarity: str) -> bool:
    df = df.copy()
    df[clarity] = pd.to_numeric(df[clarity], errors="coerce")
    lat, lon = _first(df, LAT_CANDIDATES), _first(df, LON_CANDIDATES)
    dur = _first(df, DURATION_CANDIDATES)

    if lat and lon:  # true map when coordinates are present
        fig = px.scatter_geo(
            df, lat=lat, lon=lon, color=clarity, hover_name=city,
            size=dur if dur else None, color_continuous_scale="YlOrRd",
            projection="natural earth",
        )
        fig.update_geos(bgcolor="rgba(0,0,0,0)", landcolor="#141f38",
                        oceancolor="#0a1120", showocean=True, lakecolor="#0a1120",
                        coastlinecolor="#2c3444")
        fig.update_layout(height=420, **LAYOUT)
    else:  # no coords: rank cities by clear-sky odds
        d = df.sort_values(clarity, ascending=True)
        fig = px.bar(d, x=clarity, y=city, orientation="h",
                     color=clarity, color_continuous_scale="YlOrRd")
        fig.update_layout(height=max(240, 32 * len(d)), **LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Ranked by chance of clear skies. Always check totality duration before booking.")
    return True


def _asteroid_scatter(df: pd.DataFrame, date_col: str, miss: str) -> bool:
    df = df.copy()
    df[miss] = pd.to_numeric(df[miss], errors="coerce")
    df = df.dropna(subset=[miss])
    if df.empty:
        return False
    threat = _first(df, THREAT_CANDIDATES)
    name = _first(df, NAME_CANDIDATES)
    diameter = _first(df, DIAMETER_CANDIDATES)
    fig = px.scatter(
        df, x=date_col, y=miss,
        color=threat if threat else None, color_discrete_map=THREAT_COLORS,
        size=diameter if diameter else None, size_max=30,
        hover_name=name if name else None, log_y=True,
        labels={miss: "Miss distance (lunar distances)", date_col: ""},
    )
    fig.add_hline(y=1, line_dash="dash", line_color="#b19cd9",
                  annotation_text="Moon's orbit (1 LD)")
    fig.update_layout(height=340, legend_title_text="", **LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    return True


def _event_timeline(df: pd.DataFrame, days: str, label: str) -> bool:
    df = df.copy()
    df[days] = pd.to_numeric(df[days], errors="coerce")
    df = df.dropna(subset=[days]).sort_values(days)
    if df.empty:
        return False
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[days], y=df[label], mode="markers+text",
        marker=dict(size=12, color="#ff9d5c"),
        text=[f"{int(d)}d" for d in df[days]], textposition="middle right",
    ))
    for _, r in df.iterrows():  # stems
        fig.add_shape(type="line", x0=0, x1=r[days], y0=r[label], y1=r[label],
                      line=dict(color="rgba(100,149,237,.3)", width=2))
    fig.update_layout(height=max(240, 34 * len(df)),
                      xaxis_title="Days from now", **LAYOUT)
    st.plotly_chart(fig, use_container_width=True)
    return True


# --------------------------------------------------------------------------
# 3. Sidebar locator — tonight's moon phase
# --------------------------------------------------------------------------
def current_moon_svg(now: Optional[datetime] = None) -> str:
    """A small disc showing the current illuminated fraction. The space analog
    of the bushfire app's Australia locator."""
    now = now or datetime.now(timezone.utc)
    ref = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
    syn = 29.53058867
    age = ((now - ref).total_seconds() / 86400.0) % syn
    illum = round((1 - math.cos(2 * math.pi * age / syn)) / 2 * 100)
    waxing = age < syn / 2
    names = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
             "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
    name = names[int((age / syn) * 8) % 8]
    # simple shading: light side follows waxing/waning
    shade = "-16px 0" if waxing else "16px 0"
    return (
        f'<div style="text-align:center;margin:6px 0 10px;">'
        f'<div style="width:74px;height:74px;border-radius:50%;margin:0 auto;'
        f'background:radial-gradient(circle at 60% 40%,#e8e0c8,#c8b890 45%,#1a1a2e);'
        f'box-shadow:inset {shade} 0 rgba(6,13,28,.85),0 0 18px rgba(200,180,140,.2);"></div>'
        f'<div style="font-size:12px;font-weight:700;color:#d8c890;margin-top:6px;">{name}</div>'
        f'<div style="font-size:11px;color:#9a8a58;">{illum}% illuminated</div></div>'
    )
