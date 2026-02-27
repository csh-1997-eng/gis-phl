# Ontology Mapping

Purpose: map heterogeneous source records into canonical entities before exploration or modeling.

Canonical entities:
- `geographic`
- `demographic`
- `apartment_market`
- `economic`

Conventions:
- Source-specific parsing stays in `ingestion/sources/*`.
- Entity mapping logic lives here.
- Downstream folders consume ontology-aligned tables, not raw API payloads.
