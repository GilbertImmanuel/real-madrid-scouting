"""
app.py - entry point / router for the Real Madrid scouting dashboard.

Run from the repo root:   streamlit run src/app.py

This file owns the ONLY st.set_page_config call and the navigation. Pages live in
src/pages/ and are wired explicitly via st.Page; because this file calls
st.navigation, Streamlit ignores the automatic pages/ menu (no double sidebar).
Streamlit puts this file's directory (src/) on sys.path, so pages can
`import data_loader` / `import visualizations` directly.
"""

import streamlit as st

import data_loader as dl
import visualizations as viz

st.set_page_config(
    page_title="Real Madrid Scouting",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Active theme: the sidebar brand below hardcodes light hexes that go invisible on
# dark (the charcoal "Scouting Dashboard" line especially), so resolve colors from
# the active palette. Gold underline stays gold in both. (set_page_config remains
# the first Streamlit call; this only reads context.)
dark = dl.active_dark()
PAL = viz.palette(dark)

# --- Persistent sidebar brand (shows on every page) ---------------------------
with st.sidebar:
    st.markdown(
        "<div style='line-height:1.12;margin-bottom:.25rem'>"
        "<div style='font-family:Montserrat,sans-serif;font-weight:800;"
        f"font-size:1.15rem;color:{PAL['primary']};letter-spacing:.01em'>REAL MADRID</div>"
        "<div style='font-family:Montserrat,sans-serif;font-weight:700;"
        f"font-size:0.95rem;color:inherit'>Scouting Dashboard</div>"
        "<div style='height:3px;width:42px;background:#FEBE10;margin-top:.5rem'></div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.caption("A Mourinho-fit squad-completion study")
    # Standing temporal caveat - non-negotiable, kept visible on every page.
    st.caption(
        "Methodology demo on a frozen **2022-23 FBref snapshot** - not a live "
        "shopping list."
    )

# --- Navigation ---------------------------------------------------------------
PAGES = [
    st.Page("pages/01_overview.py",          title="Overview",
            icon=":material/insights:",   url_path="overview", default=True),
    st.Page("pages/02_player_pool.py",       title="Player Pool",
            icon=":material/groups:",     url_path="player-pool"),
    st.Page("pages/03_madrid_squad_needs.py", title="Squad Needs",
            icon=":material/bar_chart:",  url_path="squad-needs"),
    st.Page("pages/04_mourinho_profile.py",  title="Mourinho Profile",
            icon=":material/tune:",       url_path="mourinho-profile"),
    st.Page("pages/05_shortlist.py",         title="Shortlist",
            icon=":material/star:",       url_path="shortlist"),
]

st.navigation(PAGES).run()
