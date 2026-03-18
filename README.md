# gis-phl
A repository for exploring geospatial applications to help the city of Philadelphia

## Project Goal

This project studies Philadelphia rental price change, how it relates to transportation with a specific focus on trains, and how those relationships compare with broader national patterns.

This project separates predictive questions about where rents may change next from explanatory questions about which factors, including train access and infrastructure, appear to be associated with those changes.

The primary goal is to identify which areas of Philadelphia are likely to become more expensive or less expensive over time.

The secondary goal is to test whether observed rent dynamics support a stronger case for train infrastructure investment.

The standard for this repo is research quality before model complexity. Strong fundamentals, clear hypotheses, defensible evaluation, and decision relevance matter more than chasing increasingly complex methods.

## Workflow

```
                          ┌───────────────────────────────────┐
                          │            Research               │
                          │                                   │
┌──────────────┐          │  ┌────────────────┐    informs    │
│  Raw Data    │──────►   │  │ Investigations │ ──────────►   │
│  Sources     │      │   │  └────────────────┘               │      ┌────────────┐
└──────────────┘      │   │         ▲                         │      │            │
                      ▼   │         │ updates                 │      │ Evaluation │
              ┌──────────┐│         │ understanding           │      │            │
              │ Ontology ││         ▼                         │      └────────────┘
              │   Facts  │├──►┌─────────────┐─────────────────┼─────────►  ▲
              └──────────┘│   │ Experiments │                 │            │
                          │   └─────────────┘                 │   context  │
                          │                                   ├────────────┘
                          └───────────────────────────────────┘
```

| Stage | Purpose |
|---|---|
| **Ingestion** | Acquire and store raw source data by maturity layer |
| **Exploration** | Build ontology fact tables and profile dataset quality before formal research work |
| **Investigations** | Structured analysis of data behavior, coverage, and assumptions |
| **Experiments** | Reproducible model runs with explicit hypotheses and evaluation plans |
| **Evaluation** | Compare model performance against expected outcomes informed by project goals and investigation findings |

## Project Structure

- [exploration](exploration): ontology, profiling, and open-ended discovery
- [investigations](investigations): structured follow-up work that is not yet a formal experiment
- [experiments](experiments): reproducible runs with explicit hypotheses and evaluation plans
- [evaluation](evaluation): cross-experiment comparison and synthesis
- [Structuring Research Projects](docs/structuring_research_projects.md): project organization philosophy
- [Scaling Research For Teams](docs/scaling_research_for_teams.md): branch, commit, and artifact handling guidance

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
- Build ontology fact tables:
```bash
uv run python exploration/ontology/build_entities.py \
  --source-dir ingestion/tmp \
  --source-layer samples \
  --output-dir exploration/tmp/ontology
```
- Manual cleanup (keep only ontology outputs in `exploration/tmp/ontology`):
```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh
```

## Reproduce Current Work

1. Build source samples and ontology fact tables.

Use the ingestion commands above.

2. Review source and entity quality.

Start Jupyter:
```bash
uv run jupyter lab
```

Then work through:
- [exploration/README.md](exploration/README.md)

3. Run the current investigation baseline.

Start with:
- [investigations/README.md](investigations/README.md)
- [investigations/inv_001_target_behavior/README.md](investigations/inv_001_target_behavior/README.md)

4. Run the current experiment set.

Use:
- [experiments/README.md](experiments/README.md)
- [experiments/exp_001_baseline_rent_growth/README.md](experiments/exp_001_baseline_rent_growth/README.md)
- [experiments/exp_002_philly_consistent_baseline/README.md](experiments/exp_002_philly_consistent_baseline/README.md)
- [experiments/exp_003_philly_region_zip_panel/README.md](experiments/exp_003_philly_region_zip_panel/README.md)

## Evaluation (Cross-Experiment)

Use:
- [evaluation/README.md](evaluation/README.md)

MLflow notes:
- Local tracking defaults to `experiments/mlruns/`
- Override backend with `MLFLOW_TRACKING_URI`
- Disable tracking for a single run with `--no-mlflow`
- View local runs with:
```bash
uv run mlflow ui --backend-store-uri experiments/mlruns
```
