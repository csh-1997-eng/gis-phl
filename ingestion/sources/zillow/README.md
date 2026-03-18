# zillow

Source-specific ingestion contract.

## Purpose
- probe endpoint/file availability
- inspect request/response structure
- capture minimal sample payloads for schema understanding

## Current Probe Coverage
- Zillow research portal metadata page
- ZORI methodology page
- ZORI CSV samples for:
  - `metro`
  - `city`
  - `zip`

## Notes
- Probe files are byte-limited samples for schema checks, not full extracts.

## Full City/MSA Extraction

Use this when the goal is to move beyond head samples and capture a larger state-filtered Zillow surface for research.

Example:

```bash
uv run python ingestion/sources/zillow/extract_state_filtered.py \
  --states PA NJ DE MD NY CT VA MA DC \
  --dataset-keys city metro
```

Outputs:
- `ingestion/tmp/targeted_extracts/zillow/city_zori_state_filtered.csv`
- `ingestion/tmp/targeted_extracts/zillow/metro_zori_state_filtered.csv`
- `ingestion/tmp/targeted_extracts/zillow/zillow_state_filtered_summary.json`
- optional full raw files in `ingestion/tmp/full_extracts/zillow/`

When these filtered files are present, downstream ontology builds prefer them over the older sample `_head.csv` files for the same dataset key.
