# Ontology

Purpose: map raw source records into reusable domain structure.

This layer should produce:
- identity tables
- source crosswalk tables
- fact tables
- reusable selection manifests

This layer should not produce:
- pre-joined modeling tables
- hidden mixtures of sample, targeted, and full raw-data maturity

## Current Outputs

Current ontology fact tables and manifests are written to `exploration/tmp/ontology/`.

Core outputs:
- `geographic.csv`
- `economic.csv`
- `apartment_market.csv`
- `zillow_theory_sample_manifest.csv`
- `zillow_theory_sample_summary.csv`
- `zillow_theory_sample_unmatched.csv`
- `apartment_market_theory_sample.csv`
- `geographic_theory_sample.csv`

## Build Fact Tables

Build ontology outputs from one explicit raw-data layer:

```bash
uv run python exploration/ontology/build_entities.py \
  --source-dir ingestion/tmp \
  --source-layer samples \
  --output-dir exploration/tmp/ontology
```

Valid `--source-layer` values:
- `samples`
- `targeted_extracts`
- `full_extracts`

The build should fail if the requested layer does not contain the required raw inputs. It should not borrow silently from another layer.

## Build The Zillow Theory Sample

Edit the design in `exploration/ontology/zillow_theory_sample.yaml`, then build the realized manifest from the current ontology tables:

```bash
uv run python exploration/ontology/build_zillow_theory_sample.py
```

Outputs:
- `exploration/tmp/ontology/zillow_theory_sample_manifest.csv`
- `exploration/tmp/ontology/zillow_theory_sample_summary.csv`
- `exploration/tmp/ontology/zillow_theory_sample_unmatched.csv`
- `exploration/tmp/ontology/apartment_market_theory_sample.csv`
- `exploration/tmp/ontology/geographic_theory_sample.csv`

## Working Standard

- Keep source-specific parsing in `ingestion/sources/`.
- Keep ontology focused on real-world objects and facts.
- Build joins for a question later, inside investigations or experiments.
