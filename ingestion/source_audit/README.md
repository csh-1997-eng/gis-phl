# source_audit

## Purpose

Audit source connectors and local probe artifacts.

## Core Questions

- Which source connectors exist and have local probe coverage?
- Which sources have sample files on disk right now?
- Which live probe checks are succeeding, failing, or blocked by SSL?
- Where is the ingestion layer complete enough to inspect further?

## Expected Inputs

- source-level metadata and contracts under `ingestion/sources/`
- live probe report at `ingestion/tmp/samples/source_audit/minimal_ingestion_report.json`
- local sample files under `ingestion/tmp/samples/`

## Expected Outputs

- a source inventory
- a live probe results table
- a sample file inventory
- a compact audit summary

## Rule

This audit is descriptive only. It should show what exists and what is callable now. It should not rank, score, or recommend.

This code belongs to ingestion operations. The audit data it produces belongs under `ingestion/tmp/samples/source_audit/`.

## Run

```bash
uv run python ingestion/source_audit/analyze.py
```

## Outputs

Artifacts are written to `ingestion/tmp/samples/source_audit/artifacts/`.

Key tables:

- `source_inventory.csv`
- `source_probe_results.csv`
- `source_sample_inventory.csv`
- `source_audit_summary.csv`

## Interpretation Standard

Use this audit to inspect the current ingestion surface. Make the research judgment later, after the audit is in front of you.
