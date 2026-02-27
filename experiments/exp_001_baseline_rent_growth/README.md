# exp_001_baseline_rent_growth

## Question
Can lagged rent signals plus unemployment explain next-month rent growth at the geography-month level?

## Hypothesis
A simple linear baseline using lagged rent features and unemployment should outperform a naive `lag1` predictor on MAE/RMSE.

## Data Inputs
- `ingestion/tmp/entities/apartment_market.csv`
- `ingestion/tmp/entities/economic.csv`

## Target
- `target_next_rent_growth_1m`: next month `rent_growth_1m` per `geography_entity_id`

## Validation
- Strict time split
- Default train end date: `2024-12-31`
- Validation starts after train end date

## Metrics
- MAE
- RMSE
- Directional accuracy

## Run

```bash
python experiments/exp_001_baseline_rent_growth/src/train.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --econ-path ingestion/tmp/entities/economic.csv \
  --artifacts-dir experiments/exp_001_baseline_rent_growth/artifacts \
  --train-end-date 2024-12-31
```

## Outputs
- `artifacts/modeling_table.csv`
- `artifacts/dataset_summary.csv`
- `artifacts/predictions.csv`
- `artifacts/metrics.json`
- `artifacts/feature_weights.csv`
