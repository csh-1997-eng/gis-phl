# Experiments

Each experiment should live in its own subfolder with:
- objective
- data slice/version
- feature set
- model/training config
- metrics and artifacts
- methodology writeup (`METHODOLOGY.md`)
- conclusions and next step


## Scaffold a new experiment

Use the scaffold script so every new `exp_*` folder includes the standard files:

```bash
./experiments/scripts/new_experiment.sh exp_003_transit_features_v1
```

This creates:
- `experiments/exp_003_transit_features_v1/README.md`
- `experiments/exp_003_transit_features_v1/METHODOLOGY.md`
- `experiments/exp_003_transit_features_v1/src/`
- `experiments/exp_003_transit_features_v1/artifacts/`
