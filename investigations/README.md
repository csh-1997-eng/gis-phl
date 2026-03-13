# investigations

Use this directory for work that is more structured than exploration and less rigid than a formal experiment.

Current sequence:

- `inv_001_target_behavior`: understand the target before changing models
- `inv_002_geography_scope`: compare geography levels, volatility, sparsity, and scope effects
- `inv_003_data_readiness`: audit candidate datasets before building new ontology joins

Working standard:

- Investigations should answer a concrete question.
- They should produce reusable outputs, not just notebook observations.
- They should narrow future experiment choices.
- They should not pretend to be final claims.

Promotion rule:

- Keep open-ended discovery in `exploration/`.
- Move work here when the question sharpens and the analysis needs structure.
- Promote work to `experiments/` only when the hypothesis and evaluation plan are stable.

## Run Order

1. Start with [inv_001_target_behavior/README.md](inv_001_target_behavior/README.md)
2. Move to [inv_002_geography_scope/README.md](inv_002_geography_scope/README.md)
3. Use [inv_003_data_readiness/README.md](inv_003_data_readiness/README.md) before expanding the ontology or feature table

## Commands

Run the implemented investigation:

```bash
uv run python investigations/inv_001_target_behavior/src/analyze.py
```

Current status:
- `inv_001` is implemented
- `inv_002` and `inv_003` are defined and scoped, but not yet scripted
