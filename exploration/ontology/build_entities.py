#!/usr/bin/env python3
"""Build ontology-aligned fact tables from one explicit raw-data layer."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from map_to_entities import (
    base_geographic_entities,
    load_fred_entities_from_csv,
    load_zori_apartment_market_entities_from_csv,
    map_ntad_feature_to_geographic,
    unique_by_key,
    zori_geographic_entities,
)

DEFAULT_SOURCE_DIR = Path("ingestion/tmp")
DEFAULT_OUTPUT_DIR = Path("exploration/tmp/ontology")
DEFAULT_SOURCE_LAYER = "samples"


def _zori_dataset_key_from_name(path: Path) -> str:
    return path.name.split("_zori_", 1)[0].lower()


def _zori_file_priority(path: Path) -> tuple[int, int, str]:
    name = path.name.lower()
    if "state_filtered" in name:
        priority = 3
    elif "full" in name:
        priority = 2
    elif "head" in name:
        priority = 1
    else:
        priority = 0
    size = path.stat().st_size if path.exists() else 0
    return (priority, size, path.name)


def resolve_source_layer_dir(source_dir: Path, source_layer: str) -> Path:
    layer_dir = source_dir / source_layer
    if layer_dir.exists():
        return layer_dir
    if source_dir.exists() and source_layer == DEFAULT_SOURCE_LAYER:
        return source_dir
    raise FileNotFoundError(f"Could not find requested source layer: {layer_dir}")


def find_required_file(source_layer_dir: Path, relative_path: Path) -> Path:
    candidate = source_layer_dir / relative_path
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Could not find {relative_path} under requested source layer: {source_layer_dir}")


def select_zori_files(source_layer_dir: Path) -> list[Path]:
    zori_files: list[Path] = []
    zillow_dir = source_layer_dir / "zillow"
    zori_files.extend(sorted(zillow_dir.glob("*_zori_*.csv")))
    legacy_file = zillow_dir / "zori_head.csv"
    if legacy_file.exists():
        zori_files.append(legacy_file)

    if not zori_files:
        return []

    by_dataset: dict[str, list[Path]] = {}
    for path in zori_files:
        by_dataset.setdefault(_zori_dataset_key_from_name(path), []).append(path)

    selected: list[Path] = []
    for dataset_key, paths in by_dataset.items():
        del dataset_key
        best = sorted(paths, key=_zori_file_priority, reverse=True)[0]
        selected.append(best)

    return sorted(selected, key=lambda path: path.name)


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def load_ntad_geojson_features(geojson_path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(geojson_path.read_text(encoding="utf-8"))
    return payload.get("features", [])


def build_entities(source_dir: Path, source_layer: str) -> Dict[str, List[Dict[str, Any]]]:
    source_layer_dir = resolve_source_layer_dir(source_dir, source_layer)

    fred_rows = load_fred_entities_from_csv(
        find_required_file(source_layer_dir, Path("fred/philly_unemployment_head.csv"))
    )

    apt_rows: List[Dict[str, Any]] = []
    zori_files = select_zori_files(source_layer_dir)

    if not zori_files:
        raise FileNotFoundError(f"No Zillow ZORI CSVs found under requested source layer: {source_layer_dir}")

    for csv_path in zori_files:
        apt_rows.extend(
            load_zori_apartment_market_entities_from_csv(
                csv_path,
                source_dataset=csv_path.name,
            )
        )

    apt_rows = unique_by_key(apt_rows, "entity_id")

    ntad_features = load_ntad_geojson_features(
        find_required_file(source_layer_dir, Path("ntad_amtrak/amtrak_sample.geojson"))
    )
    amtrak_geo_rows = [map_ntad_feature_to_geographic(feat) for feat in ntad_features]

    geographic_rows = base_geographic_entities() + zori_geographic_entities(apt_rows) + amtrak_geo_rows
    geographic_rows = unique_by_key(geographic_rows, "entity_id")

    return {
        "economic": fred_rows,
        "apartment_market": apt_rows,
        "geographic": geographic_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ontology-aligned entity and fact tables")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Root raw-data directory containing samples, targeted_extracts, and full_extracts",
    )
    parser.add_argument(
        "--source-layer",
        choices=["samples", "targeted_extracts", "full_extracts"],
        default=DEFAULT_SOURCE_LAYER,
        help="Explicit raw-data maturity layer to map into ontology outputs",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for entity CSVs",
    )
    args = parser.parse_args()

    entity_sets = build_entities(args.source_dir, args.source_layer)

    write_csv(
        args.output_dir / "economic.csv",
        entity_sets["economic"],
        ["entity_id", "geography_entity_id", "period", "unemployment_rate", "inflation_rate"],
    )
    write_csv(
        args.output_dir / "apartment_market.csv",
        entity_sets["apartment_market"],
        [
            "entity_id",
            "geography_entity_id",
            "period",
            "rent_index",
            "rent_growth_1m",
            "rent_growth_12m",
            "region_id",
            "region_name",
            "region_type",
            "state_name",
            "source_dataset",
        ],
    )
    write_csv(
        args.output_dir / "geographic.csv",
        entity_sets["geographic"],
        ["entity_id", "geography_type", "name", "county_fips", "state_fips"],
    )

    print(f"Wrote entity tables to: {args.output_dir}")
    for name, rows in entity_sets.items():
        print(f"- {name}: {len(rows)} rows")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
