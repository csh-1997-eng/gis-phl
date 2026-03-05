"""Build modeling table for exp_003 Philly-region ZIP panel."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFAULT_REGION_STATES = ("PA", "NJ", "DE")


def _infer_region_type(geo_id: str) -> str:
    gid = str(geo_id).lower()
    if ":zip:" in gid:
        return "zip"
    if ":city:" in gid:
        return "city"
    if ":msa:" in gid:
        return "msa"
    if gid.startswith("geo:zori:"):
        return "zori_region"
    return "unknown"


def _infer_state_from_geo_id(geo_id: str) -> str:
    tail = str(geo_id).split(":")[-1]
    if "__" in tail:
        return tail.split("__")[-1].upper()
    return ""


def _normalize_apartment_market_schema(apt: pd.DataFrame) -> pd.DataFrame:
    out = apt.copy()
    geo = out.get("geography_entity_id", pd.Series([""] * len(out), index=out.index)).fillna("").astype(str)

    if "region_type" not in out.columns:
        out["region_type"] = geo.apply(_infer_region_type)
    else:
        out["region_type"] = out["region_type"].fillna("").astype(str).str.lower()

    if "state_name" not in out.columns:
        out["state_name"] = geo.apply(_infer_state_from_geo_id)
    else:
        state = out["state_name"].fillna("").astype(str)
        out["state_name"] = state.where(state.str.len() > 0, geo.apply(_infer_state_from_geo_id))

    if "region_name" not in out.columns:
        out["region_name"] = geo
    else:
        out["region_name"] = out["region_name"].fillna("").astype(str)

    if "source_dataset" not in out.columns:
        out["source_dataset"] = "legacy_unknown"
    else:
        out["source_dataset"] = out["source_dataset"].fillna("legacy_unknown").astype(str)

    return out


def build_modeling_table(apt_path: Path, econ_path: Path, region_states: tuple[str, ...] = DEFAULT_REGION_STATES, min_history_months: int = 24) -> pd.DataFrame:
    apt = pd.read_csv(apt_path, low_memory=False)
    econ = pd.read_csv(econ_path, low_memory=False)
    apt = _normalize_apartment_market_schema(apt)

    apt["period_dt"] = pd.to_datetime(apt["period"], format="%Y-%m-%d", errors="coerce")
    econ["period_dt"] = pd.to_datetime(econ["period"], format="%Y-%m-%d", errors="coerce")

    apt = apt.dropna(subset=["period_dt", "geography_entity_id", "rent_index", "rent_growth_1m"]).copy()
    econ = econ.dropna(subset=["period_dt"]).copy()

    apt = apt[(apt["region_type"] == "zip") & (apt["state_name"].isin(region_states))].copy()
    if apt.empty:
        raise ValueError(f"No ZIP rows found for states={region_states}")

    zip_counts = apt.groupby("geography_entity_id", as_index=False).agg(n_months=("period_dt", "nunique"))
    keep_geo = set(zip_counts[zip_counts["n_months"] >= min_history_months]["geography_entity_id"].tolist())
    apt = apt[apt["geography_entity_id"].isin(keep_geo)].copy()
    if apt.empty:
        raise ValueError(f"No ZIP geographies satisfy min_history_months={min_history_months}")

    apt["period_month"] = apt["period_dt"].dt.to_period("M").astype(str)
    econ["period_month"] = econ["period_dt"].dt.to_period("M").astype(str)
    econ_monthly = econ.sort_values("period_dt").groupby("period_month", as_index=False).agg({"unemployment_rate": "mean"})

    df = apt.merge(econ_monthly, on="period_month", how="left")
    df = df.sort_values(["geography_entity_id", "period_dt"]).reset_index(drop=True)

    grouped = df.groupby("geography_entity_id", group_keys=False)
    df["rent_growth_1m_lag1"] = grouped["rent_growth_1m"].shift(1)
    df["rent_growth_1m_lag3"] = grouped["rent_growth_1m"].shift(3)
    df["rent_growth_1m_lag12"] = grouped["rent_growth_1m"].shift(12)
    df["rent_index_lag1"] = grouped["rent_index"].shift(1)
    df["target_next_rent_growth_1m"] = grouped["rent_growth_1m"].shift(-1)

    feature_cols = ["rent_growth_1m_lag1", "rent_growth_1m_lag3", "rent_growth_1m_lag12", "rent_index_lag1", "unemployment_rate"]
    model_df = df.dropna(subset=["target_next_rent_growth_1m", "period_dt"] + feature_cols).copy()

    return model_df[["entity_id", "geography_entity_id", "period", "period_dt", "period_month", "region_name", "region_type", "state_name", "source_dataset", "target_next_rent_growth_1m"] + feature_cols]
