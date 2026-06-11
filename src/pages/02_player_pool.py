"""02_player_pool.py — the scouting universe.

A filterable view of `pool_enriched.csv` (the Big-5, 2020-21 -> 2022-23 player
pool that survived the tiered minutes filter). Filters on role, league, age,
value band and tier; a toggle switches between the raw season-level rows and a
minutes-weighted per-player aggregate.

Non-negotiables honoured here:
  - reads ONLY via data_loader (no direct file opens), never writes;
  - no st.set_page_config (app.py owns it);
  - palette/roles come from visualizations (single source of truth).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

import data_loader as dl
import visualizations as viz

# Active theme (detect once; pass PAL into inline-HTML colors).
dark = dl.active_dark()
PAL = viz.palette(dark)

# --- Column universe ----------------------------------------------------------
# Per-90 / rate / count stat columns (everything we weight-average in aggregate
# mode). Names must match the FBref columns EXACTLY, including spaces and '+'.
STAT_COLS = [
    "G_minus_PK_Per", "npxG_Per", "xAG_Per", "Cmp_percent_Total", "CrsPA",
    "Final_Third", "KP", "Prog", "Blocks_Blocks", "Clr", "Err", "Int",
    "Mid 3rd_Tackles", "Tkl+Int", "TklW_Tackles", "Att Pen_Touches",
    "Final_Third_Carries", "Mis_Carries", "Prog_Carries", "Prog_Receiving",
    "Succ_Dribbles", "Recov", "Won_Aerial", "Won_percent_Aerial",
    "GCA90_GCA", "SCA90_SCA",
]
# The headline stats shown by default (rest available via the "all stats" toggle).
HEADLINE_STATS = [
    "npxG_Per", "xAG_Per", "SCA90_SCA", "Prog", "Tkl+Int", "Int",
    "Won_percent_Aerial", "Succ_Dribbles", "Prog_Carries",
]
# Pretty labels for the table header (column_config).
STAT_LABELS = {
    "G_minus_PK_Per": "npG/90", "npxG_Per": "npxG/90", "xAG_Per": "xAG/90",
    "Cmp_percent_Total": "Pass %", "CrsPA": "Crs→PA", "Final_Third": "Pass→F3",
    "KP": "Key passes", "Prog": "Prog passes", "Blocks_Blocks": "Blocks",
    "Clr": "Clearances", "Err": "Errors", "Int": "Interceptions",
    "Mid 3rd_Tackles": "Tkl (mid 3rd)", "Tkl+Int": "Tkl+Int",
    "TklW_Tackles": "Tkl won", "Att Pen_Touches": "Box touches",
    "Final_Third_Carries": "Carries→F3", "Mis_Carries": "Miscontrols",
    "Prog_Carries": "Prog carries", "Prog_Receiving": "Prog recv",
    "Succ_Dribbles": "Succ dribbles", "Recov": "Recoveries",
    "Won_Aerial": "Aerials won", "Won_percent_Aerial": "Aerial %",
    "GCA90_GCA": "GCA/90", "SCA90_SCA": "SCA/90",
}
PCT_FMT = {"Cmp_percent_Total", "Won_percent_Aerial"}  # one-decimal percentages


def _pretty_role(role: str) -> str:
    return str(role).replace("_", " ").title()


# --- Aggregation (in-page, minutes-weighted; no file writes) ------------------
@st.cache_data
def _aggregate(pool: pd.DataFrame) -> pd.DataFrame:
    """Collapse season rows to one row per player (Url).

    Stats are minutes-weighted means across the player's seasons (NaN-aware:
    a season missing a stat is dropped from that stat's weighting). Categorical
    and value fields are taken from the player's latest season; minutes are
    summed; age is the latest (max).
    """
    w = pool["Min_Playing"].fillna(0.0)
    latest = (pool.sort_values("Season_End_Year")
                  .groupby("Url", sort=False).tail(1)
                  .set_index("Url"))

    out = pd.DataFrame(index=latest.index)
    for col in ["Player", "role", "Comp", "Squad", "tier", "valM", "band"]:
        out[col] = latest[col]
    g = pool.groupby("Url", sort=False)
    out["Age"] = g["Age"].max()
    out["n_seasons"] = g["Season_End_Year"].nunique()
    out["total_min"] = g["Min_Playing"].sum()

    url = pool["Url"]
    for c in STAT_COLS:
        num = (pool[c] * w).groupby(url).sum(min_count=1)
        den = w.where(pool[c].notna()).groupby(url).sum(min_count=1)
        out[c] = num / den.replace(0, np.nan)
    return out.reset_index()


def _column_config(stat_cols, *, by_season: bool) -> dict:
    cfg = {
        "Player": st.column_config.TextColumn("Player", width="medium"),
        "role": st.column_config.TextColumn("Role"),
        "Comp": st.column_config.TextColumn("League"),
        "Squad": st.column_config.TextColumn("Club"),
        "tier": st.column_config.TextColumn("Tier", width="small"),
        "Age": st.column_config.NumberColumn("Age", format="%.0f", width="small"),
        "valM": st.column_config.NumberColumn("Value (€M)", format="%.1f"),
    }
    if by_season:
        cfg["Season_End_Year"] = st.column_config.NumberColumn("Season", format="%d")
        cfg["Min_Playing"] = st.column_config.NumberColumn("Minutes", format="%d")
    else:
        cfg["n_seasons"] = st.column_config.NumberColumn("Seasons", format="%d", width="small")
        cfg["total_min"] = st.column_config.NumberColumn("Minutes", format="%d")
    for c in stat_cols:
        label = STAT_LABELS.get(c, c)
        fmt = "%.1f" if c in PCT_FMT else "%.2f"
        cfg[c] = st.column_config.NumberColumn(label, format=fmt)
    return cfg


# ==============================================================================
st.title("Player Pool")
st.caption(
    "The scouting universe — every player-season that cleared the tiered minutes "
    "filter across the Big 5 European leagues, 2020-21 → 2022-23."
)

pool = dl.load_pool_enriched().copy()
pool["valM"] = pool["market_value_eur"] / 1e6
pool["band"] = pool["valM"].apply(dl.band_of)

# Role color legend (chips) — reuses the one ramp from visualizations.
chips = "".join(
    f"<span style='display:inline-block;margin:0 .5rem .35rem 0;padding:.1rem .55rem;"
    f"border-radius:6px;background:{viz.ROLE_COLORS[r]};color:#fff;font-size:.74rem;"
    f"font-weight:600'>{_pretty_role(r)}</span>"
    for r in viz.ROLE_ORDER
)
st.markdown(chips, unsafe_allow_html=True)

# --- Sidebar filters ----------------------------------------------------------
with st.sidebar:
    st.markdown("#### Filters")
    sel_roles = st.multiselect(
        "Role", viz.ROLE_ORDER, default=viz.ROLE_ORDER, format_func=_pretty_role,
    )
    leagues = sorted(pool["Comp"].dropna().unique())
    sel_leagues = st.multiselect("League", leagues, default=leagues)

    sel_tiers = st.multiselect(
        "Tier", ["A", "B", "C"], default=["A", "B", "C"],
        help="A = primary pool · B = emerging · C = youth watch.",
    )
    include_excluded = st.checkbox(
        "Include players outside the tiered pool", value=False,
        help="Adds players who did not clear the minutes filter (no tier).",
    )

    ages = pool["Age"].dropna()
    a_lo, a_hi = int(ages.min()), int(ages.max())
    sel_age = st.slider("Age", a_lo, a_hi, (a_lo, a_hi))

    sel_bands = st.multiselect(
        "Value band", ["marquee", "mid", "bargain", "unknown"],
        default=["marquee", "mid", "bargain", "unknown"],
        format_func=lambda b: {
            "marquee": "Marquee (≥ €80M)", "mid": "Mid (€30–80M)",
            "bargain": "Bargain (< €30M)", "unknown": "Unknown value",
        }[b],
    )

# --- Apply season-level filters -----------------------------------------------
mask = (
    pool["role"].isin(sel_roles)
    & pool["Comp"].isin(sel_leagues)
    & pool["Age"].between(sel_age[0], sel_age[1])
    & pool["band"].isin(sel_bands)
)
tier_ok = pool["tier"].isin(sel_tiers)
if include_excluded:
    tier_ok = tier_ok | pool["tier"].isna()
mask &= tier_ok
filtered = pool[mask].copy()

# --- View toggle --------------------------------------------------------------
left, right = st.columns([3, 2])
with left:
    view = st.radio(
        "View", ["By season", "Aggregate (per player)"],
        horizontal=True, label_visibility="collapsed",
    )
show_all = st.toggle("Show all stat columns", value=False)
by_season = view.startswith("By season")
stat_cols = STAT_COLS if show_all else HEADLINE_STATS

if by_season:
    table = filtered
    base_cols = ["Player", "role", "Comp", "Squad", "Season_End_Year",
                 "Age", "Min_Playing", "tier", "valM"]
    n_players = filtered["Url"].nunique()
    summary = f"**{len(table):,}** player-seasons · **{n_players:,}** unique players"
else:
    table = _aggregate(filtered) if len(filtered) else filtered.assign(n_seasons=0, total_min=0)
    base_cols = ["Player", "role", "Comp", "Age", "n_seasons",
                 "total_min", "tier", "valM"]
    summary = f"**{len(table):,}** players (minutes-weighted across their seasons)"

with right:
    st.markdown(
        f"<div style='text-align:right;padding-top:.35rem;color:{PAL['muted']}'>{summary}</div>",
        unsafe_allow_html=True,
    )

# --- Render -------------------------------------------------------------------
display_cols = base_cols + [c for c in stat_cols if c in table.columns]
sort_col = "valM" if "valM" in table.columns else display_cols[0]
table = table[display_cols].sort_values(sort_col, ascending=False, na_position="last")
table = table.assign(role=table["role"].map(_pretty_role))

st.dataframe(
    table,
    width="stretch",
    hide_index=True,
    height=560,
    column_config=_column_config(
        [c for c in stat_cols if c in display_cols], by_season=by_season),
)

st.caption(
    "Per-90 and rate stats shown as-is; aggregate view is minutes-weighted across "
    "a player's seasons. Defensive counts (tackles, clearances, blocks) are **not** "
    "possession-adjusted — players at low-block sides (e.g. Metz, Atalanta) are "
    "flattered on raw volume. Values are highest career market value, in €M."
)
