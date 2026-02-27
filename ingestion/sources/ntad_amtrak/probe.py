"""NTAD Amtrak stations probe."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

from sources.common import FetchResult, http_get_bytes, write_text


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    name = "ntad_amtrak_stations"
    base = (
        "https://services.arcgis.com/xOi1kZaI0eWDREZv/ArcGIS/rest/services/"
        "NTAD_Amtrak_Stations/FeatureServer/0/query"
    )
    params = {
        "where": "1=1",
        "outFields": "*",
        "resultRecordCount": "5",
        "f": "geojson",
    }
    url = f"{base}?{urlencode(params)}"
    try:
        body = http_get_bytes(url, max_bytes=500_000)
        payload = json.loads(body.decode("utf-8", errors="replace"))
        features = payload.get("features", [])
        preview = []
        for feat in features[:5]:
            props = feat.get("properties", {})
            preview.append(
                {
                    "station": props.get("STATION") or props.get("STATION_NM") or props,
                    "city": props.get("CITY") or props.get("CITY_NAME"),
                    "state": props.get("STATE") or props.get("STATE_ABBR"),
                }
            )

        write_text(tmp_dir / "amtrak_sample.geojson", json.dumps(payload, indent=2))
        return [
            FetchResult(
                name=name,
                ok=True,
                details={
                    "url": url,
                    "feature_count": len(features),
                    "preview": preview,
                    "tmp_sample": str(tmp_dir / "amtrak_sample.geojson"),
                },
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [FetchResult(name=name, ok=False, details={"url": url}, error=str(exc))]
