"""04_mourinho_profile.py — the Mourinho archetype, role by role.

Renders config/mourinho_weights.json: per role, the hand-authored metric weights
(bars), each metric's per-90/rate and direction flags, and which metrics are the
axes on the shortlist radars. The page narrates what the archetype rewards and is
explicit that these weights are an authored tactical PRIOR, not objective truth.

Non-negotiables honoured: reads only via data_loader (load_weights), never writes,
no st.set_page_config. The radar-axis mapping is data_loader.ROLE_RADAR_AXES so the
axes here match page 05's radars exactly.
"""
from __future__ import annotations

import streamlit as st

import data_loader as dl
import visualizations as viz

dark = dl.active_dark()
PAL = viz.palette(dark)


def _pretty_metric(key: str) -> str:
    """'non_pen_xg' -> 'Non Pen Xg' (mirrors the app's label convention)."""
    return key.replace("_", " ").title()


def _pretty_role(role: str) -> str:
    return str(role).replace("_", " ").title()


def _weight_rows(role: str, metrics: dict) -> str:
    """Build the HTML for one role's weight bars, ordered heaviest first."""
    axes = set(dl.ROLE_RADAR_AXES.get(role, []))
    color = viz.ROLE_COLORS[role]
    items = sorted(metrics.items(), key=lambda kv: kv[1]["weight"], reverse=True)
    max_w = max((m["weight"] for _, m in items), default=1.0)

    rows = []
    for key, spec in items:
        w = spec["weight"]
        bar_pct = (w / max_w) * 100 if max_w else 0
        is_axis = f"pct__{key}" in axes
        low = spec.get("direction") == "low"

        label = _pretty_metric(key)
        marker = (f" <span title='Axis on the shortlist radar' "
                  f"style='color:{color}'>&#9670;</span>") if is_axis else ""
        flags = "per 90" if spec.get("per90") else "rate"
        if low:
            flags += " &middot; &#8595; lower better"

        rows.append(
            f"<div style='display:flex;align-items:center;gap:.6rem;margin:.26rem 0'>"
            f"<div style='width:188px;font-size:.83rem;color:inherit'>{label}{marker}</div>"
            f"<div style='flex:1;background:rgba(135,145,160,.22);border-radius:4px;height:13px'>"
            f"<div style='width:{bar_pct:.1f}%;background:{color};height:100%;border-radius:4px'></div>"
            f"</div>"
            f"<div style='width:42px;text-align:right;font-size:.8rem;font-weight:600;"
            f"color:inherit'>{w:.0%}</div>"
            f"<div style='width:118px;font-size:.7rem;color:{PAL['muted']}'>{flags}</div>"
            f"</div>"
        )
    return "".join(rows)


# ==============================================================================
weights = dl.load_weights()
roles = weights["roles"]

st.title("Mourinho Profile")
st.caption(
    "The scoring archetype — a hand-authored set of per-role metric weights that "
    "encode Mourinho's tactical identity: defensive solidity, aerial dominance, "
    "transitional carrying, and wide players who track back."
)

# --- Authored-prior caveat (one of the three standing caveats) ----------------
st.warning(
    "**These weights are an authored prior, not objective truth.** They were "
    "written *before* the rankings were seen — that ordering is what keeps the "
    "exercise honest. Every candidate is percentile-ranked **within their role** "
    "and scored against the weights below; a metric missing for a player is "
    "dropped and that role's remaining weights are rescaled to sum to 1.0.",
    icon=":material/info:",
)

with st.expander("How a player's fit score is built"):
    st.markdown(
        "1. Assign each player a role from their Transfermarkt position.\n"
        "2. For every metric in that role, percentile-rank the player's "
        "3-season average **against same-role players only** (0-100).\n"
        "3. Composite fit = sum(weight x percentile). NaN metrics are dropped and "
        "the role's weights rescaled to 1.0.\n"
        "4. `direction = low` metrics (errors, miscontrols) are reverse-ranked - "
        "a lower raw value scores higher."
    )
    st.markdown(
        f"<span style='color:{PAL['muted']};font-size:.82rem'>"
        "Pressing pressures are deliberately <b>excluded</b>: Opta stopped publishing "
        "them for 2022-23, and Mourinho's identity is a compact low block rather "
        "than a gegenpress - so a 3-season pressure signal would be both "
        "inconsistent and off-archetype.</span>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"<div style='margin:.4rem 0 .2rem;color:{PAL['muted']};font-size:.8rem'>"
    "&#9670; marks the six axes drawn on each player's shortlist radar &middot; "
    "weights sum to 100% within every role.</div>",
    unsafe_allow_html=True,
)

# --- Per-role weight panels ---------------------------------------------------
for role in viz.ROLE_ORDER:
    spec = roles[role]
    color = viz.ROLE_COLORS[role]
    with st.container(border=True):
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:.55rem;margin-bottom:.15rem'>"
            f"<span style='width:13px;height:13px;border-radius:3px;background:{color};"
            f"display:inline-block'></span>"
            f"<span style='font-family:Montserrat,sans-serif;font-weight:700;"
            f"font-size:1.05rem;color:inherit'>{_pretty_role(role)}</span>"
            f"<span style='color:{PAL['muted']};font-size:.8rem'>"
            f"&middot; {len(spec['metrics'])} metrics</span></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='color:{PAL['muted']};font-size:.86rem;font-style:italic;"
            f"margin-bottom:.5rem'>{spec['_rationale']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(_weight_rows(role, spec["metrics"]), unsafe_allow_html=True)

st.caption(
    "Source: config/mourinho_weights.json. Edit a weight there and the whole "
    "scoring pipeline shifts - the archetype is transparent and tunable by design."
)
