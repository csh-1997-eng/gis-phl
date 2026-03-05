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
