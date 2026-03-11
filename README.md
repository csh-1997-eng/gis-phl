# gis-phl
A repository for exploring geospatial applications to help the city of Philadelphia

## Environment And Jupyter

- This repo uses one `uv`-managed project environment for scripts, notebooks, tests, and MLflow.
- One-time setup:
```bash
uv sync --all-groups
./scripts/install_jupyter_kernel.sh
```
- Launch Jupyter Lab from the project environment:
```bash
uv run jupyter lab
```
- Refresh the lockfile after dependency changes:
```bash
uv lock
uv sync --all-groups
```
- Reinstall/remove the kernel if needed:
```bash
./scripts/remove_jupyter_kernel.sh
./scripts/install_jupyter_kernel.sh
```
- Dependency policy:
  - Anything committed must run from the declared `pyproject.toml` + `uv.lock`.
  - Add new notebook libraries to `pyproject.toml` in the same PR that introduces them.
  - Do not rely on notebook-only `pip install` calls outside the managed project environment.

## Ingestion Pipeline Commands

- Run source probes:
```bash
uv run python ingestion/minimal_ingest.py
```
- Build ontology entity tables:
```bash
uv run python ingestion/ontology/build_entities.py \
  --source-dir ingestion/tmp/source_samples \
  --output-dir ingestion/tmp/entities
```
- Manual cleanup (keep only ontology entity outputs in `ingestion/tmp/entities`):
```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh
```

## Experiment Baseline (exp_001)

```bash
uv run python experiments/exp_001_baseline_rent_growth/src/train.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --econ-path ingestion/tmp/entities/economic.csv \
  --artifacts-dir experiments/exp_001_baseline_rent_growth/artifacts \
  --train-end-date 2024-12-31
```

MLflow notes:
- Local tracking defaults to `experiments/mlruns/`
- Override backend with `MLFLOW_TRACKING_URI`
- Disable tracking for a single run with `--no-mlflow`
- View local runs with `uv run mlflow ui --backend-store-uri experiments/mlruns`

## Evaluation (Cross-Experiment)

Open:
- `evaluation/notebooks/01_experiment_comparison.ipynb`

This notebook compares `exp_001` / `exp_002` / `exp_003`, supports file or MLflow-backed loading, and writes CSV outputs to:
- `evaluation/tmp/notebook_exports/01_experiment_comparison/`
