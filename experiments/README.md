# Experiments

Each experiment should live in its own subfolder with:
- objective
- data slice/version
- feature set
- model/training config
- structured run spec (`run_spec.yaml`)
- metrics and artifacts
- methodology writeup (`METHODOLOGY.md`)
- conclusions and next step

## MLflow Tracking

- Training scripts default to a local MLflow file store at `experiments/mlruns/`.
- Override the backend by setting `MLFLOW_TRACKING_URI`.
- Each run logs:
  - the experiment `run_spec.yaml`
  - flattened params and metrics
  - the same local CSV/JSON artifacts already written under `artifacts/`
- Opt out for a run with `--no-mlflow`.
- Run naming discipline:
  - keep the experiment key stable
  - use `--variant` for meaningful iteration names such as `v1_baseline_linear` or `v2_clean_city_keys`
  - use `--run-name` only when an explicit one-off override is needed
- Training scripts also tag runs with:
  - `stage`
  - `target`
  - `geo_scope`
  - `feature_set`
  - `ontology_version`

## Environment Rule

- Run experiments from the project-managed `uv` environment.
- Use `uv sync --all-groups` after dependency changes.
- Do not install notebook or experiment libraries ad hoc outside `pyproject.toml`.

## Run Order

1. [exp_001_baseline_rent_growth/README.md](exp_001_baseline_rent_growth/README.md)
2. [exp_002_philly_consistent_baseline/README.md](exp_002_philly_consistent_baseline/README.md)
3. [exp_003_philly_region_zip_panel/README.md](exp_003_philly_region_zip_panel/README.md)

These are separate experiment surfaces, not one cumulative pipeline. Run them against the same ontology entity tables when you want a clean comparison set.

## Shared Inputs

All current experiments assume:

- `ingestion/tmp/entities/apartment_market.csv`
- `ingestion/tmp/entities/economic.csv`

Build those first from the ingestion workflow.

## Quick Commands

`exp_001`

```bash
uv run python experiments/exp_001_baseline_rent_growth/src/train.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --econ-path ingestion/tmp/entities/economic.csv \
  --artifacts-dir experiments/exp_001_baseline_rent_growth/artifacts \
  --train-end-date 2024-12-31
```

`exp_002`

```bash
uv run python experiments/exp_002_philly_consistent_baseline/src/train.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --econ-path ingestion/tmp/entities/economic.csv \
  --artifacts-dir experiments/exp_002_philly_consistent_baseline/artifacts \
  --train-end-date 2024-12-31
```

`exp_003`

```bash
uv run python experiments/exp_003_philly_region_zip_panel/src/train.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --econ-path ingestion/tmp/entities/economic.csv \
  --artifacts-dir experiments/exp_003_philly_region_zip_panel/artifacts \
  --train-end-date 2024-12-31
```


## Scaffold a new experiment

Scaffold new experiments so every new `exp_*` folder includes the standard files:

```bash
mkdir -p experiments/exp_003_transit_features_v1/{src,artifacts}
```

Then add:
- `experiments/exp_003_transit_features_v1/README.md`
- `experiments/exp_003_transit_features_v1/METHODOLOGY.md`
- `experiments/exp_003_transit_features_v1/run_spec.yaml`
