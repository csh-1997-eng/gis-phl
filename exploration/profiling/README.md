# Profiling

Purpose: summarize ontology outputs so the project knows what it actually has before investigation or modeling.

This layer should answer:
- how much data exists
- which geographies are covered
- what time ranges are available
- where duplicates, gaps, or missingness exist
- how balanced the panels are

Profiling should read from `exploration/tmp/ontology/`.

Important profiling outputs can live in committed `artifacts/`.
Disposable runs, notebook exports, and intermediate summaries should stay in `tmp/`.

This layer is descriptive. It should clarify the ontology surface, not make research claims.
