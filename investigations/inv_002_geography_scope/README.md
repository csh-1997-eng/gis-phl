# inv_002_geography_scope

## Purpose

Compare geography levels and scope choices before declaring one modeling surface to be the default.

## Core Questions

- How do ZIP, city, and MSA panels differ in volatility and stability?
- Where is the panel sparse or imbalanced by geography type?
- Are some units too noisy for the current target definition?
- How much of the observed difficulty is caused by geography scope rather than model weakness?

## Expected Inputs

- `ingestion/tmp/entities/apartment_market.csv`
- `ingestion/tmp/entities/geographic.csv`
- experiment artifact summaries and predictions where useful

## Expected Outputs

- geography-level volatility summaries
- panel sparsity summaries
- error concentration views by geography type
- a recommendation on which geography surface is most defensible for the next experiment cycle

## Run

This investigation is not implemented yet.

The intended entrypoint is:

```bash
uv run python investigations/inv_002_geography_scope/src/analyze.py
```

Do not treat this as runnable until the script exists.
