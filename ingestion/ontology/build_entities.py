#!/usr/bin/env python3
"""Build ontology-aligned entity tables from source sample files."""

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

DEFAULT_SOURCE_DIR = Path("ingestion/tmp/source_samples")
DEFAULT_OUTPUT_DIR = Path("ingestion/tmp/entities")


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


def build_entities(source_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    fred_rows = load_fred_entities_from_csv(source_dir / "fred" / "philly_unemployment_head.csv")

    apt_rows = load_zori_apartment_market_entities_from_csv(source_dir / "zillow" / "zori_head.csv")

    ntad_features = load_ntad_geojson_features(source_dir / "ntad_amtrak" / "amtrak_sample.geojson")
    amtrak_geo_rows = [map_ntad_feature_to_geographic(feat) for feat in ntad_features]

    geographic_rows = base_geographic_entities() + zori_geographic_entities(apt_rows) + amtrak_geo_rows
    geographic_rows = unique_by_key(geographic_rows, "entity_id")

    return {
        "economic": fred_rows,
        "apartment_market": apt_rows,
        "geographic": geographic_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ontology-aligned entity tables")
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Source sample directory (from minimal ingest)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for entity CSVs",
    )
    args = parser.parse_args()

    entity_sets = build_entities(args.source_dir)

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
