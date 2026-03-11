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

## Environment Rule

- Run experiments from the project-managed `uv` environment.
- Use `uv sync --all-groups` after dependency changes.
- Do not install notebook or experiment libraries ad hoc outside `pyproject.toml`.


## Scaffold a new experiment

Scaffold new experiments so every new `exp_*` folder includes the standard files:

```bash
mkdir -p experiments/exp_003_transit_features_v1/{src,artifacts}
```

Then add:
- `experiments/exp_003_transit_features_v1/README.md`
- `experiments/exp_003_transit_features_v1/METHODOLOGY.md`
- `experiments/exp_003_transit_features_v1/run_spec.yaml`
