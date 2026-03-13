from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from investigations.plotting import (
    COLOR_BLUE,
    COLOR_GOLD,
    COLOR_NAVY,
    COLOR_RED,
    COLOR_TEAL,
    PALETTE,
    apply_plot_style,
)
import matplotlib.pyplot as plt


DEFAULT_APT_PATH = REPO_ROOT / "ingestion/tmp/entities/apartment_market.csv"
DEFAULT_GEO_PATH = REPO_ROOT / "ingestion/tmp/entities/geographic.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "investigations/inv_001_target_behavior/artifacts"
TARGET_COLUMN = "rent_growth_1m"
HORIZONS = (1, 3, 6, 12)
EARLY_PERIOD_MAX_YEAR = 2019
SHOCK_PERIOD_MAX_YEAR = 2022


def load_panel(apt_path: Path, geo_path: Path) -> pd.DataFrame:
    apt = pd.read_csv(apt_path, low_memory=False)
    period_text = apt["period"].astype("string")
    date_mask = period_text.str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    apt["period"] = pd.NaT
    apt.loc[date_mask.fillna(False), "period"] = pd.to_datetime(
        period_text.loc[date_mask.fillna(False)],
        format="%Y-%m-%d",
        errors="coerce",
    )
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
    panel["period_month"] = panel["period"].dt.month
    panel["period_year"] = panel["period"].dt.year
    panel = panel.sort_values(["geography_entity_id", "period"]).reset_index(drop=True)
    return panel


def summarize_target(panel: pd.DataFrame) -> pd.DataFrame:
    summary = (
        panel.groupby("geography_type", dropna=False)
        .agg(
            row_count=(TARGET_COLUMN, "size"),
            geo_count=("geography_entity_id", "nunique"),
            mean_target=(TARGET_COLUMN, "mean"),
            std_target=(TARGET_COLUMN, "std"),
            median_target=(TARGET_COLUMN, "median"),
            mean_abs_target=(TARGET_COLUMN, lambda s: float(s.abs().mean())),
            p05_target=(TARGET_COLUMN, lambda s: float(s.quantile(0.05))),
            p95_target=(TARGET_COLUMN, lambda s: float(s.quantile(0.95))),
        )
        .reset_index()
        .sort_values(["row_count", "geography_type"], ascending=[False, True])
    )
    return summary


def variance_decomposition(panel: pd.DataFrame) -> pd.DataFrame:
    pieces: list[dict[str, float | str]] = []
    for geography_type, group in panel.groupby("geography_type", dropna=False):
        geo_means = group.groupby("geography_entity_id")[TARGET_COLUMN].mean()
        within = group[TARGET_COLUMN] - group.groupby("geography_entity_id")[TARGET_COLUMN].transform("mean")
        total_var = float(group[TARGET_COLUMN].var(ddof=1))
        between_var = float(geo_means.var(ddof=1)) if len(geo_means) > 1 else 0.0
        within_var = float(within.var(ddof=1))
        pieces.append(
            {
                "geography_type": geography_type,
                "row_count": int(len(group)),
                "geo_count": int(group["geography_entity_id"].nunique()),
                "total_variance": total_var,
                "between_geography_variance": between_var,
                "within_geography_variance": within_var,
                "between_share": (between_var / total_var) if total_var else np.nan,
                "within_share": (within_var / total_var) if total_var else np.nan,
            }
        )
    return pd.DataFrame(pieces).sort_values("row_count", ascending=False)


def autocorrelation_summary(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for geography_type, group in panel.groupby("geography_type", dropna=False):
        for horizon in HORIZONS:
            samples = 0
            correlations: list[float] = []
            naive_errors: list[float] = []
            for _, geo_group in group.groupby("geography_entity_id"):
                current = geo_group[TARGET_COLUMN]
                lagged = current.shift(horizon)
                aligned = pd.DataFrame({"current": current, "lagged": lagged}).dropna()
                if aligned.empty:
                    continue
                samples += int(len(aligned))
                if len(aligned) >= 2:
                    corr = aligned["current"].corr(aligned["lagged"])
                    if pd.notna(corr):
                        correlations.append(float(corr))
                naive_errors.extend((aligned["current"] - aligned["lagged"]).abs().tolist())
            rows.append(
                {
                    "geography_type": geography_type,
                    "horizon_months": horizon,
                    "sample_count": samples,
                    "mean_series_autocorr": float(np.mean(correlations)) if correlations else np.nan,
                    "median_series_autocorr": float(np.median(correlations)) if correlations else np.nan,
                    "naive_mae_using_lag": float(np.mean(naive_errors)) if naive_errors else np.nan,
                }
            )
    return pd.DataFrame(rows).sort_values(["geography_type", "horizon_months"])


def autocorrelation_by_geography(panel: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for (geography_entity_id, geography_type, geography_name), geo_group in panel.groupby(
        ["geography_entity_id", "geography_type", "geography_name"],
        dropna=False,
    ):
        for horizon in HORIZONS:
            current = geo_group[TARGET_COLUMN]
            lagged = current.shift(horizon)
            aligned = pd.DataFrame({"current": current, "lagged": lagged}).dropna()
            if aligned.empty:
                continue
            corr = aligned["current"].corr(aligned["lagged"]) if len(aligned) >= 2 else np.nan
            rows.append(
                {
                    "geography_entity_id": geography_entity_id,
                    "geography_type": geography_type,
                    "geography_name": geography_name,
                    "horizon_months": horizon,
                    "sample_count": int(len(aligned)),
                    "autocorr": float(corr) if pd.notna(corr) else np.nan,
                    "naive_mae_using_lag": float((aligned["current"] - aligned["lagged"]).abs().mean()),
                    "min_period": str(geo_group["period"].min().date()),
                    "max_period": str(geo_group["period"].max().date()),
                    "target_std": float(geo_group[TARGET_COLUMN].std(ddof=1))
                    if len(geo_group) > 1
                    else np.nan,
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["geography_type", "horizon_months", "sample_count", "geography_entity_id"],
        ascending=[True, True, False, True],
    )


def seasonality_summary(panel: pd.DataFrame) -> pd.DataFrame:
    return (
        panel.groupby(["geography_type", "period_month"], dropna=False)
        .agg(
            row_count=(TARGET_COLUMN, "size"),
            mean_target=(TARGET_COLUMN, "mean"),
            std_target=(TARGET_COLUMN, "std"),
            mean_abs_target=(TARGET_COLUMN, lambda s: float(s.abs().mean())),
        )
        .reset_index()
        .sort_values(["geography_type", "period_month"])
    )


def panel_balance(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    grouped = panel.groupby(["geography_entity_id", "geography_type", "geography_name"], dropna=False)
    by_geo = (
        grouped.agg(
            row_count=("period", "size"),
            unique_period_count=("period", "nunique"),
            min_period=("period", "min"),
            max_period=("period", "max"),
            target_std=(TARGET_COLUMN, "std"),
        )
        .reset_index()
        .sort_values(["geography_type", "row_count"], ascending=[True, False])
    )
    by_geo["expected_months"] = (
        (by_geo["max_period"].dt.year - by_geo["min_period"].dt.year) * 12
        + (by_geo["max_period"].dt.month - by_geo["min_period"].dt.month)
        + 1
    )
    by_geo["duplicate_period_rows"] = by_geo["row_count"] - by_geo["unique_period_count"]
    by_geo["coverage_ratio"] = by_geo["unique_period_count"] / by_geo["expected_months"]
    by_geo["missing_internal_months"] = by_geo["expected_months"] - by_geo["unique_period_count"]

    summary = (
        by_geo.groupby("geography_type", dropna=False)
        .agg(
            geo_count=("geography_entity_id", "size"),
            median_row_count=("row_count", "median"),
            median_unique_period_count=("unique_period_count", "median"),
            min_row_count=("row_count", "min"),
            max_row_count=("row_count", "max"),
            median_coverage_ratio=("coverage_ratio", "median"),
            mean_missing_internal_months=("missing_internal_months", "mean"),
            total_duplicate_period_rows=("duplicate_period_rows", "sum"),
            median_target_std=("target_std", "median"),
        )
        .reset_index()
        .sort_values("geo_count", ascending=False)
    )
    return by_geo, summary


def duplicate_geography_periods(panel: pd.DataFrame) -> pd.DataFrame:
    return (
        panel.groupby(["geography_entity_id", "geography_type", "geography_name", "period"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .loc[lambda df: df["row_count"] > 1]
        .sort_values(["row_count", "geography_type", "geography_entity_id", "period"], ascending=[False, True, True, True])
    )


def yearly_summary(panel: pd.DataFrame) -> pd.DataFrame:
    return (
        panel.groupby(["geography_type", "period_year"], dropna=False)
        .agg(
            row_count=(TARGET_COLUMN, "size"),
            mean_target=(TARGET_COLUMN, "mean"),
            std_target=(TARGET_COLUMN, "std"),
            mean_abs_target=(TARGET_COLUMN, lambda s: float(s.abs().mean())),
        )
        .reset_index()
        .sort_values(["geography_type", "period_year"])
    )


def _period_regime(period_year: int) -> str:
    if period_year <= EARLY_PERIOD_MAX_YEAR:
        return "pre_2020"
    if period_year <= SHOCK_PERIOD_MAX_YEAR:
        return "shock_2020_2022"
    return "recent_2023_plus"


def structural_shift(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    framed = panel.copy()
    framed["regime"] = framed["period_year"].map(_period_regime)

    by_geo = (
        framed.groupby(
            ["geography_entity_id", "geography_type", "geography_name", "regime"],
            dropna=False,
        )
        .agg(
            row_count=(TARGET_COLUMN, "size"),
            mean_target=(TARGET_COLUMN, "mean"),
            std_target=(TARGET_COLUMN, "std"),
            mean_abs_target=(TARGET_COLUMN, lambda s: float(s.abs().mean())),
        )
        .reset_index()
    )

    wide = by_geo.pivot_table(
        index=["geography_entity_id", "geography_type", "geography_name"],
        columns="regime",
        values=["row_count", "mean_target", "std_target", "mean_abs_target"],
        aggfunc="first",
    )
    wide.columns = [f"{metric}_{regime}" for metric, regime in wide.columns]
    wide = wide.reset_index()

    for regime in ("pre_2020", "shock_2020_2022", "recent_2023_plus"):
        row_col = f"row_count_{regime}"
        if row_col not in wide.columns:
            wide[row_col] = np.nan
        mean_col = f"mean_target_{regime}"
        if mean_col not in wide.columns:
            wide[mean_col] = np.nan

    wide["mean_shift_shock_vs_pre"] = (
        wide["mean_target_shock_2020_2022"] - wide["mean_target_pre_2020"]
    )
    wide["mean_shift_recent_vs_pre"] = (
        wide["mean_target_recent_2023_plus"] - wide["mean_target_pre_2020"]
    )
    wide["mean_shift_recent_vs_shock"] = (
        wide["mean_target_recent_2023_plus"] - wide["mean_target_shock_2020_2022"]
    )
    wide["max_abs_mean_shift"] = wide[
        [
            "mean_shift_shock_vs_pre",
            "mean_shift_recent_vs_pre",
            "mean_shift_recent_vs_shock",
        ]
    ].abs().max(axis=1)

    summary = (
        wide.groupby("geography_type", dropna=False)
        .agg(
            geo_count=("geography_entity_id", "size"),
            median_shift_shock_vs_pre=("mean_shift_shock_vs_pre", "median"),
            median_shift_recent_vs_pre=("mean_shift_recent_vs_pre", "median"),
            median_shift_recent_vs_shock=("mean_shift_recent_vs_shock", "median"),
            median_max_abs_mean_shift=("max_abs_mean_shift", "median"),
            p90_max_abs_mean_shift=("max_abs_mean_shift", lambda s: float(s.quantile(0.9))),
        )
        .reset_index()
        .sort_values("geo_count", ascending=False)
    )
    return wide.sort_values(
        ["geography_type", "max_abs_mean_shift", "geography_entity_id"],
        ascending=[True, False, True],
    ), summary


def _save_target_volatility_plot(summary: pd.DataFrame, plots_dir: Path) -> None:
    apply_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].bar(summary["geography_type"], summary["std_target"], color=COLOR_BLUE, width=0.65)
    axes[0].set_title("Target Volatility By Geography Type")
    axes[0].set_ylabel("std(rent_growth_1m)")
    axes[0].tick_params(axis="x", rotation=20)
    axes[0].grid(axis="y")
    axes[0].set_axisbelow(True)

    axes[1].bar(summary["geography_type"], summary["mean_abs_target"], color=COLOR_GOLD, width=0.65)
    axes[1].set_title("Mean Absolute Target By Geography Type")
    axes[1].set_ylabel("mean(|rent_growth_1m|)")
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].grid(axis="y")
    axes[1].set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(plots_dir / "target_volatility_by_geography_type.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _save_naive_mae_plot(autocorr: pd.DataFrame, plots_dir: Path) -> None:
    apply_plot_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    for idx, (geography_type, group) in enumerate(autocorr.groupby("geography_type", dropna=False)):
        ax.plot(
            group["horizon_months"],
            group["naive_mae_using_lag"],
            marker="o",
            linewidth=2,
            color=PALETTE[idx % len(PALETTE)],
            label=geography_type,
        )
    ax.set_title("Naive Lag Error By Horizon")
    ax.set_xlabel("Lag horizon (months)")
    ax.set_ylabel("MAE using lagged target")
    ax.legend(frameon=False)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(plots_dir / "naive_mae_by_horizon.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _save_autocorrelation_plot(autocorr: pd.DataFrame, plots_dir: Path) -> None:
    apply_plot_style()
    fig, ax = plt.subplots(figsize=(8, 5))
    for idx, (geography_type, group) in enumerate(autocorr.groupby("geography_type", dropna=False)):
        ax.plot(
            group["horizon_months"],
            group["mean_series_autocorr"],
            marker="o",
            linewidth=2,
            color=PALETTE[idx % len(PALETTE)],
            label=geography_type,
        )
    ax.axhline(0.0, color="black", linewidth=1, alpha=0.4)
    ax.set_title("Mean Series Autocorrelation By Horizon")
    ax.set_xlabel("Lag horizon (months)")
    ax.set_ylabel("Mean per-series autocorrelation")
    ax.legend(frameon=False)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(plots_dir / "autocorrelation_by_horizon.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _save_yearly_mean_target_plot(yearly: pd.DataFrame, plots_dir: Path) -> None:
    apply_plot_style()
    fig, ax = plt.subplots(figsize=(10, 5))
    for idx, (geography_type, group) in enumerate(yearly.groupby("geography_type", dropna=False)):
        ax.plot(
            group["period_year"],
            group["mean_target"],
            marker="o",
            linewidth=2,
            color=PALETTE[idx % len(PALETTE)],
            label=geography_type,
        )
    ax.axhline(0.0, color="black", linewidth=1, alpha=0.4)
    ax.set_title("Yearly Mean Target By Geography Type")
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean rent_growth_1m")
    ax.legend(frameon=False)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(plots_dir / "yearly_mean_target_by_geography_type.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def _save_structural_shift_plot(summary: pd.DataFrame, plots_dir: Path) -> None:
    apply_plot_style()
    x = np.arange(len(summary))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(
        x - width,
        summary["median_shift_shock_vs_pre"],
        width=width,
        label="shock vs pre",
        color=COLOR_TEAL,
    )
    ax.bar(
        x,
        summary["median_shift_recent_vs_pre"],
        width=width,
        label="recent vs pre",
        color=COLOR_GOLD,
    )
    ax.bar(
        x + width,
        summary["median_shift_recent_vs_shock"],
        width=width,
        label="recent vs shock",
        color=COLOR_RED,
    )
    ax.axhline(0.0, color="black", linewidth=1, alpha=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(summary["geography_type"], rotation=20)
    ax.set_title("Median Structural Shift By Geography Type")
    ax.set_ylabel("Shift in mean rent_growth_1m")
    ax.legend(frameon=False)
    ax.grid(axis="y")
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(plots_dir / "structural_shift_summary.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_plots(
    *,
    target_summary: pd.DataFrame,
    autocorr: pd.DataFrame,
    yearly: pd.DataFrame,
    structural_summary: pd.DataFrame,
    plots_dir: Path,
) -> None:
    plots_dir.mkdir(parents=True, exist_ok=True)
    _save_target_volatility_plot(target_summary, plots_dir)
    _save_naive_mae_plot(autocorr, plots_dir)
    _save_autocorrelation_plot(autocorr, plots_dir)
    _save_yearly_mean_target_plot(yearly, plots_dir)
    _save_structural_shift_plot(structural_summary, plots_dir)


def main() -> None:
    output_dir = DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    plots_dir = output_dir / "plots"

    panel = load_panel(DEFAULT_APT_PATH, DEFAULT_GEO_PATH)
    target_summary = summarize_target(panel)
    variance = variance_decomposition(panel)
    autocorr = autocorrelation_summary(panel)
    autocorr_by_geo = autocorrelation_by_geography(panel)
    seasonality = seasonality_summary(panel)
    panel_by_geo, panel_summary = panel_balance(panel)
    duplicates = duplicate_geography_periods(panel)
    structural_by_geo, structural_summary = structural_shift(panel)
    yearly = yearly_summary(panel)

    target_summary.to_csv(output_dir / "target_summary_by_geography_type.csv", index=False)
    variance.to_csv(output_dir / "variance_decomposition.csv", index=False)
    autocorr.to_csv(output_dir / "autocorrelation_summary.csv", index=False)
    autocorr_by_geo.to_csv(output_dir / "autocorrelation_by_geography.csv", index=False)
    autocorr.rename(
        columns={"naive_mae_using_lag": "naive_mae"},
    ).to_csv(output_dir / "naive_strength_by_horizon.csv", index=False)
    seasonality.to_csv(output_dir / "seasonality_by_month.csv", index=False)
    panel_by_geo.to_csv(output_dir / "panel_balance_by_geography.csv", index=False)
    panel_summary.to_csv(output_dir / "panel_balance_summary.csv", index=False)
    duplicates.to_csv(output_dir / "duplicate_geography_periods.csv", index=False)
    structural_by_geo.to_csv(output_dir / "structural_shift_by_geography.csv", index=False)
    structural_summary.to_csv(output_dir / "structural_shift_summary.csv", index=False)
    yearly.to_csv(output_dir / "yearly_target_summary.csv", index=False)
    write_plots(
        target_summary=target_summary,
        autocorr=autocorr,
        yearly=yearly,
        structural_summary=structural_summary,
        plots_dir=plots_dir,
    )

    print(f"Wrote investigation outputs to: {output_dir.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
