# exp_002_philly_consistent_baseline

## Purpose

This experiment isolates the Philadelphia city series and asks whether the same baseline feature set behaves differently on a much narrower scope.

## Inputs

- `ingestion/tmp/entities/apartment_market.csv`
- `ingestion/tmp/entities/economic.csv`

## Run

```bash
uv run python experiments/exp_002_philly_consistent_baseline/src/train.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --econ-path ingestion/tmp/entities/economic.csv \
  --artifacts-dir experiments/exp_002_philly_consistent_baseline/artifacts \
  --train-end-date 2024-12-31
```

## MLflow

Use `--variant` for meaningful changes to the experiment definition.

Example:

```bash
uv run python experiments/exp_002_philly_consistent_baseline/src/train.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --econ-path ingestion/tmp/entities/economic.csv \
  --artifacts-dir experiments/exp_002_philly_consistent_baseline/artifacts \
  --train-end-date 2024-12-31 \
  --variant v2_clean_city_keys \
  --stage baseline \
  --target-name r1m_next \
  --geo-scope philly_city \
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
