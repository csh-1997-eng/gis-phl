"""OpenDataPhilly L&I property history probe.

The OpenDataPhilly dataset page links only to li.phila.gov/Property-History,
a Vue.js web app with no direct download. The underlying data is served via
the Philadelphia Carto SQL API across three tables: li_permits, li_violations,
and li_appeals. We probe those directly.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from sources.common import FetchResult, http_get_bytes, write_bytes


DATASET_SLUG = "licenses-and-inspections-property-history"
DATASET_URL = f"https://opendataphilly.org/datasets/{DATASET_SLUG}/"

CARTO_BASE = "https://phl.carto.com/api/v2/sql"

# Each entry: (result_name, table, columns_to_select)
CARTO_PROBES: list[tuple[str, str, str]] = [
    (
        "li_permits",
        "li_permits",
        "objectid,addresskey,opa_account_num,address,zip,ownername,permitnumber,permittype,permitdescription,permitissuedate,status",
    ),
    (
        "li_violations",
        "li_violations",
        "objectid,addresskey,opa_account_num,address,zip,ownername,casenumber,violationtype,violationdescription,violationdate,status",
    ),
    (
        "li_appeals",
        "li_appeals",
        "objectid,addresskey,opa_account_num,address,zip,ownername,primaryapplicant,applictype,processeddate,decision,decisiondate",
    ),
]


def _carto_csv_url(table: str, columns: str, limit: int = 5) -> str:
    q = f"SELECT {columns} FROM {table} LIMIT {limit}"
    encoded = q.replace(" ", "+").replace(",", "%2C").replace("*", "%2A")
    return f"{CARTO_BASE}?q={encoded}&format=csv"


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir

    results: list[FetchResult] = []
    for probe_name, table, columns in CARTO_PROBES:
        name = f"li_property_history_{probe_name}"
        url = _carto_csv_url(table, columns)
        try:
            body = http_get_bytes(url, max_bytes=250_000)
            write_bytes(tmp_dir / f"{probe_name}_head.csv", body)
            decoded = body.decode("utf-8", errors="replace")
            reader = csv.reader(io.StringIO(decoded))
            rows = [row for i, row in enumerate(reader) if i <= 5]
            results.append(
                FetchResult(
                    name=name,
                    ok=True,
                    details={
                        "dataset_slug": DATASET_SLUG,
                        "dataset_url": DATASET_URL,
                        "carto_table": table,
                        "resource_url": url,
                        "resource_bytes_sampled": len(body),
                        "sample_rows": rows,
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                FetchResult(
                    name=name,
                    ok=False,
                    details={
                        "dataset_slug": DATASET_SLUG,
                        "dataset_url": DATASET_URL,
                        "carto_table": table,
                        "resource_url": url,
                    },
                    error=str(exc),
                )
            )

    return results
