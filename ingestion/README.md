# Ingestion

This folder contains source-level ingestion contracts and ontology mapping into canonical entities.

## Data Sources

- `SEPTA GTFS`: Static transit schedules and stop/route definitions; use it to derive planned accessibility and connectivity features.
- `SEPTA GTFS-RT`: Real-time transit updates (delays, vehicle positions, alerts); use it to measure reliability and disruption signals.
- `Philadelphia Property Bulk Download`: Citywide property-level records; use it for parcel-level geographic and housing context.
- `OpenDataPhilly - Certified for Rental Suitability`: Rental suitability license records; use it to track legal rental supply and unit-level compliance indicators.
- `OpenDataPhilly - Licenses & Inspections Property History`: Property permit/inspection/violation history; use it for quality/risk and neighborhood condition signals.
- `Zillow Research (ZORI + methodology)`: Rent index time series and documentation; use it as the main rent trend target and benchmark definition.
- `FRED PHIL942UR`: Philadelphia metro unemployment rate series; use it for macroeconomic regime features in forecasting.
- `NTAD Amtrak Stations`: National Amtrak station geospatial data; use it to capture intercity rail access and hub proximity effects.


## Layout

- `sources/`: one subfolder per source with request/response inspection code
- `ontology/`: canonical entity definitions and mapping code
- `minimal_ingest.py`: lightweight cross-source probe for connector health

## Run

```bash
python ingestion/minimal_ingest.py
```

Optional output and temp directories:

```bash
python ingestion/minimal_ingest.py \
  --output-dir ingestion/tmp/minimal_samples \
  --tmp-dir ingestion/tmp/source_samples
```

## Output

- report: `ingestion/tmp/minimal_samples/minimal_ingestion_report.json`
- per-source samples: `ingestion/tmp/source_samples/<source_name>/`

The report records per-source status, metadata, and small sample rows/bytes.
Promote stable datasets to `data/` only when ingestion logic is validated.

## Build Ontology Entities

After source probes generate samples, build canonical entity tables:

```bash
python ingestion/ontology/build_entities.py \
  --source-dir ingestion/tmp/source_samples \
  --output-dir ingestion/tmp/entities
```

Outputs:
- `ingestion/tmp/entities/geographic.csv`
- `ingestion/tmp/entities/economic.csv`
- `ingestion/tmp/entities/apartment_market.csv`

## Manual Cleanup (Keep Entities Only)

After building entities, remove probe artifacts to save disk space:

```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh
```

Non-interactive mode:

```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh --yes
```
