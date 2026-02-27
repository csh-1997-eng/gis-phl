"""Mapping functions from source payloads into canonical ontology entities."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _slugify(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_")


def map_fred_row_to_economic(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map a FRED unemployment row into an economic entity dictionary."""
    period = str(row.get("observation_date", "")).strip()
    return {
        "entity_id": f"economic:phl_msa:{period}",
        "geography_entity_id": "geo:phl_msa",
        "period": period,
        "unemployment_rate": _to_float(row.get("PHIL942UR")),
        "inflation_rate": None,
    }


def map_zori_observation_to_apartment_market(
    region_id: str,
    region_name: str,
    period: str,
    rent_index: float | None,
    prev_1m: float | None,
    prev_12m: float | None,
) -> Dict[str, Any]:
    """Map one Zillow ZORI region-period observation to apartment_market."""
    geo_slug = _slugify(region_name) if region_name else str(region_id)
    rent_growth_1m = None
    rent_growth_12m = None
    if rent_index is not None and prev_1m not in (None, 0.0):
        rent_growth_1m = (rent_index / prev_1m) - 1.0
    if rent_index is not None and prev_12m not in (None, 0.0):
        rent_growth_12m = (rent_index / prev_12m) - 1.0

    return {
        "entity_id": f"apt_market:{region_id}:{period}",
        "geography_entity_id": f"geo:zori:{geo_slug}",
        "period": period,
        "rent_index": rent_index,
        "rent_growth_1m": rent_growth_1m,
        "rent_growth_12m": rent_growth_12m,
    }


def load_fred_entities_from_csv(csv_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            mapped = map_fred_row_to_economic(row)
            if not mapped["period"]:
                continue
            rows.append(mapped)
    return rows


def load_zori_apartment_market_entities_from_csv(csv_path: Path) -> List[Dict[str, Any]]:
    entities: List[Dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        if reader.fieldnames is None:
            return entities

        meta_cols = {"RegionID", "SizeRank", "RegionName", "RegionType", "StateName"}
        period_cols = [col for col in reader.fieldnames if col not in meta_cols]

        for row in reader:
            region_id = str(row.get("RegionID", "")).strip()
            region_name = str(row.get("RegionName", "")).strip()
            values: List[float | None] = [_to_float(row.get(period)) for period in period_cols]
            for idx, period in enumerate(period_cols):
                rent_index = values[idx]
                prev_1m = values[idx - 1] if idx >= 1 else None
                prev_12m = values[idx - 12] if idx >= 12 else None
                entities.append(
                    map_zori_observation_to_apartment_market(
                        region_id=region_id,
                        region_name=region_name,
                        period=period,
                        rent_index=rent_index,
                        prev_1m=prev_1m,
                        prev_12m=prev_12m,
                    )
                )
    return entities


def map_ntad_feature_to_geographic(feature: Dict[str, Any]) -> Dict[str, Any]:
    props = feature.get("properties", {})
    station_code = str(props.get("Code", "")).strip() or str(props.get("OBJECTID", "unknown"))
    station_name = str(props.get("StationName", "")).strip() or str(props.get("Name", "")).strip()
    return {
        "entity_id": f"geo:amtrak_station:{station_code.lower()}",
        "geography_type": "amtrak_station",
        "name": station_name or station_code,
        "county_fips": None,
        "state_fips": None,
    }


def unique_by_key(rows: Iterable[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for row in rows:
        value = row.get(key)
        if value in seen:
            continue
        seen.add(value)
        deduped.append(row)
    return deduped


def base_geographic_entities() -> List[Dict[str, Any]]:
    return [
        {
            "entity_id": "geo:phl_msa",
            "geography_type": "msa",
            "name": "Philadelphia-Camden-Wilmington, PA-NJ-DE-MD MSA",
            "county_fips": None,
            "state_fips": None,
        }
    ]


def zori_geographic_entities(apartment_market_rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for row in apartment_market_rows:
        geo_id = str(row.get("geography_entity_id", "")).strip()
        if not geo_id:
            continue
        output.append(
            {
                "entity_id": geo_id,
                "geography_type": "zori_region",
                "name": geo_id.replace("geo:zori:", "").replace("_", " ").title(),
                "county_fips": None,
                "state_fips": None,
            }
        )
    return unique_by_key(output, "entity_id")
