# Exploration

Everything related to EDA and source/entity understanding lives here.

## Layout

- `notebooks/`: exploratory notebooks
- `env/`: pinned notebook environment and kernel controls

## Notebooks

- `01_data_source_investigation.ipynb`: inspect minimal source probe results.
- `02_entity_sanity_checks.ipynb`: validate ontology entity outputs (nulls, keys, periods, integrity).
- Both notebooks export summary CSVs to `exploration/tmp/notebook_exports/<notebook_name>/`.

## Start Exploration

```bash
./env/scripts/bootstrap_notebook_env.sh
cd env
make lab
```

## Re-run Entity Exploration (Scripted)

Use this when entity schemas evolve and you want deterministic CSV outputs without manually re-running notebook cells:

```bash
python exploration/scripts/run_entity_exploration.py \
  --entities-dir ingestion/tmp/entities \
  --output-dir exploration/tmp/notebook_exports/02_entity_sanity_checks
```

Exports include:
- `table_summary.csv`
- `apartment_market_granularity.csv`
- `zip_panel_geographies.csv`
- `zip_panel_state_summary.csv`
- `schema_compat_report.csv`
