#!/usr/bin/env python3
"""Train and evaluate baseline models for exp_001."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_dataset import build_modeling_table


FEATURE_COLS = [
    "rent_growth_1m_lag1",
    "rent_growth_1m_lag3",
    "rent_growth_1m_lag12",
    "rent_index_lag1",
    "unemployment_rate",
]
TARGET_COL = "target_next_rent_growth_1m"


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def directional_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.sign(y_true) == np.sign(y_pred)))


def spearman_corr(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Spearman rank correlation without external dependencies."""
    s_true = pd.Series(y_true).rank(method="average")
    s_pred = pd.Series(y_pred).rank(method="average")
    corr = s_true.corr(s_pred, method="pearson")
    return float(corr) if corr is not None else float("nan")


def fit_linear_regression(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    # Add intercept term and solve ordinary least squares via lstsq.
    X_design = np.column_stack([np.ones(len(X)), X])
    coeffs, _, _, _ = np.linalg.lstsq(X_design, y, rcond=None)
    return coeffs


def predict_linear_regression(X: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    X_design = np.column_stack([np.ones(len(X)), X])
    return X_design @ coeffs


def evaluate_split(df: pd.DataFrame, train_end_date: str) -> dict:
    train_end = pd.to_datetime(train_end_date)
    train_df = df[df["period_dt"] <= train_end].copy()
    val_df = df[df["period_dt"] > train_end].copy()

    if train_df.empty or val_df.empty:
        raise ValueError(
            "Train/validation split is empty. Adjust --train-end-date for available periods."
        )

    X_train = train_df[FEATURE_COLS].to_numpy(dtype=float)
    y_train = train_df[TARGET_COL].to_numpy(dtype=float)

    X_val = val_df[FEATURE_COLS].to_numpy(dtype=float)
    y_val = val_df[TARGET_COL].to_numpy(dtype=float)

    # Baseline 1: naive predictor = last observed 1m growth.
    y_pred_naive = val_df["rent_growth_1m_lag1"].to_numpy(dtype=float)

    # Baseline 2: linear regression.
    coeffs = fit_linear_regression(X_train, y_train)
    y_pred_linear = predict_linear_regression(X_val, coeffs)

    metrics = {
        "split": {
            "train_end_date": train_end_date,
            "train_rows": int(len(train_df)),
            "validation_rows": int(len(val_df)),
            "train_min_period": str(train_df["period_dt"].min().date()),
            "train_max_period": str(train_df["period_dt"].max().date()),
            "validation_min_period": str(val_df["period_dt"].min().date()),
            "validation_max_period": str(val_df["period_dt"].max().date()),
        },
        "naive_lag1": {
            "mae": mae(y_val, y_pred_naive),
            "rmse": rmse(y_val, y_pred_naive),
            "directional_accuracy": directional_accuracy(y_val, y_pred_naive),
            "spearman_corr": spearman_corr(y_val, y_pred_naive),
        },
        "linear_regression": {
            "mae": mae(y_val, y_pred_linear),
            "rmse": rmse(y_val, y_pred_linear),
            "directional_accuracy": directional_accuracy(y_val, y_pred_linear),
            "spearman_corr": spearman_corr(y_val, y_pred_linear),
        },
    }

    preds = val_df[
        ["entity_id", "geography_entity_id", "period", TARGET_COL, "rent_growth_1m_lag1"]
    ].copy()
    preds = preds.rename(columns={TARGET_COL: "y_true", "rent_growth_1m_lag1": "y_pred_naive_lag1"})
    preds["y_pred_linear"] = y_pred_linear

    weights = pd.DataFrame(
        {
            "feature": ["intercept"] + FEATURE_COLS,
            "weight": coeffs,
        }
    )

    summary = pd.DataFrame(
        [
            {
                "row_count": int(len(df)),
                "geo_count": int(df["geography_entity_id"].nunique()),
                "min_period": str(df["period_dt"].min().date()),
                "max_period": str(df["period_dt"].max().date()),
            }
        ]
    )

    return {
        "metrics": metrics,
        "predictions": preds,
        "weights": weights,
        "summary": summary,
        "train_df": train_df,
        "val_df": val_df,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Train exp_001 baseline rent growth models")
    parser.add_argument("--apt-path", type=Path, required=True)
    parser.add_argument("--econ-path", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--train-end-date", type=str, default="2024-12-31")
    args = parser.parse_args()

    args.artifacts_dir.mkdir(parents=True, exist_ok=True)

    modeling_df = build_modeling_table(args.apt_path, args.econ_path)
    results = evaluate_split(modeling_df, args.train_end_date)

    modeling_df.to_csv(args.artifacts_dir / "modeling_table.csv", index=False)
    results["summary"].to_csv(args.artifacts_dir / "dataset_summary.csv", index=False)
    results["predictions"].to_csv(args.artifacts_dir / "predictions.csv", index=False)
    results["weights"].to_csv(args.artifacts_dir / "feature_weights.csv", index=False)

    with (args.artifacts_dir / "metrics.json").open("w", encoding="utf-8") as fp:
        json.dump(results["metrics"], fp, indent=2)

    print(f"Wrote artifacts to: {args.artifacts_dir}")
    print(json.dumps(results["metrics"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
