# Structuring Research Projects

## Purpose

Research projects need enough structure to preserve decisions and results, but not so much structure that early inquiry gets forced into fake rigor. Good organization should help work mature. It should not make uncertain work pretend to be settled.

## Core Principle

Different kinds of work belong in different places. Folder boundaries should reflect the maturity of the thinking, not just the file type.

## Recommended Structure

- `ingestion/`: source access, normalization, and entity-building
- `exploration/`: open-ended discovery, rough notebooks, fast iteration, unresolved questions
- `investigations/`: directed analysis with a concrete line of inquiry, light structure, and emerging methods
- `experiments/`: reproducible runs with a clear hypothesis, defined evaluation plan, and stable entrypoint
- `evaluation/`: comparison, synthesis, and decision support across experiments

## What Belongs In Investigations

Use `investigations/` when work is no longer pure exploration but is not yet ready to be treated as an experiment.

Typical signs:

- The question is becoming concrete.
- The work needs more structure than a loose notebook.
- Several approaches are being compared, but the evaluation design is still moving.
- The output is meant to guide future experiments, not make a final claim.

`investigations/` is the bridge between curiosity and proof.

## Promotion Rules

- Move work from `exploration/` to `investigations/` when the question sharpens and the path forward needs discipline.
- Move work from `investigations/` to `experiments/` when the hypothesis, data boundary, evaluation plan, and run path are stable.
- Keep `experiments/` reserved for reproducible claims, not general analysis.

## Standard

The repo should show how thinking evolves without collapsing every stage of work into the same bucket. Good structure preserves flexibility early and rigor later.
