#!/usr/bin/env python3
"""Build a theory-labeled Zillow sampling manifest and filtered panel."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_APT_PATH = REPO_ROOT / "exploration/tmp/ontology/apartment_market.csv"
DEFAULT_GEO_PATH = REPO_ROOT / "exploration/tmp/ontology/geographic.csv"
DEFAULT_CONFIG_PATH = REPO_ROOT / "exploration/ontology/zillow_theory_sample.yaml"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "exploration/tmp/ontology"


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def load_geo_inventory(apt_path: Path, geo_path: Path) -> pd.DataFrame:
    apt = pd.read_csv(apt_path, low_memory=False)
    geo = pd.read_csv(geo_path, low_memory=False)
    apt["period_dt"] = pd.to_datetime(apt["period"], errors="coerce")

    geo_inventory = (
        apt.groupby(
            ["geography_entity_id", "region_name", "region_type", "state_name", "source_dataset"],
            dropna=False,
        )
        .agg(
            row_count=("entity_id", "size"),
            min_period=("period_dt", "min"),
            max_period=("period_dt", "max"),
        )
        .reset_index()
    )
    geo_lookup = geo.rename(columns={"entity_id": "geography_entity_id", "name": "geography_name"})
    geo_inventory = geo_inventory.merge(
        geo_lookup[["geography_entity_id", "geography_type", "geography_name"]],
        on="geography_entity_id",
        how="left",
    )
    geo_inventory["state_name"] = geo_inventory["state_name"].where(geo_inventory["state_name"].notna(), None)
    return geo_inventory.sort_values(["region_type", "state_name", "region_name", "geography_entity_id"])


def _normalize_state(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text if text else None


def select_exact_matches(
    geo_inventory: pd.DataFrame,
    layer: str,
    exact_matches: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    for spec in exact_matches:
        region_type = spec["region_type"]
        region_name = spec["region_name"]
        state_name = _normalize_state(spec.get("state_name"))

        mask = (geo_inventory["region_type"] == region_type) & (geo_inventory["region_name"] == region_name)
        if state_name is None:
            mask = mask & geo_inventory["state_name"].isna()
        else:
            mask = mask & (geo_inventory["state_name"] == state_name)

        matches = geo_inventory.loc[mask].copy()
        if matches.empty:
            unmatched.append(
                {
                    "layer": layer,
                    "selection_method": "exact_match",
                    "region_type": region_type,
                    "region_name": region_name,
                    "state_name": state_name,
                    "rationale": spec.get("rationale", ""),
                }
            )
            continue

        for _, row in matches.iterrows():
            selected.append(
                {
                    "layer": layer,
                    "selection_method": "exact_match",
                    "selection_reason": spec.get("rationale", ""),
                    "geography_entity_id": row["geography_entity_id"],
                    "geography_type": row.get("geography_type"),
                    "geography_name": row.get("geography_name"),
                    "region_type": row["region_type"],
                    "region_name": row["region_name"],
                    "state_name": row["state_name"],
                    "source_dataset": row["source_dataset"],
                    "row_count": row["row_count"],
                    "min_period": row["min_period"],
                    "max_period": row["max_period"],
                    "anchor_geo": None,
                    "overlap_months": None,
                    "mae_vs_anchor_rent_growth_1m": None,
                    "corr_vs_anchor_rent_growth_1m": None,
                }
            )

    return selected, unmatched


def select_nearest_candidates(
    geo_inventory: pd.DataFrame,
    layer: str,
    rule: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    file_path = REPO_ROOT / rule["file"]
    if not file_path.exists():
        return [], [
            {
                "layer": layer,
                "selection_method": "nearest_rule",
                "region_type": None,
                "region_name": str(file_path),
                "state_name": None,
                "rationale": f"Candidate file not found: {file_path}",
            }
        ]

    candidates = pd.read_csv(file_path)
    allowed_states = set(rule.get("allowed_states", []))
    min_overlap = int(rule.get("min_overlap_months", 0))
    top_n = int(rule.get("top_n", len(candidates)))

    if "state_name" in candidates.columns and allowed_states:
        candidates = candidates[candidates["state_name"].isin(allowed_states)].copy()
    if "overlap_months" in candidates.columns:
        candidates = candidates[candidates["overlap_months"] >= min_overlap].copy()

    candidates = candidates.head(top_n).copy()
    if candidates.empty:
        return [], [
            {
                "layer": layer,
                "selection_method": "nearest_rule",
                "region_type": None,
                "region_name": str(file_path),
                "state_name": ",".join(sorted(allowed_states)) if allowed_states else None,
                "rationale": "No candidates satisfied the nearest-rule filters.",
            }
        ]

    selected: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for _, row in candidates.iterrows():
        candidate_match = geo_inventory.loc[
            geo_inventory["geography_entity_id"] == row.get("candidate_geo")
        ].copy()

        if candidate_match.empty:
            candidate_match = geo_inventory.loc[
                (geo_inventory["region_name"] == row.get("region_name"))
                & (geo_inventory["region_type"] == row.get("region_type"))
                & (geo_inventory["state_name"].fillna("") == str(row.get("state_name", "")))
            ].copy()

        if candidate_match.empty:
            unmatched.append(
                {
                    "layer": layer,
                    "selection_method": "nearest_rule",
                    "region_type": row.get("region_type"),
                    "region_name": row.get("region_name"),
                    "state_name": row.get("state_name"),
                    "rationale": f"Candidate not found in current apartment_market inventory: {row.get('candidate_geo')}",
                }
            )
            continue

        inventory_row = candidate_match.iloc[0]
        selected.append(
            {
                "layer": layer,
                "selection_method": "nearest_rule",
                "selection_reason": rule.get("rationale", ""),
                "geography_entity_id": inventory_row["geography_entity_id"],
                "geography_type": inventory_row.get("geography_type"),
                "geography_name": inventory_row.get("geography_name"),
                "region_type": inventory_row["region_type"],
                "region_name": inventory_row["region_name"],
                "state_name": inventory_row["state_name"],
                "source_dataset": inventory_row["source_dataset"],
                "row_count": inventory_row["row_count"],
                "min_period": inventory_row["min_period"],
                "max_period": inventory_row["max_period"],
                "anchor_geo": row.get("anchor_geo"),
                "overlap_months": row.get("overlap_months"),
                "mae_vs_anchor_rent_growth_1m": row.get("mae_vs_anchor_rent_growth_1m"),
                "corr_vs_anchor_rent_growth_1m": row.get("corr_vs_anchor_rent_growth_1m"),
            }
        )

    return selected, unmatched


def build_manifest(geo_inventory: pd.DataFrame, config: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected_rows: list[dict[str, Any]] = []
    unmatched_rows: list[dict[str, Any]] = []

    for layer_spec in config.get("layers", []):
        layer = layer_spec["layer"]
        if layer_spec.get("exact_matches"):
            selected, unmatched = select_exact_matches(geo_inventory, layer, layer_spec["exact_matches"])
            selected_rows.extend(selected)
            unmatched_rows.extend(unmatched)
        for rule in layer_spec.get("nearest_rules", []):
            selected, unmatched = select_nearest_candidates(geo_inventory, layer, rule)
            selected_rows.extend(selected)
            unmatched_rows.extend(unmatched)

    manifest = pd.DataFrame(selected_rows)
    if manifest.empty:
        manifest = pd.DataFrame(
            columns=[
                "layer",
                "selection_method",
                "selection_reason",
                "geography_entity_id",
                "geography_type",
                "geography_name",
                "region_type",
                "region_name",
                "state_name",
                "source_dataset",
                "row_count",
                "min_period",
                "max_period",
                "anchor_geo",
                "overlap_months",
                "mae_vs_anchor_rent_growth_1m",
                "corr_vs_anchor_rent_growth_1m",
            ]
        )
    else:
        manifest = manifest.sort_values(
            ["layer", "region_type", "state_name", "region_name", "geography_entity_id"]
        ).drop_duplicates(subset=["layer", "geography_entity_id"], keep="first")

    unmatched = pd.DataFrame(unmatched_rows)
    return manifest, unmatched


def build_summary(manifest: pd.DataFrame) -> pd.DataFrame:
    if manifest.empty:
        return pd.DataFrame(
            columns=[
                "layer",
                "region_type",
                "geo_count",
                "state_count",
                "total_rows",
                "min_period",
                "max_period",
            ]
        )

    return (
        manifest.groupby(["layer", "region_type"], dropna=False)
        .agg(
            geo_count=("geography_entity_id", "nunique"),
            state_count=("state_name", lambda s: int(s.dropna().nunique())),
            total_rows=("row_count", "sum"),
            min_period=("min_period", "min"),
            max_period=("max_period", "max"),
        )
        .reset_index()
        .sort_values(["layer", "region_type"])
    )


def write_filtered_outputs(
    apt_path: Path,
    geo_path: Path,
    manifest: pd.DataFrame,
    output_dir: Path,
) -> None:
    apt = pd.read_csv(apt_path, low_memory=False)
    geo = pd.read_csv(geo_path, low_memory=False)

    selected_geo_ids = manifest["geography_entity_id"].dropna().unique().tolist()
    filtered_apt = apt[apt["geography_entity_id"].isin(selected_geo_ids)].copy()
    filtered_geo = geo[geo["entity_id"].isin(selected_geo_ids)].copy()

    filtered_apt.to_csv(output_dir / "apartment_market_theory_sample.csv", index=False)
    filtered_geo.to_csv(output_dir / "geographic_theory_sample.csv", index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a theory-labeled Zillow sample manifest")
    parser.add_argument("--apt-path", type=Path, default=DEFAULT_APT_PATH)
    parser.add_argument("--geo-path", type=Path, default=DEFAULT_GEO_PATH)
    parser.add_argument("--config-path", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    config = load_config(args.config_path)
    geo_inventory = load_geo_inventory(args.apt_path, args.geo_path)
    manifest, unmatched = build_manifest(geo_inventory, config)
    summary = build_summary(manifest)

    manifest.to_csv(args.output_dir / "zillow_theory_sample_manifest.csv", index=False)
    summary.to_csv(args.output_dir / "zillow_theory_sample_summary.csv", index=False)
    unmatched.to_csv(args.output_dir / "zillow_theory_sample_unmatched.csv", index=False)
    write_filtered_outputs(args.apt_path, args.geo_path, manifest, args.output_dir)

    print(f"Wrote theory-labeled Zillow sample to: {args.output_dir}")
    print(f"- manifest rows: {len(manifest)}")
    print(f"- unmatched requests: {len(unmatched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
