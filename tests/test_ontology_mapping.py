from __future__ import annotations

import csv
from pathlib import Path

from exploration.ontology.map_to_entities import map_zori_observation_to_apartment_market
from exploration.ontology.map_to_entities import load_zori_apartment_market_entities_from_csv


def test_zori_city_geography_id_uses_region_id_not_name_slug() -> None:
    richmond_va = map_zori_observation_to_apartment_market(
        region_id="6752",
        region_name="Richmond",
        region_type="city",
        state_name="VA",
        source_dataset="city_zori.csv",
        period="2025-01-31",
        rent_index=1800.0,
        prev_1m=1790.0,
        prev_12m=1700.0,
    )
    richmond_tx = map_zori_observation_to_apartment_market(
        region_id="47379",
        region_name="Richmond",
        region_type="city",
        state_name="TX",
        source_dataset="city_zori.csv",
        period="2025-01-31",
        rent_index=1600.0,
        prev_1m=1595.0,
        prev_12m=1500.0,
    )

    assert richmond_va["geography_entity_id"] == "geo:zori:city:6752"
    assert richmond_tx["geography_entity_id"] == "geo:zori:city:47379"
    assert richmond_va["geography_entity_id"] != richmond_tx["geography_entity_id"]


def test_zori_loader_ignores_non_date_metadata_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(
            fp,
            fieldnames=[
                "RegionID",
                "SizeRank",
                "RegionName",
                "RegionType",
                "StateName",
                "State",
                "Metro",
                "CountyName",
                "2015-01-31",
                "2015-02-28",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "RegionID": "13271",
                "SizeRank": "1",
                "RegionName": "Philadelphia",
                "RegionType": "city",
                "StateName": "PA",
                "State": "PA",
                "Metro": "Philadelphia",
                "CountyName": "Philadelphia",
                "2015-01-31": "1500",
                "2015-02-28": "1515",
            }
        )

    entities = load_zori_apartment_market_entities_from_csv(csv_path)

    assert [row["period"] for row in entities] == ["2015-01-31", "2015-02-28"]
