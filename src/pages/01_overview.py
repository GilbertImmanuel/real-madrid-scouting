"""01_overview.py — the landing page / project story.

Frames the study before any numbers: the Mourinho-fit premise, the FBref data
pivot (told as a strength), the 2022-23 snapshot framing, the three analytical
lenses, and the three standing caveats kept openly as the honest centrepiece.

Non-negotiables honoured: reads only via data_loader (for the live headline
counts), never writes, no st.set_page_config.
"""
from __future__ import annotations

import streamlit as st

import data_loader as dl
import visualizations as viz

dark = dl.active_dark()
PAL = viz.palette(dark)


def _rule(color: str) -> None:
    st.markdown(
        f"<div style='height:3px;width:46px;background:{color};margin:.1rem 0 .7rem'></div>",
        unsafe_allow_html=True,
    )


# --- Live headline numbers (so the framing is grounded in the real pool) ------
pool = dl.load_pool_enriched()
tiered = pool[pool["tier"].isin(["A", "B", "C"])]["Url"].nunique()
n_leagues = int(pool["Comp"].nunique())
short = dl.load_shortlist_final()
n_short = len(short)
n_leads = int(short["lead_target"].sum()) if "lead_target" in short.columns else len(dl.GAP_ROLES)
n_youth = len(dl.load_youth())

# ==============================================================================
st.title("Completing Real Madrid's squad under Mourinho")
st.markdown(
    f"<div style='font-size:1.05rem;color:inherit;max-width:60rem'>"
    "A data-driven scouting study: which players would <b>complete</b> Real Madrid's "
    "squad for a José Mourinho project — judged on squad need, Mourinho fit, and raw "
    "quality, not on hype.</div>",
    unsafe_allow_html=True,
)
st.write("")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Players scouted", f"{tiered:,}")
c2.metric("Leagues", n_leagues)
c3.metric("Shortlist targets", n_short)
c4.metric("Youth watchlist", n_youth)

st.caption(
    f"Big-{n_leagues} European leagues · seasons 2020-21 → 2022-23 · "
    f"{n_leads} lead targets across the three positions of need."
)

# --- Premise ------------------------------------------------------------------
st.subheader("The premise")
_rule(PAL["primary"])
st.markdown(
    "Florentino Pérez was re-elected Real Madrid president on **7 June 2026** "
    "(~65% of the vote, a mandate to 2030), and Mourinho's appointment for 2026-27 "
    "is the working premise of this study. A Pérez board building a multi-year "
    "project won't sign players who'd be 30-plus for its duration — so the search "
    "is **age-capped** and weighted toward profiles that fit a Mourinho side: "
    "defensively secure, aerially strong, strong in transition, with wide players "
    "who track back."
)

# --- The data pivot, framed as a strength -------------------------------------
st.subheader("Why a 2022-23 snapshot — and why that's a feature")
_rule(PAL["primary"])
st.markdown(
    "In **January 2026** FBref's advanced data (xG, progressive actions, the full "
    "defensive table) was **permanently removed** when Opta pulled its feed — live "
    "scraping for these metrics is dead. Rather than abandon the depth, the pipeline "
    "pivoted to a **frozen pre-removal snapshot** (`worldfootballR_data`, archived "
    "September 2025), giving a complete, reproducible record of the Big-5 leagues "
    "through 2022-23.\n\n"
    "The trade-off is honest: this is a **methodology demonstration on a frozen "
    "snapshot**, not a live shopping list. But the pipeline is **season-agnostic** — "
    "point it at a live feed and it runs identically. The constraint became a "
    "cleaner, fully reproducible build."
)

# --- The three lenses ---------------------------------------------------------
st.subheader("Three lenses")
_rule(PAL["primary"])
st.markdown(
    f"<div style='color:{PAL['muted']};margin-bottom:.6rem'>Every candidate is "
    "judged on three independent questions; only players that answer all three well "
    "reach the shortlist.</div>",
    unsafe_allow_html=True,
)
lenses = [
    ("Pool quality", "groups",
     "Did the player actually play, and produce, across three seasons of a top-5 "
     "league? The tiered minutes filter builds the scouting universe.",
     "→ Player Pool"),
    ("Mourinho fit", "tune",
     "How well does the player's profile match the hand-authored Mourinho archetype "
     "for their role — percentile-ranked against same-role peers?",
     "→ Mourinho Profile"),
    ("Squad need", "bar_chart",
     "Does Madrid actually need this profile? The shortlist targets only the thin or "
     "ageing areas of the current squad: striker, defensive mid, full-back.",
     "→ Squad Needs"),
]
cols = st.columns(3)
for col, (title, _icon, body, link) in zip(cols, lenses):
    with col:
        with st.container(border=True):
            st.markdown(
                f"<div style='font-family:Montserrat,sans-serif;font-weight:700;"
                f"font-size:1rem;color:{PAL['primary']}'>{title}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size:.86rem;color:inherit;min-height:6.2rem'>"
                f"{body}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='font-size:.8rem;font-weight:600;color:{PAL['muted']};"
                f"margin-bottom:.35rem'>"
                f"{link}</div>",
                unsafe_allow_html=True,
            )

# --- The three caveats: the honest centrepiece --------------------------------
st.subheader("Three caveats, kept in plain sight")
_rule(PAL["primary"])
caveats = [
    ("2022-23 snapshot basis",
     "Every stat is from the frozen 2020-21 → 2022-23 record. Players are valued and "
     "aged as of then (Haaland at Dortmund, Davies at Bayern); several 'targets' have "
     "since moved or aged out. The current-squad page, by contrast, reflects today's "
     "Madrid — so the two are deliberately not on the same timeline."),
    ("Defender volume inflation",
     "Raw defensive counts (tackles, clearances, blocks) aren't possession-adjusted, "
     "so players at low-block sides (Metz, Atalanta) are flattered on volume. "
     "Possession-adjusting is a noted next refinement."),
    ("Authored weights, not objective truth",
     "The Mourinho archetype is a hand-authored prior — metric weights set before the "
     "rankings were seen. It encodes a defensible reading of his identity, but it is a "
     "hypothesis to argue with, not a measurement. It's transparent and fully editable."),
]
with st.container(border=True):
    for i, (head, body) in enumerate(caveats):
        st.markdown(
            f"<div style='display:flex;gap:.6rem;{'margin-top:.7rem' if i else ''}'>"
            f"<div style='color:{PAL['primary']};font-weight:700'>{i + 1}.</div>"
            f"<div><span style='font-weight:700;color:inherit'>{head}.</span> "
            f"<span style='color:inherit'>{body}</span></div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("<div style='height:.45rem'></div>", unsafe_allow_html=True)

st.write("")
st.caption(
    "Navigate with the sidebar: **Player Pool** (the universe) → **Squad Needs** "
    "(the gaps) → **Mourinho Profile** (the archetype) → **Shortlist** (the targets)."
)
