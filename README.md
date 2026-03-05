# gis-phl
A repository for exploring geospatial applications to help the city of Philadelphia

## Environment And Jupyter

- Notebook environment is managed in `exploration/env/` (dedicated `.venv` + named kernel).
- One-time setup:
```bash
./exploration/env/scripts/bootstrap_notebook_env.sh
```
- Launch Jupyter Lab:
```bash
cd exploration/env
make lab
```
- Rebuild/remove kernel if needed:
```bash
./exploration/env/scripts/remove_notebook_kernel.sh
./exploration/env/scripts/bootstrap_notebook_env.sh
```

## Ingestion Pipeline Commands

- Run source probes:
```bash
python ingestion/minimal_ingest.py
```
- Build ontology entity tables:
```bash
python ingestion/ontology/build_entities.py \
  --source-dir ingestion/tmp/source_samples \
  --output-dir ingestion/tmp/entities
```
- Manual cleanup (keep only ontology entity outputs in `ingestion/tmp/entities`):
```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh
```

## Experiment Baseline (exp_001)

```bash
python experiments/exp_001_baseline_rent_growth/src/train.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --econ-path ingestion/tmp/entities/economic.csv \
  --artifacts-dir experiments/exp_001_baseline_rent_growth/artifacts \
  --train-end-date 2024-12-31
```

## Evaluation (Cross-Experiment)

Open:
- `evaluation/notebooks/01_experiment_comparison.ipynb`

This notebook compares `exp_001` / `exp_002` / `exp_003` and writes CSV outputs to:
- `evaluation/tmp/notebook_exports/01_experiment_comparison/`
