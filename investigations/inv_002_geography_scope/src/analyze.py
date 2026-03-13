from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from investigations.plotting import (
    COLOR_BLUE,
    COLOR_GOLD,
    COLOR_NAVY,
    COLOR_RED,
    COLOR_SLATE,
    COLOR_TEAL,
    apply_plot_style,
    save_figure,
    style_axis,
)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DEFAULT_APT_PATH = REPO_ROOT / "ingestion/tmp/entities/apartment_market.csv"
DEFAULT_GEO_PATH = REPO_ROOT / "ingestion/tmp/entities/geographic.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "investigations/inv_002_geography_scope/artifacts"
PLOTS_DIRNAME = "plots"
TARGET_COLUMN = "rent_growth_1m"

EXPERIMENT_SPECS = [
    {
        "experiment_key": "exp_001",
        "label": "exp_001 baseline mixed surface",
        "predictions_path": REPO_ROOT / "experiments/exp_001_baseline_rent_growth/artifacts/predictions.csv",
        "metrics_path": REPO_ROOT / "experiments/exp_001_baseline_rent_growth/artifacts/metrics.json",
        "surface_note": "mixed_national_surface",
    },
    {
        "experiment_key": "exp_002",
        "label": "exp_002 Philadelphia consistent baseline",
        "predictions_path": REPO_ROOT / "experiments/exp_002_philly_consistent_baseline/artifacts/predictions_holdout.csv",
        "metrics_path": REPO_ROOT / "experiments/exp_002_philly_consistent_baseline/artifacts/metrics.json",
        "surface_note": "philly_city_plus_msa_context",
    },
    {
        "experiment_key": "exp_003",
        "label": "exp_003 Philadelphia regional ZIP panel",
        "predictions_path": REPO_ROOT / "experiments/exp_003_philly_region_zip_panel/artifacts/predictions_holdout.csv",
        "metrics_path": REPO_ROOT / "experiments/exp_003_philly_region_zip_panel/artifacts/metrics.json",
        "surface_note": "philly_regional_zip_surface",
    },
]

LOCAL_DECISION_RELEVANCE = {
    "zori_zip": 5,
    "zori_city": 3,
    "zori_msa": 2,
    "zori_country": 1,
}

RECOMMENDATION_TEXT = {
    "zori_zip": "Highest local relevance. Keep as the main candidate surface for neighborhood questions, but treat it as noisy and require stronger feature discipline.",
    "zori_city": "Best controlled baseline surface. Use it to test hypotheses cleanly before trusting more granular predictions.",
    "zori_msa": "Best stabilizing benchmark. Useful for macro context and sanity checks, not for localized action.",
    "zori_country": "Reference only. Too coarse for the project decision surface.",
}


def load_panel(apt_path: Path, geo_path: Path) -> pd.DataFrame:
    apt = pd.read_csv(apt_path, low_memory=False)
    apt["period"] = pd.to_datetime(apt["period"], errors="coerce")
    geo = pd.read_csv(geo_path)
    panel = apt.merge(
        geo[["entity_id", "geography_type", "name"]],
        left_on="geography_entity_id",
        right_on="entity_id",
        how="left",
        suffixes=("", "_geo"),
    )
    panel = panel.rename(columns={"name": "geography_name"})
    panel = panel.loc[panel["period"].notna() & panel[TARGET_COLUMN].notna()].copy()
    panel = panel.sort_values(["geography_entity_id", "period"]).reset_index(drop=True)
    return panel


def build_panel_balance(panel: pd.DataFrame) -> pd.DataFrame:
    by_geo = (
        panel.groupby(["geography_entity_id", "geography_type", "geography_name"], dropna=False)
        .agg(
            row_count=("period", "size"),
            unique_period_count=("period", "nunique"),
            min_period=("period", "min"),
            max_period=("period", "max"),
            target_std=(TARGET_COLUMN, "std"),
            mean_abs_target=(TARGET_COLUMN, lambda s: float(s.abs().mean())),
        )
        .reset_index()
    )
    by_geo["history_months"] = (
        (by_geo["max_period"].dt.year - by_geo["min_period"].dt.year) * 12
        + (by_geo["max_period"].dt.month - by_geo["min_period"].dt.month)
        + 1
    )
    by_geo["coverage_ratio"] = by_geo["unique_period_count"] / by_geo["history_months"]
    by_geo["missing_internal_months"] = by_geo["history_months"] - by_geo["unique_period_count"]
    return by_geo.sort_values(["geography_type", "row_count"], ascending=[True, False])


def build_surface_panel_summary(by_geo: pd.DataFrame) -> pd.DataFrame:
    summary = (
        by_geo.groupby("geography_type", dropna=False)
        .agg(
            geo_count=("geography_entity_id", "size"),
            median_history_months=("history_months", "median"),
            median_unique_period_count=("unique_period_count", "median"),
            median_coverage_ratio=("coverage_ratio", "median"),
            median_target_std=("target_std", "median"),
            p90_target_std=("target_std", lambda s: float(s.quantile(0.9))),
            median_mean_abs_target=("mean_abs_target", "median"),
            mean_missing_internal_months=("missing_internal_months", "mean"),
        )
        .reset_index()
        .sort_values("geo_count", ascending=False)
    )
    return summary


def load_predictions(path: Path, geo_lookup: pd.DataFrame) -> pd.DataFrame:
    predictions = pd.read_csv(path)
    predictions["period"] = pd.to_datetime(predictions["period"], errors="coerce")
    predictions = predictions.merge(
        geo_lookup,
        left_on="geography_entity_id",
        right_on="entity_id",
        how="left",
        suffixes=("", "_geo"),
    )
    predictions["naive_abs_error"] = (predictions["y_true"] - predictions["y_pred_naive_lag1"]).abs()
    predictions["linear_abs_error"] = (predictions["y_true"] - predictions["y_pred_linear"]).abs()
    predictions["linear_gain_vs_naive"] = predictions["naive_abs_error"] - predictions["linear_abs_error"]
    return predictions


def build_experiment_error_summary(geo_lookup: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    overall_rows: list[dict[str, float | int | str]] = []
    by_type_rows: list[dict[str, float | int | str]] = []
    by_geo_frames: list[pd.DataFrame] = []

    for spec in EXPERIMENT_SPECS:
        predictions = load_predictions(spec["predictions_path"], geo_lookup)
        metrics = json.loads(spec["metrics_path"].read_text())
        holdout = metrics.get("holdout", {})
        split = holdout.get("split", {})

        overall_rows.append(
            {
                "experiment_key": spec["experiment_key"],
                "experiment_label": spec["label"],
                "surface_note": spec["surface_note"],
                "holdout_rows": int(len(predictions)),
                "holdout_geo_count": int(predictions["geography_entity_id"].nunique()),
                "y_true_std": float(predictions["y_true"].std(ddof=1)),
                "naive_mae": float(predictions["naive_abs_error"].mean()),
                "linear_mae": float(predictions["linear_abs_error"].mean()),
                "mae_gain_vs_naive": float(predictions["linear_gain_vs_naive"].mean()),
                "relative_gain_pct": float(predictions["linear_gain_vs_naive"].mean() / predictions["naive_abs_error"].mean())
                if float(predictions["naive_abs_error"].mean()) > 0
                else np.nan,
                "normalized_linear_mae": float(predictions["linear_abs_error"].mean() / predictions["y_true"].std(ddof=1))
                if float(predictions["y_true"].std(ddof=1)) > 0
                else np.nan,
                "normalized_naive_mae": float(predictions["naive_abs_error"].mean() / predictions["y_true"].std(ddof=1))
                if float(predictions["y_true"].std(ddof=1)) > 0
                else np.nan,
                "train_rows": split.get("train_rows"),
                "validation_rows": split.get("validation_rows"),
            }
        )

        grouped = (
            predictions.groupby("geography_type", dropna=False)
            .agg(
                holdout_rows=("entity_id", "size"),
                holdout_geo_count=("geography_entity_id", "nunique"),
                y_true_std=("y_true", "std"),
                naive_mae=("naive_abs_error", "mean"),
                linear_mae=("linear_abs_error", "mean"),
                mae_gain_vs_naive=("linear_gain_vs_naive", "mean"),
            )
            .reset_index()
        )
        grouped.insert(0, "experiment_key", spec["experiment_key"])
        grouped.insert(1, "experiment_label", spec["label"])
        grouped["relative_gain_pct"] = grouped["mae_gain_vs_naive"] / grouped["naive_mae"]
        grouped["normalized_linear_mae"] = grouped["linear_mae"] / grouped["y_true_std"]
        grouped["normalized_naive_mae"] = grouped["naive_mae"] / grouped["y_true_std"]
        by_type_rows.extend(grouped.to_dict(orient="records"))

        by_geo = (
            predictions.groupby(["geography_entity_id", "geography_type", "name"], dropna=False)
            .agg(
                holdout_rows=("entity_id", "size"),
                y_true_std=("y_true", "std"),
                naive_mae=("naive_abs_error", "mean"),
                linear_mae=("linear_abs_error", "mean"),
                mae_gain_vs_naive=("linear_gain_vs_naive", "mean"),
            )
            .reset_index()
        )
        by_geo.insert(0, "experiment_key", spec["experiment_key"])
        by_geo.insert(1, "experiment_label", spec["label"])
        by_geo["relative_gain_pct"] = by_geo["mae_gain_vs_naive"] / by_geo["naive_mae"]
        by_geo["normalized_linear_mae"] = by_geo["linear_mae"] / by_geo["y_true_std"]
        by_geo["normalized_naive_mae"] = by_geo["naive_mae"] / by_geo["y_true_std"]
        by_geo_frames.append(by_geo)

    overall = pd.DataFrame(overall_rows).sort_values("experiment_key")
    by_type = pd.DataFrame(by_type_rows).sort_values(["experiment_key", "geography_type"])
    by_geo = pd.concat(by_geo_frames, ignore_index=True).sort_values(
        ["experiment_key", "linear_mae", "geography_entity_id"],
        ascending=[True, False, True],
    )
    return overall, by_type, by_geo


def build_surface_recommendation(
    surface_panel_summary: pd.DataFrame,
    experiment_error_by_type: pd.DataFrame,
) -> pd.DataFrame:
    error_best = (
        experiment_error_by_type.sort_values(["geography_type", "normalized_linear_mae", "linear_mae"])
        .groupby("geography_type", as_index=False)
        .first()
        .rename(
            columns={
                "experiment_key": "best_evidence_experiment_key",
                "experiment_label": "best_evidence_experiment_label",
                "linear_mae": "best_linear_mae",
                "naive_mae": "best_naive_mae",
                "mae_gain_vs_naive": "best_mae_gain_vs_naive",
                "normalized_linear_mae": "best_normalized_linear_mae",
                "relative_gain_pct": "best_relative_gain_pct",
            }
        )
    )

    recommendation = surface_panel_summary.merge(error_best, on="geography_type", how="left")

    max_target_std = float(recommendation["median_target_std"].max())
    max_missing = float(recommendation["mean_missing_internal_months"].max())
    max_history = float(recommendation["median_history_months"].max())

    recommendation["stability_score"] = (
        5 - 4 * (recommendation["median_target_std"] / max_target_std)
    ).clip(lower=1, upper=5)
    recommendation["panel_depth_score"] = (
        1 + 4 * (recommendation["median_history_months"] / max_history)
    ).clip(lower=1, upper=5)
    recommendation["panel_completeness_score"] = (
        5 - 4 * (recommendation["mean_missing_internal_months"] / max_missing)
        if max_missing > 0
        else 5.0
    )
    recommendation["panel_completeness_score"] = recommendation["panel_completeness_score"].clip(lower=1, upper=5)
    recommendation["local_decision_relevance"] = recommendation["geography_type"].map(LOCAL_DECISION_RELEVANCE).fillna(1)
    recommendation["current_model_signal_score"] = (
        1 + 4 * recommendation["best_relative_gain_pct"].fillna(0).clip(lower=0)
    ).clip(lower=1, upper=5)
    recommendation["modeling_readiness_score"] = (
        0.35 * recommendation["stability_score"]
        + 0.25 * recommendation["panel_depth_score"]
        + 0.20 * recommendation["panel_completeness_score"]
        + 0.20 * recommendation["current_model_signal_score"]
    )
    recommendation["research_value_score"] = (
        0.55 * recommendation["local_decision_relevance"]
        + 0.45 * recommendation["current_model_signal_score"]
    )

    recommendation["recommended_role"] = recommendation["geography_type"].map(
        {
            "zori_city": "baseline_surface",
            "zori_zip": "candidate_surface",
            "zori_msa": "benchmark_surface",
            "zori_country": "reference_only",
        }
    ).fillna("reference_only")
    recommendation["recommendation"] = recommendation["geography_type"].map(RECOMMENDATION_TEXT).fillna(
        "Use as a low-priority reference surface."
    )

    return recommendation.sort_values(["research_value_score", "modeling_readiness_score"], ascending=[False, False])


def plot_surface_volatility(by_geo: pd.DataFrame, output_path: Path) -> None:
    ordered = ["zori_msa", "zori_city", "zori_zip"]
    data = [by_geo.loc[by_geo["geography_type"] == geography_type, "target_std"].dropna() for geography_type in ordered]
    labels = ["MSA", "City", "ZIP"]

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    box = ax.boxplot(
        data,
        patch_artist=True,
        tick_labels=labels,
        medianprops={"color": "white", "linewidth": 1.4},
    )
    for patch, color in zip(box["boxes"], [COLOR_TEAL, COLOR_BLUE, COLOR_RED], strict=False):
        patch.set_facecolor(color)
        patch.set_alpha(0.9)
    style_axis(ax)
    ax.set_title("Target Volatility by Geography Surface")
    ax.set_ylabel("Per-geography standard deviation of 1-month rent growth")
    save_figure(fig, output_path)


def plot_surface_history(by_geo: pd.DataFrame, output_path: Path) -> None:
    ordered = ["zori_msa", "zori_city", "zori_zip"]
    data = [by_geo.loc[by_geo["geography_type"] == geography_type, "history_months"].dropna() for geography_type in ordered]
    labels = ["MSA", "City", "ZIP"]

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    box = ax.boxplot(
        data,
        patch_artist=True,
        tick_labels=labels,
        medianprops={"color": "white", "linewidth": 1.4},
    )
    for patch, color in zip(box["boxes"], [COLOR_TEAL, COLOR_BLUE, COLOR_RED], strict=False):
        patch.set_facecolor(color)
        patch.set_alpha(0.9)
    style_axis(ax)
    ax.set_title("Panel History by Geography Surface")
    ax.set_ylabel("Observed months per geography")
    save_figure(fig, output_path)


def plot_experiment_holdout_mae(experiment_summary: pd.DataFrame, output_path: Path) -> None:
    labels = experiment_summary["experiment_key"].tolist()
    positions = np.arange(len(labels))
    width = 0.34

    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    ax.bar(
        positions - width / 2,
        experiment_summary["naive_mae"],
        width=width,
        color=COLOR_SLATE,
        label="Naive lag-1 MAE",
    )
    ax.bar(
        positions + width / 2,
        experiment_summary["linear_mae"],
        width=width,
        color=COLOR_NAVY,
        label="Linear model MAE",
    )
    style_axis(ax)
    ax.set_title("Holdout Error by Experiment Surface")
    ax.set_ylabel("Mean absolute error")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.legend(frameon=False, ncols=2, loc="upper right")
    save_figure(fig, output_path)


def plot_surface_tradeoff(recommendation: pd.DataFrame, output_path: Path) -> None:
    label_map = {"zori_zip": "ZIP", "zori_city": "City", "zori_msa": "MSA", "zori_country": "Country"}
    color_map = {
        "baseline_surface": COLOR_BLUE,
        "candidate_surface": COLOR_RED,
        "benchmark_surface": COLOR_TEAL,
        "reference_only": COLOR_GOLD,
    }

    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    for _, row in recommendation.iterrows():
        ax.scatter(
            row["median_target_std"],
            row["modeling_readiness_score"],
            s=row["geo_count"] * 1.8,
            color=color_map.get(row["recommended_role"], COLOR_SLATE),
            alpha=0.85,
            edgecolor="white",
            linewidth=0.8,
        )
        ax.annotate(
            label_map.get(row["geography_type"], row["geography_type"]),
            (row["median_target_std"], row["modeling_readiness_score"]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=9,
        )
    style_axis(ax)
    ax.set_title("Surface Tradeoff: Volatility vs Modeling Readiness")
    ax.set_xlabel("Median per-geography target volatility")
    ax.set_ylabel("Heuristic modeling readiness score")
    save_figure(fig, output_path)


def plot_error_concentration(by_geo_errors: pd.DataFrame, output_path: Path) -> None:
    filtered = by_geo_errors.loc[by_geo_errors["experiment_key"].isin(["exp_001", "exp_003"])].copy()
    filtered = filtered.sort_values("linear_mae", ascending=False).groupby("experiment_key").head(10)
    filtered["label"] = filtered["name"].fillna(filtered["geography_entity_id"])
    filtered["display"] = filtered["experiment_key"] + " | " + filtered["label"]
    filtered = filtered.sort_values("linear_mae", ascending=True)

    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    ax.barh(filtered["display"], filtered["linear_mae"], color=COLOR_NAVY, label="Linear model MAE")
    ax.barh(filtered["display"], filtered["naive_mae"], color=COLOR_SLATE, alpha=0.45, label="Naive lag-1 MAE")
    style_axis(ax, x_grid=True, y_grid=False)
    ax.set_title("Worst Holdout Error Concentration by Geography")
    ax.set_xlabel("Mean absolute error")
    ax.legend(frameon=False, loc="lower right")
    save_figure(fig, output_path)


def main(
    apt_path: Path = DEFAULT_APT_PATH,
    geo_path: Path = DEFAULT_GEO_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None:
    apply_plot_style()
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = output_dir / PLOTS_DIRNAME
    plots_dir.mkdir(parents=True, exist_ok=True)

    panel = load_panel(apt_path, geo_path)
    geo_lookup = pd.read_csv(geo_path)[["entity_id", "geography_type", "name"]]

    by_geo_panel = build_panel_balance(panel)
    surface_panel_summary = build_surface_panel_summary(by_geo_panel)
    experiment_summary, error_by_type, error_by_geo = build_experiment_error_summary(geo_lookup)
    recommendation = build_surface_recommendation(surface_panel_summary, error_by_type)

    by_geo_panel.to_csv(output_dir / "panel_balance_by_geography.csv", index=False)
    surface_panel_summary.to_csv(output_dir / "surface_panel_summary.csv", index=False)
    experiment_summary.to_csv(output_dir / "experiment_error_summary.csv", index=False)
    error_by_type.to_csv(output_dir / "experiment_error_by_geography_type.csv", index=False)
    error_by_geo.to_csv(output_dir / "error_concentration_by_geography.csv", index=False)
    recommendation.to_csv(output_dir / "surface_recommendation.csv", index=False)

    plot_surface_volatility(by_geo_panel, plots_dir / "surface_volatility_distribution.png")
    plot_surface_history(by_geo_panel, plots_dir / "surface_history_distribution.png")
    plot_experiment_holdout_mae(experiment_summary, plots_dir / "experiment_holdout_mae.png")
    plot_surface_tradeoff(recommendation, plots_dir / "surface_tradeoff_matrix.png")
    plot_error_concentration(error_by_geo, plots_dir / "error_concentration_by_geography.png")


if __name__ == "__main__":
    main()
