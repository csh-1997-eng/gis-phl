# exp_003_philly_region_zip_panel

## Purpose

This experiment moves to ZIP-level panel data in the Philadelphia regional footprint and tests the same baseline feature set on a more granular surface.

## Inputs

- `exploration/tmp/ontology/apartment_market.csv`
- `exploration/tmp/ontology/economic.csv`

## Run

```bash
uv run python experiments/exp_003_philly_region_zip_panel/src/train.py \
  --apt-path exploration/tmp/ontology/apartment_market.csv \
  --econ-path exploration/tmp/ontology/economic.csv \
  --artifacts-dir experiments/exp_003_philly_region_zip_panel/artifacts \
  --train-end-date 2024-12-31
```

## MLflow

Use `--variant` for meaningful changes to the experiment definition.

Example:

```bash
uv run python experiments/exp_003_philly_region_zip_panel/src/train.py \
  --apt-path exploration/tmp/ontology/apartment_market.csv \
  --econ-path exploration/tmp/ontology/economic.csv \
  --artifacts-dir experiments/exp_003_philly_region_zip_panel/artifacts \
  --train-end-date 2024-12-31 \
  --variant v1_baseline_linear \
  --stage baseline \
  --target-name r1m_next \
  --geo-scope philly_zip_region \
  --feature-set lags_plus_econ \
  --ontology-version 2026-03-11-city-key-fix
```

## Outputs

- `artifacts/modeling_table.csv`
- `artifacts/dataset_summary.csv`
- `artifacts/predictions_holdout.csv`
- `artifacts/predictions_rolling.csv`
- `artifacts/metrics.json`
- `artifacts/feature_weights_holdout.csv`
- `artifacts/zip_panel_state_summary.csv`
