"""
scoring.py - Mourinho-fit scoring for the Real Madrid scouting pool.

Pipeline:
  1. load the cleaned player pool (NB1 output: one row per player-season)
  2. aggregate each player's metrics across seasons (minutes-weighted, per-90 aware)
  3. percentile-rank every metric WITHIN role
  4. combine percentiles using config/mourinho_weights.json, rescaling the weights
     for any metric a player is missing so the score stays on a 0-100 scale

Per-90 conversion lives HERE, not in NB1: the weights file is the single source of
truth for which columns are raw counts (per90=true) vs already-rates (per90=false).

Used by NB3/NB4 and the Streamlit app via the functions below; also runnable directly
(`python src/scoring.py`) for a quick sanity print.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------------------------- io ----
def load_weights(path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_pool(path) -> pd.DataFrame:
    return pd.read_csv(path)


def _metric_catalogue(weights: dict) -> dict:
    """Every metric column used anywhere, mapped to its per90 flag (for aggregation)."""
    cat = {}
    for role in weights["roles"].values():
        for m in role["metrics"].values():
            cat[m["column"]] = bool(m["per90"])
    return cat


# ------------------------------------------------------------ aggregation ----
def aggregate_player_seasons(pool: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """Collapse a player's season rows into one row, minutes-weighted and NaN-aware.

    per90=True  columns -> sum(counts over present seasons) / sum(90s over present seasons)
    per90=False columns -> minutes-weighted mean over present seasons

    Uses Min_Playing (primary-club minutes, which match the stat counts) as the weight,
    NOT season_total_min (that was only for the Tier filter). A metric missing in some
    seasons is aggregated over the seasons where it exists; missing in all -> NaN.
    """
    cat = _metric_catalogue(weights)
    records = []
    for url, g in pool.groupby("Url"):
        rep = g.loc[g["Min_Playing"].idxmax()]  # representative row for identity fields
        rec = {
            "Url": url,
            "Player": rep["Player"],
            "Squad": rep["Squad"],
            "role": rep["role"],
            "Age": rep.get("Age"),
            "n_seasons": int(len(g)),
            "total_min": float(g["Min_Playing"].sum()),
        }
        for col, per90 in cat.items():
            if col not in g.columns:
                rec[col] = np.nan
                continue
            sub = g[["Min_Playing", col]].dropna(subset=[col])
            mins = float(sub["Min_Playing"].sum())
            if sub.empty or mins <= 0:
                rec[col] = np.nan
            elif per90:
                rec[col] = float(sub[col].sum() / (mins / 90.0))
            else:  # already a rate -> minutes-weighted average
                rec[col] = float((sub[col] * sub["Min_Playing"]).sum() / mins)
        records.append(rec)
    return pd.DataFrame.from_records(records)


# ---------------------------------------------------------------- scoring ----
def _percentiles_within(sub: pd.DataFrame, metric_specs: dict) -> pd.DataFrame:
    """Percentile-rank (0-100) each metric within the given (single-role) frame.
    direction='low' metrics are reversed so that a lower raw value scores higher."""
    pct = pd.DataFrame(index=sub.index)
    for name, m in metric_specs.items():
        col = m["column"]
        p = sub[col].rank(pct=True) if col in sub.columns else pd.Series(np.nan, index=sub.index)
        if m.get("direction", "high") == "low":
            p = 1.0 - p
        pct[name] = p * 100.0
    return pct


def score_pool(agg: pd.DataFrame, weights: dict) -> pd.DataFrame:
    """Percentile-within-role + rescaled weighted composite.

    Returns one row per player with `mourinho_score` (0-100), `role_rank`,
    `metrics_used`, and a `pct__<metric>` breakdown (handy for radar charts).
    """
    pieces = []
    for role, spec in weights["roles"].items():
        sub = agg[agg["role"] == role].copy()
        if sub.empty:
            continue
        metric_specs = spec["metrics"]
        pct = _percentiles_within(sub, metric_specs)

        weight_vec = np.array([metric_specs[n]["weight"] for n in pct.columns], dtype=float)
        P = pct.to_numpy(dtype=float)            # (players, metrics), NaN allowed
        present = ~np.isnan(P)
        eff_w = present * weight_vec             # missing metrics get zero weight
        denom = eff_w.sum(axis=1)
        numer = np.nansum(P * eff_w, axis=1)
        score = np.where(denom > 0, numer / denom, np.nan)

        sub["mourinho_score"] = score
        sub["role_rank"] = pd.Series(score, index=sub.index).rank(ascending=False, method="min")
        sub["metrics_used"] = present.sum(axis=1)
        for c in pct.columns:
            sub[f"pct__{c}"] = pct[c].to_numpy()
        pieces.append(sub)

    if not pieces:
        return pd.DataFrame()
    res = pd.concat(pieces, ignore_index=True)
    return (res.sort_values(["role", "mourinho_score"], ascending=[True, False])
               .reset_index(drop=True))


def top_n(scored: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top-n players per role by composite score."""
    return (scored.sort_values("mourinho_score", ascending=False)
                  .groupby("role", group_keys=False).head(n))


def run(pool_path, weights_path) -> pd.DataFrame:
    """Convenience end-to-end: load -> aggregate -> score."""
    weights = load_weights(weights_path)
    pool = load_pool(pool_path)
    return score_pool(aggregate_player_seasons(pool, weights), weights)


# ----------------------------------------------------------- script demo ----
if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parents[1]
    weights_path = ROOT / "config" / "mourinho_weights.json"
    pool_path = ROOT / "data" / "transformed" / "tier_A_players.csv"

    scored = run(pool_path, weights_path)
    out = ROOT / "data" / "transformed" / "scored_pool.csv"
    scored.to_csv(out, index=False)
    print(f"scored {len(scored)} players -> {out}\n")

    show = ["Player", "Squad", "role", "Age", "total_min", "metrics_used", "mourinho_score"]
    for role in scored["role"].unique():
        print(f"--- top 5 {role} ---")
        print(scored[scored["role"] == role][show].head(5).to_string(index=False))
        print()
