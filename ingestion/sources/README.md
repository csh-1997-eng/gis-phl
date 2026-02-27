# Source Connectors

One subfolder per data source. Keep source contracts isolated here.

## Contract Rules
- never mix sources in the same connector module
- include request shape, response schema notes, and sample payload outputs
- keep source probing and parsing code deterministic and testable
