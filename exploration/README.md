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
