#!/usr/bin/env python3
"""Train and evaluate Philly-consistent baseline models for exp_002."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from build_dataset import PHILLY_GEO_ID, build_modeling_table

FEATURE_COLS = ["rent_growth_1m_lag1", "rent_growth_1m_lag3", "rent_growth_1m_lag12", "rent_index_lag1", "unemployment_rate"]
TARGET_COL = "target_next_rent_growth_1m"


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float: return float(np.mean(np.abs(y_true - y_pred)))
def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float: return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float: return float(np.mean(np.sign(y_true) == np.sign(y_pred)))

def spearman_corr(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    corr = pd.Series(y_true).rank(method="average").corr(pd.Series(y_pred).rank(method="average"), method="pearson")
    return float(corr) if corr is not None else float("nan")


def fit_linear_regression(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    Xd = np.column_stack([np.ones(len(X)), X])
    coeffs, _, _, _ = np.linalg.lstsq(Xd, y, rcond=None)
    return coeffs


def predict_linear_regression(X: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones(len(X)), X]) @ coeffs


def score(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {"mae": mae(y_true, y_pred), "rmse": rmse(y_true, y_pred), "directional_accuracy": directional_accuracy(y_true, y_pred), "spearman_corr": spearman_corr(y_true, y_pred)}


def evaluate_window(df: pd.DataFrame, train_end: pd.Timestamp, val_end: pd.Timestamp | None = None) -> dict[str, Any]:
    tr = df[df["period_dt"] <= train_end].copy()
    va = df[df["period_dt"] > train_end].copy() if val_end is None else df[(df["period_dt"] > train_end) & (df["period_dt"] <= val_end)].copy()
    if tr.empty or va.empty:
        raise ValueError("Train/validation split is empty for provided cutoff window.")

    X_train, y_train = tr[FEATURE_COLS].to_numpy(float), tr[TARGET_COL].to_numpy(float)
    X_val, y_val = va[FEATURE_COLS].to_numpy(float), va[TARGET_COL].to_numpy(float)
    y_naive = va["rent_growth_1m_lag1"].to_numpy(float)
    coeffs = fit_linear_regression(X_train, y_train)
    y_lin = predict_linear_regression(X_val, coeffs)

    preds = va[["entity_id", "geography_entity_id", "period", TARGET_COL, "rent_growth_1m_lag1"]].copy()
    preds = preds.rename(columns={TARGET_COL: "y_true", "rent_growth_1m_lag1": "y_pred_naive_lag1"})
    preds["y_pred_linear"] = y_lin

    return {
        "split": {"train_rows": int(len(tr)), "validation_rows": int(len(va)), "train_min_period": str(tr["period_dt"].min().date()), "train_max_period": str(tr["period_dt"].max().date()), "validation_min_period": str(va["period_dt"].min().date()), "validation_max_period": str(va["period_dt"].max().date())},
        "naive_lag1": score(y_val, y_naive),
        "linear_regression": score(y_val, y_lin),
        "predictions": preds,
        "weights": pd.DataFrame({"feature": ["intercept"] + FEATURE_COLS, "weight": coeffs}),
    }


def rolling_backtest(df: pd.DataFrame, n_folds: int, val_months: int, min_train_months: int) -> list[dict[str, Any]]:
    periods = sorted(df["period_dt"].dropna().drop_duplicates())
    out: list[dict[str, Any]] = []
    for i in range(1, n_folds + 1):
        cutoff_idx = len(periods) - (val_months * i) - 1
        if cutoff_idx < min_train_months:
            break
        train_end = pd.Timestamp(periods[cutoff_idx])
        val_end = train_end + pd.DateOffset(months=val_months)
        w = evaluate_window(df, train_end, val_end)
        w["split"]["fold"] = i
        w["split"]["train_end_date"] = str(train_end.date())
        w["split"]["validation_end_date"] = str(val_end.date())
        out.append(w)
    return out


def aggregate(rolling_results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    if not rolling_results:
        return {}
    agg: dict[str, dict[str, float]] = {}
    for m in ["naive_lag1", "linear_regression"]:
        agg[m] = {}
        for k in ["mae", "rmse", "directional_accuracy", "spearman_corr"]:
            vals = [float(r[m][k]) for r in rolling_results]
            agg[m][f"{k}_mean"] = float(np.mean(vals))
            agg[m][f"{k}_std"] = float(np.std(vals))
    return agg


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apt-path", type=Path, required=True)
    p.add_argument("--econ-path", type=Path, required=True)
    p.add_argument("--artifacts-dir", type=Path, required=True)
    p.add_argument("--train-end-date", type=str, default="2024-12-31")
    p.add_argument("--philly-geo-id", type=str, default=PHILLY_GEO_ID)
    p.add_argument("--rolling-folds", type=int, default=3)
    p.add_argument("--rolling-val-months", type=int, default=6)
    p.add_argument("--min-train-months", type=int, default=36)
    a = p.parse_args()

    a.artifacts_dir.mkdir(parents=True, exist_ok=True)
    df = build_modeling_table(a.apt_path, a.econ_path, a.philly_geo_id)
    holdout = evaluate_window(df, pd.to_datetime(a.train_end_date), None)
    rolling = rolling_backtest(df, a.rolling_folds, a.rolling_val_months, a.min_train_months)
    rolling_agg = aggregate(rolling)

    df.to_csv(a.artifacts_dir / "modeling_table.csv", index=False)
    holdout["predictions"].to_csv(a.artifacts_dir / "predictions_holdout.csv", index=False)
    holdout["weights"].to_csv(a.artifacts_dir / "feature_weights_holdout.csv", index=False)
    if rolling:
        pieces = []
        for r in rolling:
            t = r["predictions"].copy(); t["fold"] = r["split"]["fold"]; t["train_end_date"] = r["split"]["train_end_date"]; t["validation_end_date"] = r["split"]["validation_end_date"]; pieces.append(t)
        pd.concat(pieces, ignore_index=True).to_csv(a.artifacts_dir / "predictions_rolling.csv", index=False)

    pd.DataFrame([{"row_count": int(len(df)), "geo_count": int(df["geography_entity_id"].nunique()), "geography_entity_id": a.philly_geo_id, "min_period": str(df["period_dt"].min().date()), "max_period": str(df["period_dt"].max().date())}]).to_csv(a.artifacts_dir / "dataset_summary.csv", index=False)

    metrics = {
        "scope": {"philly_geo_id": a.philly_geo_id},
        "holdout": {"split": {**holdout["split"], "train_end_date": a.train_end_date}, "naive_lag1": holdout["naive_lag1"], "linear_regression": holdout["linear_regression"]},
        "rolling": {"n_folds_requested": a.rolling_folds, "n_folds_executed": len(rolling), "folds": [{"split": r["split"], "naive_lag1": r["naive_lag1"], "linear_regression": r["linear_regression"]} for r in rolling], "aggregate": rolling_agg},
    }
    (a.artifacts_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"Wrote artifacts to: {a.artifacts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
