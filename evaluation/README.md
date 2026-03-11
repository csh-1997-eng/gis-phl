# Evaluation

This folder compares results across experiments.

## How We Evaluate

- Compare all experiments on the same holdout metrics: `MAE`, `RMSE`, `directional_accuracy`, `spearman_corr`.
- Compare both baseline and learned models (`naive_lag1` vs `linear_regression`) per experiment.
- Track split metadata (`train/validation rows`, date ranges, geography count) so metric differences are interpreted in context.
- Compare rolling aggregate metrics when available to check stability, not just one cutoff.
- Compare dataset scope (`row_count`, `geo_count`) to understand if gains come from better modeling, broader data, or both.

## Why This Matters

- Keeps comparisons fair across experiment iterations.
- Prevents over-trusting a single metric or single split.
- Makes tradeoffs explicit between accuracy, robustness, and dataset coverage.

## Notebook

- `notebooks/01_experiment_comparison.ipynb`: compares `exp_001`, `exp_002`, `exp_003` metrics and dataset summaries.
- Launch notebooks from the unified project environment with `uv run jupyter lab`.
- Set `SOURCE_MODE` inside the notebook to `files`, `mlflow`, or `auto`.
- `auto` prefers the latest FINISHED MLflow run tagged for each experiment and falls back to local artifact files.

## Exports

The notebook writes CSV summaries to:

- `evaluation/tmp/notebook_exports/01_experiment_comparison/holdout_metrics_comparison.csv`
- `evaluation/tmp/notebook_exports/01_experiment_comparison/split_summary_comparison.csv`
- `evaluation/tmp/notebook_exports/01_experiment_comparison/rolling_aggregate_comparison.csv` (when available)
- `evaluation/tmp/notebook_exports/01_experiment_comparison/dataset_summary_comparison.csv` (when available)

The notebook also writes graphics:
- `evaluation/tmp/notebook_exports/01_experiment_comparison/holdout_error_bars.png`
- `evaluation/tmp/notebook_exports/01_experiment_comparison/model_gain_vs_naive.png`
- `evaluation/tmp/notebook_exports/01_experiment_comparison/dataset_scope_comparison.png`
