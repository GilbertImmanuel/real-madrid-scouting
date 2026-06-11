"""
data_loader.py - single cached I/O layer for the Real Madrid scouting Streamlit app.

Every page imports from here; no page opens a file directly (project non-negotiable).
All reads are cached with @st.cache_data. Paths are anchored to the repo root via
pathlib so the app is Windows-safe and location-independent.

Layout assumed (this file lives in src/):

    repo_root/
        src/data_loader.py          <- here
        config/mourinho_weights.json
        data/transformed/*.csv
        data/outputs/*.csv
        assets/...
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

# --- Path constants (repo-root anchored; never hardcode separators) -----------
ROOT    = Path(__file__).resolve().parents[1]   # src/ -> repo root
DATA    = ROOT / "data"
TRANS   = DATA / "transformed"
OUTPUTS = DATA / "outputs"
CONFIG  = ROOT / "config"
ASSETS  = ROOT / "assets"

# --- Domain constants (from the schema; shared so pages stay consistent) ------
ROLES = [
    "center_back", "full_back", "defensive_mid",
    "central_mid", "wide_attacker", "striker",
]

GAP_ROLES = ["striker", "defensive_mid", "full_back"]

# Value bands operate on valM (EUR millions, from highest_market_value_in_eur).
# Stored as inclusive lower bounds; see band_of().
VALUE_BANDS = {"marquee": 80.0, "mid": 30.0, "bargain": 0.0}

# The 26 role-relative percentile columns - the radar axis universe.
PCT_COLS = [
    "pct__aerial_win_pct", "pct__aerials_won", "pct__interceptions",
    "pct__clearances", "pct__tackles_plus_int", "pct__blocks",
    "pct__pass_completion", "pct__progressive_passes", "pct__errors",
    "pct__tackles_won", "pct__crosses_into_pen_area", "pct__passes_into_final_3rd",
    "pct__progressive_carries", "pct__prog_passes_received", "pct__recoveries",
    "pct__tackles_mid_third", "pct__miscontrols", "pct__key_passes",
    "pct__expected_assists", "pct__shot_creating_actions", "pct__non_pen_xg",
    "pct__successful_dribbles", "pct__carries_into_final_3rd", "pct__non_pen_goals",
    "pct__goal_creating_actions", "pct__touches_in_box",
]

# Locked radar-axis mapping (the six heaviest-weighted metrics per role in
# mourinho_weights.json). Lifted out of 05_shortlist.py so pages 04 and 05 share
# ONE source of truth (per Chat C handoff). Prefix each with "pct__" to reach the
# percentile column. Page 05 may import this in place of its local copy; they match.
ROLE_RADAR_AXES = {
    "center_back":   ["aerial_win_pct", "interceptions", "clearances",
                      "tackles_plus_int", "pass_completion", "progressive_passes"],
    "full_back":     ["tackles_won", "interceptions", "crosses_into_pen_area",
                      "passes_into_final_3rd", "progressive_carries", "prog_passes_received"],
    "defensive_mid": ["tackles_plus_int", "interceptions", "recoveries",
                      "pass_completion", "tackles_mid_third", "progressive_passes"],
    "central_mid":   ["progressive_passes", "tackles_plus_int", "progressive_carries",
                      "passes_into_final_3rd", "key_passes", "expected_assists"],
    "wide_attacker": ["non_pen_xg", "expected_assists", "shot_creating_actions",
                      "successful_dribbles", "progressive_carries", "tackles_plus_int"],
    "striker":       ["non_pen_xg", "non_pen_goals", "aerial_win_pct",
                      "goal_creating_actions", "expected_assists", "touches_in_box"],
}


def pretty_label(col: str) -> str:
    """pct__non_pen_xg -> 'Non Pen Xg'. Matches the annotated-string convention."""
    return col.replace("pct__", "").replace("_", " ").title()


def band_of(valM) -> str:
    """Map a market value (EUR M) to its band. NaN/None -> 'unknown'."""
    if valM is None or pd.isna(valM):
        return "unknown"
    if valM >= VALUE_BANDS["marquee"]:
        return "marquee"
    if valM >= VALUE_BANDS["mid"]:
        return "mid"
    return "bargain"


# --- Runtime theme detection --------------------------------------------------
# Centralised here (data_loader already imports streamlit) so visualizations.py
# can stay streamlit-free: pages call active_dark() and pass the resulting bool
# down into viz.palette()/viz.* chart calls.
#
# NOT cached: the active theme is a per-session/per-run signal, so it must be
# re-read on every script run (never @st.cache_data).
def active_dark() -> bool:
    """True if the user's active Streamlit theme is dark, else False.

    Reads ``st.context.theme.type`` (``"light"``/``"dark"``; available on
    Streamlit >= 1.46). Defaults to False (light) on anything unexpected -- the
    attribute can be missing under AppTest, and the value can be briefly wrong
    on the very first run of a session with a custom theme, which a one-rerun
    correction resolves. Light is the safe fallback either way.
    """
    try:
        return st.context.theme.type == "dark"
    except Exception:
        return False


# --- Internal read helper -----------------------------------------------------
def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Expected data file not found: {path}\n"
            "Run the pipeline first (bootstrap_data.py -> NB1 -> NB2 -> "
            "`python src/scoring.py` -> NB3) so the CSVs exist on disk."
        )
    return pd.read_csv(path)


# --- Cached loaders (the public contract; do not rename without a handoff) ----
@st.cache_data
def load_pool_enriched() -> pd.DataFrame:
    """transformed/pool_enriched.csv - 7,222 season-level rows (multiple per player)."""
    return _read_csv(TRANS / "pool_enriched.csv")


@st.cache_data
def load_scored_pool() -> pd.DataFrame:
    """transformed/scored_pool.csv - 641 player-level rows; pct__ + mourinho_score, no value."""
    return _read_csv(TRANS / "scored_pool.csv")


@st.cache_data
def load_squad_profile() -> pd.DataFrame:
    """transformed/madrid_squad_profile.csv - 36 current-squad rows (name/sub_position/role/age/valM)."""
    return _read_csv(TRANS / "madrid_squad_profile.csv")


@st.cache_data
def load_shortlist_final() -> pd.DataFrame:
    """outputs/shortlist_final.csv - 9 rows, the band x area grid."""
    return _read_csv(OUTPUTS / "shortlist_final.csv")


@st.cache_data
def load_shortlist_annotated() -> pd.DataFrame:
    """outputs/shortlist_annotated.csv - 9 rows with strengths/weaknesses/rationale strings."""
    return _read_csv(OUTPUTS / "shortlist_annotated.csv")


@st.cache_data
def load_board_full() -> pd.DataFrame:
    """outputs/shortlist_board_full.csv - 95 rows, full ranked gap-role board (radar source)."""
    return _read_csv(OUTPUTS / "shortlist_board_full.csv")


@st.cache_data
def load_youth() -> pd.DataFrame:
    """outputs/youth_watchlist.csv - 19 Tier-C prospect rows."""
    return _read_csv(OUTPUTS / "youth_watchlist.csv")


@st.cache_data
def load_weights() -> dict:
    """config/mourinho_weights.json - the hand-authored Mourinho archetype."""
    path = CONFIG / "mourinho_weights.json"
    if not path.exists():
        raise FileNotFoundError(f"Mourinho weights not found: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)
