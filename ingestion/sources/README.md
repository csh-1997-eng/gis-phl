# Source Connectors

One subfolder per data source. Keep source contracts isolated here.

## Contract Rules
- never mix sources in the same connector module
- include request shape, response schema notes, and sample payload outputs
- keep source probing and parsing code deterministic and testable

## Active Source Modules
- `septa_gtfs`
- `septa_gtfs_rt`
- `phl_property_bulk`
- `opendataphilly_rental_suitability`
- `opendataphilly_li_property_history`
- `opendataphilly_crime_incidents`
- `zillow`
- `acs_5y`
- `lehd_lodes`
- `hud_fmr`
- `bls_labor_cpi`
- `fred`
- `ntad_amtrak`
