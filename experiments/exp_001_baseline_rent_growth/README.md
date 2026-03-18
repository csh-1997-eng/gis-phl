# exp_001_baseline_rent_growth

## Question
Can lagged rent signals plus unemployment explain next-month rent growth at the geography-month level?

## Hypothesis
A simple linear baseline using lagged rent features and unemployment should outperform a naive `lag1` predictor on MAE/RMSE.

## Data Inputs
- `exploration/tmp/ontology/apartment_market.csv`
- `exploration/tmp/ontology/economic.csv`

## Target
- `target_next_rent_growth_1m`: next month `rent_growth_1m` per `geography_entity_id`

## Model Summary
- `naive_lag1`: predicts next-month growth as last observed `rent_growth_1m`
- `linear_regression`: ordinary least squares baseline over lag + macro features

## Feature Set
- `rent_growth_1m_lag1`
- `rent_growth_1m_lag3`
- `rent_growth_1m_lag12`
- `rent_index_lag1`
- `unemployment_rate`

## Feature Lineage (Feature -> Ontology -> Source)

| Feature | Ontology Entity | Ontology Field | Upstream Source |
| --- | --- | --- | --- |
| `rent_growth_1m_lag1` | `apartment_market` | `rent_growth_1m` (lagged by 1) | Zillow ZORI |
| `rent_growth_1m_lag3` | `apartment_market` | `rent_growth_1m` (lagged by 3) | Zillow ZORI |
| `rent_growth_1m_lag12` | `apartment_market` | `rent_growth_1m` (lagged by 12) | Zillow ZORI |
| `rent_index_lag1` | `apartment_market` | `rent_index` (lagged by 1) | Zillow ZORI |
| `unemployment_rate` | `economic` | `unemployment_rate` | FRED `PHIL942UR` |

Target lineage:
- `target_next_rent_growth_1m` -> `apartment_market.rent_growth_1m` shifted forward one month -> Zillow ZORI


## Methodology Notes
See `METHODOLOGY.md` for a full writeup of current assumptions, known inconsistencies, etc

## Validation
- Strict time split
- Default train end date: `2024-12-31`
- Validation starts after train end date

## Metrics
- MAE
- RMSE
- Directional accuracy
- Spearman rank correlation

## Run

```bash
uv run python experiments/exp_001_baseline_rent_growth/src/train.py \
  --apt-path exploration/tmp/ontology/apartment_market.csv \
  --econ-path exploration/tmp/ontology/economic.csv \
  --artifacts-dir experiments/exp_001_baseline_rent_growth/artifacts \
  --train-end-date 2024-12-31
```

## Outputs
- `artifacts/modeling_table.csv`
- `artifacts/dataset_summary.csv`
- `artifacts/predictions.csv`
- `artifacts/metrics.json`
- `artifacts/feature_weights.csv`
