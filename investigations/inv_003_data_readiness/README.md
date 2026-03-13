# inv_003_data_readiness

## Purpose

Audit candidate datasets before extending the ontology or joining new features into the modeling table.

## Core Questions

- Which sources have stable join keys against the current geography surfaces?
- Which sources have time coverage aligned with the rent target horizon?
- Which sources refresh frequently enough to be plausible predictive inputs?
- Which sources are likely to add signal rather than just complexity?

## Expected Inputs

- current ontology entities in `ingestion/tmp/entities/`
- source-level metadata and coverage notes under `ingestion/sources/`

## Expected Outputs

- a join-key audit
- a coverage-window audit
- a refresh-frequency summary
- a shortlist of candidate sources worth integrating next

## Rule

Do not expand the ontology because a dataset looks interesting. Expand it when the investigation says the dataset is aligned, timely, and plausibly useful.

## Run

This investigation is not implemented yet.

The intended entrypoint is:

```bash
uv run python investigations/inv_003_data_readiness/src/analyze.py
```

Do not treat this as runnable until the script exists.
