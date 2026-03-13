# Exploration

Everything related to EDA and source/entity understanding lives here.

## Layout

- `notebooks/`: exploratory notebooks

## Notebooks

- `01_data_source_investigation.ipynb`: inspect minimal source probe results.
- `02_entity_sanity_checks.ipynb`: validate ontology entity outputs (nulls, keys, periods, integrity).
- Both notebooks export summary CSVs to `exploration/tmp/notebook_exports/<notebook_name>/`.

## Run

```bash
uv run jupyter lab
```

Then open:
- `exploration/notebooks/01_data_source_investigation.ipynb`
- `exploration/notebooks/02_entity_sanity_checks.ipynb`

Use this section after:
- `uv run python ingestion/minimal_ingest.py`
- `uv run python ingestion/ontology/build_entities.py --source-dir ingestion/tmp/source_samples --output-dir ingestion/tmp/entities`

## Reproduce The Current Exploration Outputs

The notebooks are the main workflow. Re-run them from Jupyter if the entity tables or source samples change.

Expected exports include:
- `table_summary.csv`
- `apartment_market_granularity.csv`
- `zip_panel_geographies.csv`
- `zip_panel_state_summary.csv`
- `schema_compat_report.csv`
