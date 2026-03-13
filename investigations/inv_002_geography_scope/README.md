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

```bash
uv run python investigations/inv_002_geography_scope/src/analyze.py
```

## Outputs

Artifacts are written to `investigations/inv_002_geography_scope/artifacts/`.

Key tables:

- `surface_panel_summary.csv`
- `experiment_error_summary.csv`
- `experiment_error_by_geography_type.csv`
- `error_concentration_by_geography.csv`
- `surface_recommendation.csv`

Key visuals:

- `plots/surface_volatility_distribution.png`
- `plots/surface_history_distribution.png`
- `plots/experiment_holdout_mae.png`
- `plots/surface_tradeoff_matrix.png`
- `plots/error_concentration_by_geography.png`

## Interpretation Standard

This investigation is not trying to crown a universally best geography surface.

It is trying to answer a narrower question:

- which surface is most stable for controlled baseline work
- which surface is most aligned with the real Philadelphia decision question
- where the current modeling pain is coming from
