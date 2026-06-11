# Real Madrid Scouting under Mourinho

**A data-driven scouting study: which players would *complete* Real Madrid's squad under José Mourinho — age-capped, role-by-role, and fit-scored against a hand-authored Mourinho archetype.**

The output is a multipage **Streamlit** dashboard that walks through the squad's gaps, the scoring method, and a value-band × area shortlist with role-relative radars.

> **Live demo:** [Real Madrid Scouting](https://data-driven-rm-scouting.streamlit.app/)

---

## The premise

Florentino Pérez won the Real Madrid presidential election on **7 June 2026** (mandate to 2030), and a **José Mourinho** appointment for 2026-27 has been reported as imminent. A board running a multi-year project doesn't sign players who'll be 30+ for it — so this study runs an **age-capped, Mourinho-fit** search for the players who'd round out the squad.

It is a methodology demo built on a frozen data snapshot, not a literal transfer list. See the **Disclaimer**.

---

## Methodology — three lenses

Every shortlisted player is judged through three independent lenses:

1. **Pool quality** — a tiered minutes filter over the Big-5 leagues keeps players with a real, established body of work (Tier A) and separates them from thin-sample names.
2. **Mourinho fit** — a **hand-authored** per-role weight set (`config/mourinho_weights.json`) encodes Mourinho's identity (defensive solidity, aerial dominance, transitional carrying, experience, wide players who track back). Players are percentile-ranked *within their role*, then composited 0–100. The weights are written **before** the rankings are seen, to keep the exercise honest.
3. **Squad need** — Madrid's current squad is profiled by role, depth, and age to surface the genuine **gap roles** (striker, defensive-mid, full-back) that drive the shortlist.

The result is a **value-band × area grid**: one lead target per area, plus marquee / mid / bargain options and a separate youth watchlist.

---

## Setup

**Requirements:** Python 3.13 (3.12 also fine). Works on Windows, macOS, or Linux (paths use `pathlib`).

### 1. Install

```bash
python -m pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run src/app.py
```

The app is presentation-only: it reads the committed CSV/JSON in `data/` and `config/` and never writes. As long as those files are present, this is the single command you need.

### 3. (Optional) Re-run the data pipeline

Only needed to regenerate the data from scratch. Download `players.csv` from the [Transfermarkt dataset on Kaggle](https://www.kaggle.com/datasets/davidcariboo/player-scores)
and place it at `data/raw/transfers/players.csv`.

```bash
python bootstrap_data.py          # frozen .rds snapshot  ->  data/raw/fbref/*.parquet
# notebooks/01_player_pool.ipynb   # build the tiered player pool
# notebooks/02_madrid_transfers.ipynb  # Transfermarkt enrichment + Madrid squad needs
python src/scoring.py             # per-player Mourinho-fit scores -> scored_pool.csv
# notebooks/03_scouting_output.ipynb   # funnel -> shortlist + radars + youth list
```

Re-running NB1 requires re-running NB2 (NB2 overwrites the tier files with enriched roles + market values).

---

## Project structure

```
real-madrid-scouting/
├── .streamlit/
│   └── config.toml
├── config/
│   └── mourinho_weights.json
├── bootstrap_data.py
├── notebooks/
│   ├── 01_player_pool.ipynb
│   ├── 02_madrid_transfers.ipynb
│   └── 03_scouting_output.ipynb
├── src/
│   ├── app.py
│   ├── data_loader.py
│   ├── scoring.py
│   ├── visualizations.py
│   └── pages/
│       ├── 01_overview.py
│       ├── 02_player_pool.py
│       ├── 03_madrid_squad_needs.py
│       ├── 04_mourinho_profile.py
│       └── 05_shortlist.py
├── data/
│   ├── raw/
│   ├── transformed/
│   │   ├── pool_enriched.csv
│   │   ├── madrid_squad_profile.csv
│   │   ├── scored_pool.csv
│   │   ├── fbref_merged.csv
│   │   └── tier_A/B/C_players.csv
│   └── outputs/
│       ├── shortlist_final.csv
│       ├── shortlist_annotated.csv
│       ├── shortlist_board_full.csv
│       └── youth_watchlist.csv
├── requirements.txt
└── README.md
```

**Data the app needs at runtime** (it errors without them): `config/mourinho_weights.json`, `data/transformed/pool_enriched.csv`, `data/transformed/madrid_squad_profile.csv`, and the four files in `data/outputs/`. Everything under `data/raw/` and the `tier_*` / `fbref_merged` intermediates are pipeline-only.

---

## Tech stack

Python · pandas / numpy · Matplotlib · **Streamlit** (multipage, adaptive light/dark theme). Source data comes from a **frozen pre-removal FBref snapshot** (`worldfootballR_data`, read in Python via `pyreadr`) and **Transfermarkt** (`players.csv`, dcaribou) for roles, market value, and the current squad.

---

## Disclaimer

This is a **methodology demonstration on a frozen 2022-23 snapshot** — a hypothesis to argue with, not a literal shopping list. Three caveats are kept deliberately visible because they're the project's integrity:

1. **2022-23 snapshot basis.** FBref's advanced stats (xG, progressive, SCA/GCA, the defensive table) were permanently removed in **January 2026** when Opta pulled its feed. The project pivoted to a frozen, fully reproducible snapshot (seasons 2020-21 → 2022-23). Players are therefore aged and valued **as of then** (e.g. Haaland at Dortmund, Davies at Bayern), while the current-squad page reflects **today's** Madrid — so the two sides sit on different timelines by design. The pipeline is season-agnostic and would run identically on a live feed.
2. **Defender volume inflation.** Raw tackles / clearances / blocks are **not** possession-adjusted, so low-block sides (Metz, Atalanta) are flattered on defensive volume. Possession-adjusted metrics are a noted future refinement.
3. **Authored weights, not objective truth.** The Mourinho archetype is a **hand-authored prior**, set before the rankings were seen. It's transparent and editable — change the weights and the board changes. Treat it as one informed opinion, not ground truth.

Nothing here is affiliated with, endorsed by, or sourced from Real Madrid C.F. or José Mourinho. All data belongs to its original providers (below); this repository only transforms and presents publicly available aggregate statistics for a non-commercial, educational study. The election and appointment details reflect reporting as of June 2026.

---

## Acknowledgements

- **`JaseZiv/worldfootballR_data`** — the frozen pre-removal FBref/Opta advanced-stats snapshot that makes the whole study reproducible. The underlying season stats are from **FBref** (data formerly via Stats Perform / Opta).
- **[dcaribou/transfermarkt-datasets](https://www.kaggle.com/datasets/davidcariboo/player-scores)** — the Transfermarkt dump (`players.csv`) used for player roles, market values, and the current Real Madrid squad.
- **Streamlit**, **pandas**, **numpy**, and **Matplotlib** — the open-source stack the dashboard and pipeline are built on.
- The broader **football-data community** — the open datasets, ID maps, and provider guides that make independent football analysis possible at all.
