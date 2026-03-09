"""Census ACS 5-year source probe."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode

from sources.common import FetchResult, first_successful_url, http_get_bytes, write_bytes


ACS_YEAR = "2023"


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    results: list[FetchResult] = []

    vars_url = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5/variables.json"
    vars_name = "acs_5y_variables"
    try:
        body = http_get_bytes(vars_url)
        write_bytes(tmp_dir / "variables_head.json", body)
        payload = json.loads(body.decode("utf-8", errors="replace"))
        variables = payload.get("variables", {}) if isinstance(payload, dict) else {}
        if not variables:
            raise RuntimeError("ACS variables payload did not include a non-empty 'variables' object")
        sample_keys = sorted(list(variables.keys()))[:15]
        results.append(
            FetchResult(
                name=vars_name,
                ok=True,
                details={
                    "url": vars_url,
                    "acs_year": ACS_YEAR,
                    "variable_count_sampled": len(variables),
                    "sample_variable_keys": sample_keys,
                    "tmp_sample": str(tmp_dir / "variables_head.json"),
                },
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(FetchResult(name=vars_name, ok=False, details={"url": vars_url, "acs_year": ACS_YEAR}, error=str(exc)))

    query_candidates = [
        f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5?"
        + urlencode(
            {
                "get": "NAME,B25064_001E,B25003_001E,B25003_003E",
                "for": "zip code tabulation area:19104",
            }
        ),
        f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5?"
        + urlencode(
            {
                "get": "NAME,B25064_001E,B25003_001E,B25003_003E",
                "for": "zip code tabulation area:19104",
                "in": "state:42",
            }
        ),
    ]
    query_url = query_candidates[0]
    query_name = "acs_5y_philly_zcta_sample"
    try:
        query_url, body = first_successful_url(query_candidates, max_bytes=200_000)
        write_bytes(tmp_dir / "philly_zcta_sample.json", body)
        payload = json.loads(body.decode("utf-8", errors="replace"))
        if isinstance(payload, list) and payload and isinstance(payload[0], list) and payload[0] and payload[0][0] == "error":
            raise RuntimeError(str(payload[0]))
        results.append(
            FetchResult(
                name=query_name,
                ok=True,
                details={
                    "url": query_url,
                    "candidate_urls_tried": query_candidates,
                    "acs_year": ACS_YEAR,
                    "rows_sampled": len(payload) - 1 if isinstance(payload, list) and len(payload) > 0 else 0,
                    "header": payload[0] if isinstance(payload, list) and payload else [],
                    "sample_rows": payload[1:6] if isinstance(payload, list) else [],
                    "tmp_sample": str(tmp_dir / "philly_zcta_sample.json"),
                },
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(
            FetchResult(
                name=query_name,
                ok=False,
                details={"url": query_url, "candidate_urls_tried": query_candidates, "acs_year": ACS_YEAR},
                error=str(exc),
            )
        )

    return results
