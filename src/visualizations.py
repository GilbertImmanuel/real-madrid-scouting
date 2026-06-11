"""
visualizations.py - one shared Matplotlib house style + the figures every page reuses.

House style: royal-blue primary, gold accent, hairline gridlines. No default-
matplotlib colors, no rainbow palettes. The 6 roles are colored from a single
blue->gold ramp ordered defensive->attacking, so color encodes role position
(deep blue = center_back ... gold = striker) rather than decorating.

Adaptive theming (Chat E): the canvas/text/grid neutrals come from palette(dark)
so figures match the active Streamlit light/dark theme. The locked light PALETTE,
ROLE_COLORS, and BLUE_GOLD ramp are unchanged; dark only ADDS a neutral set. Gold
stays the sole accent in both modes. Figures render server-side as PNGs and can't
follow a client toggle on their own, so the caller passes dark=<bool> in.

All functions return plain Matplotlib Figures; pages render them with st.pyplot(fig).
This module deliberately does NOT import streamlit or the weights JSON - pages
detect the theme (data_loader.active_dark()), choose the radar axes, and pass both
the pct__ columns and dark=<bool> in explicitly (per the build contract).
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, to_hex

# --- Palette (mirrors .streamlit/config.toml; keep the two in sync) -----------
ROYAL_BLUE = "#00529F"   # primary
GOLD       = "#FEBE10"   # single accent
WHITE      = "#FFFFFF"   # canvas
SURFACE    = "#F4F6F9"   # panels
CHARCOAL   = "#1A1A1A"   # text
BORDER     = "#E3E8EF"   # hairline grid / spines
MUTED      = "#9AA7B8"   # secondary series + de-emphasised labels

PALETTE = {
    "primary": ROYAL_BLUE, "accent": GOLD, "background": WHITE,
    "surface": SURFACE, "text": CHARCOAL, "border": BORDER, "muted": MUTED,
}

# --- Dark palette (Chat E; ADDED, not a replacement) --------------------------
# Mirrors [theme.dark] in .streamlit/config.toml. Royal-blue identity preserved
# via a lightened primary (#4D8FD6) for contrast on the dark canvas; gold accent
# unchanged; muted grey reads on both canvases so it is shared.
DARK_PRIMARY    = "#4D8FD6"   # royal blue, lightened for dark contrast
DARK_BACKGROUND = "#0E1117"   # canvas
DARK_SURFACE    = "#1A1F2B"   # panels
DARK_TEXT       = "#E8ECF1"   # text
DARK_BORDER     = "#2A313D"   # hairline grid / spines

DARK = {
    "primary": DARK_PRIMARY, "accent": GOLD, "background": DARK_BACKGROUND,
    "surface": DARK_SURFACE, "text": DARK_TEXT, "border": DARK_BORDER, "muted": MUTED,
}


def palette(dark: bool = False) -> dict:
    """Return the active neutral+accent palette.

    Keys (identical in both modes so callers can swap transparently):
    primary, accent, background, surface, text, border, muted.
    Default dark=False returns the locked light PALETTE, so existing callers and
    `viz.PALETTE` references are unaffected.
    """
    return DARK if dark else PALETTE


# Blue -> gold sequential ramp: the one ordered/continuous color encoding in the app.
BLUE_GOLD = LinearSegmentedColormap.from_list(
    "blue_gold", [ROYAL_BLUE, "#5B8FC9", "#E9D27A", GOLD],
)

# Roles ordered defensive -> attacking so the ramp carries meaning.
ROLE_ORDER = [
    "center_back", "full_back", "defensive_mid",
    "central_mid", "wide_attacker", "striker",
]
ROLE_COLORS = {
    r: to_hex(BLUE_GOLD(i / (len(ROLE_ORDER) - 1)))
    for i, r in enumerate(ROLE_ORDER)
}


# --- Small helpers -------------------------------------------------------------
def _pretty_label(col: str) -> str:
    """pct__non_pen_xg -> 'Non Pen Xg' (mirrors data_loader.pretty_label)."""
    return col.replace("pct__", "").replace("_", " ").title()


def _pretty_role(role: str) -> str:
    return str(role).replace("_", " ").title()


def _strip_spines(ax, keep=("left", "bottom")) -> None:
    for side, spine in ax.spines.items():
        spine.set_visible(side in keep)


# Theme-AGNOSTIC chart ink. Matplotlib renders server-side as a PNG, and Streamlit
# does NOT rerun the script on a theme toggle (it only restyles chrome client-side),
# so a per-theme PNG can't follow the toggle. Instead the figures are drawn with a
# TRANSPARENT background (the themed page shows through, so the canvas always matches
# the active theme with zero rerun) and ink colors chosen to read on BOTH light and
# dark. Series colors (ROLE_COLORS, gold, the blue player line) already read on both.
NEUTRAL_INK  = "#6E7787"   # titles, axis labels, annotations, radar axis labels
NEUTRAL_TICK = MUTED       # ticks + radar ring numbers (low-emphasis, reads on both)
NEUTRAL_GRID = MUTED       # gridlines / spines (drawn at low alpha)
PLAYER_BLUE  = "#4D8FD6"   # radar player line: royal-blue family, reads on both themes


def apply_style(dark: bool = False) -> None:
    """Install the house style globally as Matplotlib rcParams.

    Figures are theme-AGNOSTIC: transparent canvas + neutral ink that reads on both
    light and dark. This is deliberate -- Streamlit doesn't rerun the script on a
    theme toggle, so a per-theme server-side PNG would get stuck on the old theme
    until the next rerun; a transparent + dual-legible figure always matches.

    `dark` is accepted for signature/back-compat (callers pass dark=<bool>) but no
    longer drives colors. Run once on import; chart fns call it before plt.subplots()."""
    mpl.rcParams.update({
        "figure.facecolor": "none",       # transparent: themed page shows through
        "axes.facecolor": "none",
        "savefig.facecolor": "none",
        "savefig.transparent": True,      # force transparent PNGs from st.pyplot
        "font.family": "sans-serif",
        # Match the app fonts where installed; graceful fallback otherwise.
        "font.sans-serif": ["Inter", "Montserrat", "Segoe UI", "Helvetica Neue",
                            "Arial", "DejaVu Sans", "sans-serif"],
        "text.color": NEUTRAL_INK,
        "axes.labelcolor": NEUTRAL_INK,
        "axes.edgecolor": NEUTRAL_GRID,
        "axes.titlecolor": NEUTRAL_INK,
        "axes.titleweight": "bold",
        "axes.titlesize": 13,
        "axes.labelsize": 10.5,
        "axes.linewidth": 1.0,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": NEUTRAL_GRID,
        "grid.linewidth": 0.8,
        "xtick.color": NEUTRAL_TICK,
        "ytick.color": NEUTRAL_TICK,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.frameon": False,
        "legend.fontsize": 9.5,
    })


apply_style()  # theme-agnostic; the dark= param is kept only for call-site compat


# --- Charts --------------------------------------------------------------------
def radar(values, metric_cols, labels=None, title="", compare=None, dark=False):
    """Polar radar of role-relative percentiles (0-100).

    values     : dict / pd.Series keyed by pct__ column name.
    metric_cols: list of pct__ columns to use as axes (the caller chooses).
    labels     : optional pretty axis labels (defaults to prettified metric_cols).
    title      : chart title.
    compare    : optional dict/Series (e.g. role median) drawn behind in muted grey.
    dark       : accepted for call-site compat; figure is theme-agnostic (see apply_style).

    Returns a Matplotlib Figure. NaN/missing values are treated as 0.
    """
    apply_style(dark)
    labels = labels or [_pretty_label(c) for c in metric_cols]
    n = len(metric_cols)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]  # close the loop

    def _closed(src):
        vals = [float(src[c]) if (c in src and pd.notna(src[c])) else 0.0
                for c in metric_cols]
        return vals + vals[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw={"projection": "polar"})
    fig.patch.set_alpha(0.0)            # transparent: themed page shows through
    ax.patch.set_alpha(0.0)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], color=NEUTRAL_TICK, size=8)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color=NEUTRAL_INK, size=9)
    ax.tick_params(pad=8)
    ax.spines["polar"].set_color(NEUTRAL_GRID)
    ax.spines["polar"].set_alpha(0.45)
    ax.grid(color=NEUTRAL_GRID, linewidth=0.8, alpha=0.45)

    if compare is not None:
        cvals = _closed(compare)
        ax.plot(angles, cvals, color=NEUTRAL_TICK, linewidth=1.3, linestyle="--",
                label="Role median")
        ax.fill(angles, cvals, color=NEUTRAL_TICK, alpha=0.10)

    vals = _closed(values)
    ax.plot(angles, vals, color=PLAYER_BLUE, linewidth=2.2, label="Player")
    ax.fill(angles, vals, color=PLAYER_BLUE, alpha=0.18)
    # Gold vertex dots: the single accent. No edge (transparent canvas, so no halo
    # to mask on either theme).
    ax.scatter(angles[:-1], vals[:-1], color=GOLD, s=22, zorder=5, edgecolors="none")

    if title:
        ax.set_title(title, pad=22, fontsize=13, fontweight="bold", color=NEUTRAL_INK)
    if compare is not None:
        ax.legend(loc="upper right", bbox_to_anchor=(1.18, 1.12))
    fig.tight_layout()
    return fig


def squad_depth_chart(squad_df, dark=False):
    """Bar chart of player count per role, annotated with each role's mean age.

    Expects columns: role, age. Roles are ordered defensive->attacking and
    colored from the blue->gold ramp (ROLE_COLORS, reads on both themes).
    dark accepted for call-site compat; figure is theme-agnostic. Returns a Figure.
    """
    apply_style(dark)
    grp = (squad_df.groupby("role")
           .agg(count=("role", "size"), mean_age=("age", "mean")))
    order = [r for r in ROLE_ORDER if r in grp.index]
    grp = grp.reindex(order)

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    colors = [ROLE_COLORS[r] for r in grp.index]
    ax.bar(range(len(grp)), grp["count"], color=colors, width=0.66,
           edgecolor="none", zorder=3)

    ax.set_xticks(range(len(grp)))
    ax.set_xticklabels([_pretty_role(r) for r in grp.index])
    ax.set_ylabel("Players")
    ax.set_ylim(0, float(grp["count"].max()) + 2)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color=NEUTRAL_GRID, linewidth=0.8, alpha=0.45)
    _strip_spines(ax)

    for i, (_, row) in enumerate(grp.iterrows()):
        top = float(row["count"])
        ax.text(i, top + 0.12, f"{int(top)}", ha="center", va="bottom",
                color=NEUTRAL_INK, fontsize=12, fontweight="bold")
        if pd.notna(row["mean_age"]):
            ax.text(i, top + 0.62, f"avg {row['mean_age']:.0f}y", ha="center",
                    va="bottom", color=NEUTRAL_TICK, fontsize=8.5)

    ax.set_title("Squad depth by role", loc="left", pad=12)
    fig.tight_layout()
    return fig


def age_value_scatter(squad_df, dark=False):
    """Scatter of age (x) vs market value valM (y), colored by role.

    Expects columns: age, valM, role. Rows with missing valM or age are dropped
    (academy players often have blank valM). dark accepted for call-site compat;
    figure is theme-agnostic (ROLE_COLORS read on both). Returns a Figure.
    """
    apply_style(dark)
    df = squad_df.dropna(subset=["valM", "age"]).copy()

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)
    for role in [r for r in ROLE_ORDER if r in df["role"].unique()]:
        sub = df[df["role"] == role]
        ax.scatter(sub["age"], sub["valM"], s=90, color=ROLE_COLORS[role],
                   edgecolors="none", alpha=0.9, zorder=3,
                   label=_pretty_role(role))

    ax.set_xlabel("Age")
    ax.set_ylabel("Market value (€M)")
    ax.grid(color=NEUTRAL_GRID, linewidth=0.8, alpha=0.45)
    _strip_spines(ax)
    ax.set_title("Squad age vs market value", loc="left", pad=12)
    ax.legend(loc="upper right", title="Role", title_fontsize=9)
    fig.tight_layout()
    return fig
