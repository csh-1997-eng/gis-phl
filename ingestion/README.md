# Ingestion

This folder contains source-level ingestion contracts and raw-data acquisition only.

## Data Sources

- `SEPTA GTFS`: Static transit schedules and stop/route definitions; use it to derive planned accessibility and connectivity features.
- `SEPTA GTFS-RT`: Real-time transit updates (delays, vehicle positions, alerts); use it to measure reliability and disruption signals.
- `Philadelphia Property Bulk Download`: Citywide property-level records; use it for parcel-level geographic and housing context.
- `OpenDataPhilly - Certified for Rental Suitability`: Rental suitability license records; use it to track legal rental supply and unit-level compliance indicators.
- `OpenDataPhilly - Licenses & Inspections Property History`: Property permit/inspection/violation history; use it for quality/risk and neighborhood condition signals.
- `OpenDataPhilly - Crime Incidents`: Incident-level public safety records; use it for neighborhood risk and safety trend features.
- `Zillow Research (ZORI + methodology)`: Rent index time series and documentation; use it as the main rent trend target and benchmark definition.
- `Census ACS 5-year`: ZIP/tract demographic and housing attributes; use it for socioeconomic and housing stock controls.
- `Census LEHD LODES`: Workplace/residence employment geography data; use it for job access and local economic activity features.
- `HUD Fair Market Rents`: HUD reference rent levels by geography; use it as a policy/market benchmark feature.
- `BLS Labor + CPI`: Local labor market and inflation reference metadata; use it to enrich macro context and area mappings.
- `FRED PHIL942UR`: Philadelphia metro unemployment rate series; use it for macroeconomic regime features in forecasting.
- `NTAD Amtrak Stations`: National Amtrak station geospatial data; use it to capture intercity rail access and hub proximity effects.


## Layout

- `sources/`: one subfolder per source with request/response inspection code
- `source_audit/`: descriptive audit of connector state, live probe status, and local sample coverage
- `minimal_ingest.py`: lightweight cross-source probe for connector health
- `tmp/samples/`: structured probe samples and source-audit outputs
- `tmp/targeted_extracts/`: intentional source extracts for a specific research need
- `tmp/full_extracts/`: complete raw extracts when full representation is needed

## Run

```bash
uv run python ingestion/minimal_ingest.py
```

Optional output and temp directories:

```bash
uv run python ingestion/minimal_ingest.py \
  --output-dir ingestion/tmp/samples/source_audit \
  --tmp-dir ingestion/tmp/samples
```

## Output

- report: `ingestion/tmp/samples/source_audit/minimal_ingestion_report.json`
- per-source samples: `ingestion/tmp/samples/<source_name>/`

The report records per-source status, metadata, and small sample rows/bytes.
Raw data should stay under `ingestion/tmp/`. Commit only important downstream artifacts.

## Capture a Larger Zillow City/MSA Surface

Use this when the probe samples are no longer sufficient and the target surface needs a fuller state-filtered Zillow extract.

```bash
uv run python ingestion/sources/zillow/extract_state_filtered.py \
  --states PA NJ DE MD NY CT VA MA DC \
  --dataset-keys city metro
```

This writes:
- targeted filtered files into `ingestion/tmp/targeted_extracts/zillow/`
- optional full raw files into `ingestion/tmp/full_extracts/zillow/`

Downstream ontology builds prefer richer targeted/full files over older sample heads when both are present.

## Audit Source Connectors

Use this to inspect connector coverage after running `minimal_ingest.py`:

```bash
uv run python ingestion/source_audit/analyze.py
```

Outputs:
- `ingestion/tmp/samples/source_audit/artifacts/source_inventory.csv`
- `ingestion/tmp/samples/source_audit/artifacts/source_probe_results.csv`
- `ingestion/tmp/samples/source_audit/artifacts/source_sample_inventory.csv`
- `ingestion/tmp/samples/source_audit/artifacts/source_audit_summary.csv`

## Hand Off To Exploration

After raw source data is in place, build ontology fact tables from the exploration layer:

```bash
uv run python exploration/ontology/build_entities.py \
  --source-dir ingestion/tmp \
  --source-layer samples \
  --output-dir exploration/tmp/ontology
```

Outputs:
- `exploration/tmp/ontology/geographic.csv`
- `exploration/tmp/ontology/economic.csv`
- `exploration/tmp/ontology/apartment_market.csv`

`apartment_market.csv` now preserves Zillow geography metadata:
- `region_type` (for example `msa`, `city`, `zip`)
- `region_name`
- `state_name`
- `source_dataset`

## Build a Theory-Labeled Zillow Sample

Use this to define a Philadelphia-centered Zillow universe by mechanism rather than by a raw state list.

Edit the design in `exploration/ontology/zillow_theory_sample.yaml`, then build the realized manifest:

```bash
uv run python exploration/ontology/build_zillow_theory_sample.py
```

Outputs:
- `exploration/tmp/ontology/zillow_theory_sample_manifest.csv`
- `exploration/tmp/ontology/zillow_theory_sample_summary.csv`
- `exploration/tmp/ontology/zillow_theory_sample_unmatched.csv`
- `exploration/tmp/ontology/apartment_market_theory_sample.csv`
- `exploration/tmp/ontology/geographic_theory_sample.csv`

## Manual Cleanup (Keep Entities Only)

After building entities, remove probe artifacts to save disk space:

```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh
```

Non-interactive mode:

```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh --yes
```
