# Ingestion

This folder contains source-level ingestion contracts and ontology mapping into canonical entities.

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

`apartment_market.csv` now preserves Zillow geography metadata:
- `region_type` (for example `msa`, `city`, `zip`)
- `region_name`
- `state_name`
- `source_dataset`

## Audit Geography Granularity

Use this to verify how many geographies you have at each level and which Philadelphia geographies are available:

```bash
python ingestion/ontology/audit_geographic_granularity.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --output-dir ingestion/tmp/entities
```

Outputs:
- `ingestion/tmp/entities/granularity_summary.csv`
- `ingestion/tmp/entities/philly_geographies.csv`

## Find Expansion Candidates (City/MSA/ZIP)

Use this to surface ZIP availability in surrounding states and rank nearby city/MSA/ZIP series by similarity to Philadelphia trends:

```bash
python ingestion/ontology/find_expansion_candidates.py \
  --apt-path ingestion/tmp/entities/apartment_market.csv \
  --output-dir ingestion/tmp/entities
```

Outputs:
- `ingestion/tmp/entities/regional_zip_inventory.csv`
- `ingestion/tmp/entities/nearest_cities_to_philly_city.csv`
- `ingestion/tmp/entities/nearest_msas_to_philly_msa.csv`
- `ingestion/tmp/entities/nearest_zips_to_philly_msa.csv`

## Manual Cleanup (Keep Entities Only)

After building entities, remove probe artifacts to save disk space:

```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh
```

Non-interactive mode:

```bash
./ingestion/scripts/cleanup_tmp_keep_entities.sh --yes
```
