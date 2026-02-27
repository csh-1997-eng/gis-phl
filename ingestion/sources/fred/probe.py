"""FRED source probe."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from sources.common import FetchResult, http_get_bytes, write_bytes


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    name = "fred_philly_unemployment"
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=PHIL942UR"
    try:
        body = http_get_bytes(url, max_bytes=250_000)
        write_bytes(tmp_dir / "philly_unemployment_head.csv", body)
        rows = list(csv.reader(io.StringIO(body.decode("utf-8", errors="replace"))) )
        header = rows[0] if rows else []
        sample = rows[-12:] if len(rows) > 12 else rows
        return [
            FetchResult(
                name=name,
                ok=True,
                details={
                    "url": url,
                    "header": header,
                    "sample_last_rows": sample,
                    "row_count_sampled": len(rows),
                    "tmp_sample": str(tmp_dir / "philly_unemployment_head.csv"),
                },
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [FetchResult(name=name, ok=False, details={"url": url}, error=str(exc))]
