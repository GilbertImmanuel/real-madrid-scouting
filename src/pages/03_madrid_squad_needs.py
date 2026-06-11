"""03_madrid_squad_needs.py — where the shortlist comes from.

Reads madrid_squad_profile.csv (CURRENT squad) and turns it into the squad-need
story that drives the gap roles: striker, defensive_mid, full_back.
Pages never write and never open files directly \u2014 all reads go through data_loader.
"""
import streamlit as st

import data_loader as dl
import visualizations as viz

dark = dl.active_dark()

squad = dl.load_squad_profile()

st.title("Madrid Squad Needs")
st.write(
    "The current Real Madrid squad, read by role, depth and age. The thin and "
    "ageing areas below are exactly the **gap roles** the shortlist hunts in: "
    "**striker, defensive midfield, full-back**."
)


# ---- per-role summary (data-driven) -------------------------------------
def _role_summary(role: str) -> dict:
    sub = squad[squad["role"] == role]
    return {
        "n": len(sub),
        "mean_age": sub["age"].mean() if len(sub) else float("nan"),
        "oldest": sub.sort_values("age", ascending=False).head(1),
    }


gap_labels = {
    "striker": "Striker",
    "defensive_mid": "Defensive Mid",
    "full_back": "Full-Back",
}
cols = st.columns(3)
for col, role in zip(cols, dl.GAP_ROLES):
    s = _role_summary(role)
    with col:
        st.metric(
            label=gap_labels[role],
            value=f"{s['n']} in squad",
            delta=f"mean age {s['mean_age']:.0f}",
            delta_color="off",
        )

st.divider()

# ---- depth-by-role chart -------------------------------------------------
st.subheader("Depth by role")
st.caption(
    "Player count per role across the whole squad; the number inside each bar "
    "is the role's mean age."
)
st.pyplot(viz.squad_depth_chart(squad, dark=dark), width='stretch')


# ---- the gaps, narrated from the data -----------------------------------
st.subheader("Reading the gaps")

striker = squad[squad["role"] == "striker"].sort_values("valM", ascending=False)
dm = squad[squad["role"] == "defensive_mid"]
fb = squad[squad["role"] == "full_back"].sort_values("age", ascending=False)
fb_old = fb[fb["age"] >= 30]

st.markdown(
    f"""
- **Striker \u2014 thin.** Only **{len(striker)}** senior centre-forwards on the books
  ({", ".join(striker["name"].tolist())}). One marquee name plus very little behind him;
  an injury leaves the line bare. This is the headline need.
- **Defensive midfield \u2014 one senior body.** Just **{len(dm)}**
  recognised holding midfielder{"s" if len(dm) != 1 else ""}
  ({", ".join(dm["name"].tolist())}). No like-for-like cover for the single pivot
  Mourinho's shape leans on most.
- **Full-back \u2014 ageing.** {len(fb)} listed, but the senior options are getting on:
  {", ".join(f"{r['name']} ({int(r['age'])})" for _, r in fb_old.iterrows())}.
  Width and recovery pace are the first things to fade, so this is a medium-term
  rebuild rather than an emergency.
"""
)

st.divider()

# ---- age vs value scatter ------------------------------------------------
st.subheader("Age vs market value")
st.caption(
    "Each dot is a current squad member, colored by role. The dotted line marks "
    "age 30 \u2014 the P\u00e9rez board's reluctance to commit to players who would be 30+ "
    "for a multi-year project is part of why the search skews younger."
)
st.pyplot(viz.age_value_scatter(squad, dark=dark), width='stretch')
n_blank = int(squad["valM"].isna().sum())
st.caption(
    f"\u26a0\ufe0f {n_blank} squad members have no market value on file (academy / "
    "low-data players, e.g. Gonzalo Garc\u00eda) and are omitted from this scatter only."
)

# ---- standing caveats ----------------------------------------------------
with st.expander("Caveats on this analysis", icon=":material/info:"):
    st.markdown(
        "- **Defender volume inflation.** Raw defensive counts (tackles, "
        "clearances) are padded by players at low-block teams (Metz, Atalanta), "
        "who simply face more defensive situations. Possession-adjusting is a "
        "noted v2 refinement.\n"
        "- **Authored weights.** The Mourinho fit scores driving the shortlist "
        "come from a **hand-authored** set of priors, not an objective truth "
        "mined from his squads. See the Mourinho Profile page.\n"
        "- **Snapshot basis.** Player metrics are the 2022-23 frozen snapshot; "
        "the squad above is the *current* roster, so the two sides of the search "
        "sit on different timelines by design."
    )
