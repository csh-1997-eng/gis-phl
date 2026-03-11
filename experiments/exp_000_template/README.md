# Experiment Template

- question:
- hypothesis:
- run spec: `run_spec.yaml`
- data inputs (ontology entities + version):
- scope (geography/population/time):
- feature set:
- model:
- validation design:
- metrics:
- result summary:
- follow-up:

## Methodology

This experiment must include a companion `METHODOLOGY.md` that documents:
- executive summary
- what is actually happening (scope, feature alignment, validation protocol)
- feature and target lineage
- model summary and metrics
- remaining limitations
- decision log

## Tracking

- Keep `run_spec.yaml` current before training so hypothesis, reasoning, and evaluation intent are logged to MLflow.
- Training scripts should keep writing local artifacts while also logging them to MLflow unless `--no-mlflow` is used.
