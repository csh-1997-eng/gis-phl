# inv_001_target_behavior

## Purpose

Understand the behavior of the rent-growth target before changing features or model classes.

## Core Questions

- How volatile is the target across geography types and over time?
- How much variation is cross-sectional versus within-geography?
- How persistent is the target at different horizons?
- Is there visible seasonality or evidence of structural change?
- How balanced is the panel, and where is missingness concentrated?

## Inputs

- `exploration/tmp/ontology/apartment_market.csv`
- `exploration/tmp/ontology/geographic.csv`

## Outputs

- `artifacts/target_summary_by_geography_type.csv`
- `artifacts/variance_decomposition.csv`
- `artifacts/autocorrelation_summary.csv`
- `artifacts/autocorrelation_by_geography.csv`
- `artifacts/naive_strength_by_horizon.csv`
- `artifacts/seasonality_by_month.csv`
- `artifacts/panel_balance_by_geography.csv`
- `artifacts/panel_balance_summary.csv`
- `artifacts/duplicate_geography_periods.csv`
- `artifacts/structural_shift_by_geography.csv`
- `artifacts/structural_shift_summary.csv`
- `artifacts/yearly_target_summary.csv`
- `artifacts/plots/target_volatility_by_geography_type.png`
- `artifacts/plots/naive_mae_by_horizon.png`
- `artifacts/plots/autocorrelation_by_horizon.png`
- `artifacts/plots/yearly_mean_target_by_geography_type.png`
- `artifacts/plots/structural_shift_summary.png`

## Run

```bash
uv run python investigations/inv_001_target_behavior/src/analyze.py
```

Use these outputs to decide whether the next bottleneck is target definition, geography scope, or feature design.
