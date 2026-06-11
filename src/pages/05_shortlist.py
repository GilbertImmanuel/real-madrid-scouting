"""05_shortlist.py — the headline page.

A band x area grid (3 value bands x 3 gap roles) of recruitment targets, each as a
card with a live role-relative radar (from shortlist_board_full.csv), value band,
Mourinho fit, and an auto-rationale (from shortlist_annotated.csv). Lead targets
per area are emphasised in gold. Below: an expandable full ranked board per role,
and a youth watchlist.

Pages never write and never open files directly \u2014 reads go through data_loader.
"""
import pandas as pd
import streamlit as st

import data_loader as dl
import visualizations as viz

# ---------------------------------------------------------------- config
# Radar axes per role = the heaviest-weighted metrics in mourinho_weights.json.
# Chat B owns this choice; page 04 (Mourinho Profile) should mirror it.
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

# Active theme (detect once; pass PAL/dark everywhere below).
dark = dl.active_dark()
PAL = viz.palette(dark)

BAND_ORDER = ["marquee", "mid", "bargain"]
BAND_RANGE = {"marquee": "\u2265 \u20ac80M", "mid": "\u20ac30\u201380M", "bargain": "< \u20ac30M"}
BAND_COLOR = {"marquee": PAL["primary"],
              "mid":     "#3777b8",   # reads on both themes (= ROLE_COLORS full_back)
              "bargain": PAL["muted"]}
ROLE_TITLE = {"striker": "Striker", "defensive_mid": "Defensive Mid", "full_back": "Full-Back"}

# Strengths/weaknesses accent literals (page-local; not in PALETTE). Lightened on
# dark so they stay legible on the dark canvas; gold stays accent-only elsewhere.
POS_COLOR = "#4ade80" if dark else "#1f7a4d"   # strengths (green)
NEG_COLOR = "#f59e0b" if dark else "#b25b00"   # weaknesses (orange)

# ---------------------------------------------------------------- data
final = dl.load_shortlist_final()
annotated = dl.load_shortlist_annotated().set_index("Player")
board = dl.load_board_full()
youth = dl.load_youth()

# role-median percentile profile (drawn behind each radar as context)
role_median = {
    role: board[board["role"] == role][dl.PCT_COLS].median()
    for role in board["role"].unique()
}


def _axes_cols(role):
    return ["pct__" + m for m in ROLE_RADAR_AXES.get(role, [])]


def _board_row(player, role):
    hit = board[(board["Player"] == player) & (board["role"] == role)]
    if hit.empty:
        hit = board[board["Player"] == player]
    return hit.iloc[0] if not hit.empty else None


def _chip(text, color):
    return (
        f"<span style='background:{color};color:#fff;border-radius:10px;"
        f"padding:1px 9px;font-size:0.72rem;font-weight:700;"
        f"letter-spacing:.02em'>{text}</span>"
    )


# ---------------------------------------------------------------- header
st.title("Shortlist")
st.write(
    "Targets laid out as a **value band \u00d7 area** grid: three price tiers down, "
    "three squad gaps across. One pick per cell \u2014 the best Mourinho fit at that "
    "price for that need. **Gold marks the lead target** in each area."
)

leads = final[final["lead_target"]]
lc = st.columns(3)
for col, role in zip(lc, dl.GAP_ROLES):
    row = leads[leads["role"] == role]
    with col:
        if not row.empty:
            r = row.iloc[0]
            st.markdown(
                f"<div style='border:2px solid {PAL['accent']};"
                f"border-radius:12px;padding:10px 14px'>"
                f"<div style='font-size:.72rem;color:{PAL['muted']};"
                f"font-weight:700'>\u2b50 LEAD \u00b7 {ROLE_TITLE[role].upper()}</div>"
                f"<div style='font-size:1.15rem;font-weight:800'>{r['Player']}</div>"
                f"<div style='font-size:.82rem;color:{PAL['muted']}'>"
                f"{r['Squad']} \u00b7 fit {r['mourinho_score']:.0f}</div></div>",
                unsafe_allow_html=True,
            )

st.divider()

# ---------------------------------------------------------------- the grid
st.subheader("Band \u00d7 area board")

for band in BAND_ORDER:
    st.markdown(
        f"#### {band.title()} &nbsp; "
        f"<span style='font-size:.8rem;color:{PAL['muted']};"
        f"font-weight:600'>{BAND_RANGE[band]}</span>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3, gap="medium")
    for col, role in zip(cols, dl.GAP_ROLES):
        cell = final[(final["band"] == band) & (final["role"] == role)]
        with col:
            with st.container(border=True):
                if cell.empty:
                    st.caption(f"_{ROLE_TITLE[role]} \u2014 no pick at this band._")
                    continue
                r = cell.iloc[0]
                is_lead = bool(r["lead_target"])

                head = f"**{r['Player']}**"
                if is_lead:
                    head = f"\u2b50 {head}"
                st.markdown(head)
                st.markdown(
                    f"{_chip(ROLE_TITLE[role], BAND_COLOR[band])} "
                    f"&nbsp; <span style='color:{PAL['muted']};font-size:.8rem'>"
                    f"{r['Squad']} \u00b7 age {int(r['age_snap'])} \u00b7 \u20ac{r['valM']:.0f}M</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<span style='font-size:.78rem;color:{PAL['muted']}'>"
                    f"Mourinho fit</span> &nbsp;"
                    f"<span style='font-size:1.05rem;font-weight:800;"
                    f"color:{PAL['primary']}'>{r['mourinho_score']:.0f}</span>"
                    f"<span style='color:{PAL['muted']};font-size:.8rem'>/100</span>",
                    unsafe_allow_html=True,
                )

                brow = _board_row(r["Player"], role)
                if brow is not None:
                    fig = viz.radar(
                        brow, _axes_cols(role),
                        compare=role_median.get(role),
                        title="",
                        dark=dark,
                    )
                    st.pyplot(fig, width='stretch')

                ann = annotated.loc[r["Player"]] if r["Player"] in annotated.index else None
                if ann is not None:
                    st.markdown(
                        f"<span style='color:{POS_COLOR};font-size:.8rem'>\u25b2 "
                        f"{ann['strengths']}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color:{NEG_COLOR};font-size:.8rem'>\u25bc "
                        f"{ann['weaknesses']}</span>",
                        unsafe_allow_html=True,
                    )
                    with st.expander("Why this pick"):
                        st.write(ann["rationale"])

st.caption(
    "Radar = role-relative percentiles (0\u2013100) on this role's heaviest Mourinho "
    "metrics; the dashed grey shape behind is the role's median across the board. "
    "A radar only makes sense **within** a role \u2014 axes differ between roles."
)

st.divider()

# ---------------------------------------------------------------- full board
st.subheader("Full board per role")
st.caption("Every candidate that survived the funnel for each gap role, ranked by Mourinho fit.")

board_cols = ["role_rank", "Player", "Squad", "age_snap", "valM", "band", "mourinho_score"]
for role in dl.GAP_ROLES:
    sub = (board[board["role"] == role]
           .sort_values("role_rank")[board_cols]
           .reset_index(drop=True))
    with st.expander(f"{ROLE_TITLE[role]} \u2014 {len(sub)} candidates"):
        st.dataframe(
            sub.rename(columns={
                "role_rank": "Rank", "age_snap": "Age",
                "valM": "Value (\u20acM)", "mourinho_score": "Fit",
            }).style.format({"Rank": "{:.0f}", "Age": "{:.0f}",
                             "Value (\u20acM)": "{:.0f}", "Fit": "{:.1f}"}),
            width='stretch', hide_index=True,
        )

st.divider()

# ---------------------------------------------------------------- youth
st.subheader("Youth watchlist")
st.caption(
    "Tier C prospects (age \u2264 21) scored against the **senior** pool \u2014 a separate "
    "track for talent to develop into the gap roles rather than fill them now."
)
youth_show = youth.sort_values("mourinho_score", ascending=False).reset_index(drop=True)
youth_show["role"] = youth_show["role"].map(lambda r: r.replace("_", " ").title())
st.dataframe(
    youth_show.rename(columns={
        "valM": "Value (\u20acM)", "mourinho_score": "Fit", "role": "Role",
    }).style.format({"Age": "{:.0f}", "Value (\u20acM)": "{:.0f}", "Fit": "{:.1f}"}),
    width='stretch', hide_index=True,
)

with st.expander("Caveats", icon=":material/info:"):
    st.markdown(
        "- **Snapshot basis (2022-23).** Haaland is at Dortmund here, Davies at "
        "Bayern \u2014 several targets have since moved or aged. This is a methodology "
        "demo on a frozen snapshot, not a live shopping list.\n"
        "- **Defender volume inflation.** Low-block teams (Metz, Atalanta) pad "
        "tackle/clearance counts, which can flatter defensive radars.\n"
        "- **Authored weights.** Fit scores rest on hand-authored Mourinho priors, "
        "not objective truth (see the Mourinho Profile page)."
    )
