"""Build modeling table for exp_001 baseline rent growth forecast."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_modeling_table(apt_path: Path, econ_path: Path) -> pd.DataFrame:
    apt = pd.read_csv(apt_path)
    econ = pd.read_csv(econ_path)

    apt["period_dt"] = pd.to_datetime(apt["period"], errors="coerce")
    econ["period_dt"] = pd.to_datetime(econ["period"], errors="coerce")

    apt = apt.dropna(subset=["period_dt", "geography_entity_id"]).copy()
    econ = econ.dropna(subset=["period_dt"]).copy()

    # Align to month key to avoid day-of-month mismatch across sources.
    apt["period_month"] = apt["period_dt"].dt.to_period("M").astype(str)
    econ["period_month"] = econ["period_dt"].dt.to_period("M").astype(str)

    econ_monthly = (
        econ.sort_values("period_dt")
        .groupby("period_month", as_index=False)
        .agg({"unemployment_rate": "mean"})
    )

    df = apt.merge(econ_monthly, on="period_month", how="left")
    df = df.sort_values(["geography_entity_id", "period_dt"]).reset_index(drop=True)

    grouped = df.groupby("geography_entity_id", group_keys=False)
    df["rent_growth_1m_lag1"] = grouped["rent_growth_1m"].shift(1)
    df["rent_growth_1m_lag3"] = grouped["rent_growth_1m"].shift(3)
    df["rent_growth_1m_lag12"] = grouped["rent_growth_1m"].shift(12)
    df["rent_index_lag1"] = grouped["rent_index"].shift(1)

    # Forecast target: next month's 1m rent growth.
    df["target_next_rent_growth_1m"] = grouped["rent_growth_1m"].shift(-1)

    feature_cols = [
        "rent_growth_1m_lag1",
        "rent_growth_1m_lag3",
        "rent_growth_1m_lag12",
        "rent_index_lag1",
        "unemployment_rate",
    ]

    required_cols = ["target_next_rent_growth_1m", "period_dt", "geography_entity_id"] + feature_cols
    model_df = df.dropna(subset=required_cols).copy()

    return model_df[
        [
            "entity_id",
            "geography_entity_id",
            "period",
            "period_dt",
            "period_month",
            "target_next_rent_growth_1m",
        ]
        + feature_cols
    ]
