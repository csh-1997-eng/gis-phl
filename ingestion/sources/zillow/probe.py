"""Zillow source probe."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from sources.common import FetchResult, http_get_bytes, write_bytes


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir

    results: list[FetchResult] = []

    zori_feeds = [
        (
            "zillow_zori_sample_metro",
            "metro",
            "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv",
            450_000,
        ),
        (
            "zillow_zori_sample_city",
            "city",
            "https://files.zillowstatic.com/research/public_csvs/zori/City_zori_uc_sfrcondomfr_sm_month.csv",
            900_000,
        ),
        (
            "zillow_zori_sample_zip",
            "zip",
            "https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv",
            1_400_000,
        ),
    ]

    for result_name, dataset_key, zori_url, max_bytes in zori_feeds:
        try:
            body = http_get_bytes(zori_url, max_bytes=max_bytes)
            tmp_path = tmp_dir / f"{dataset_key}_zori_head.csv"
            write_bytes(tmp_path, body)

            reader = csv.reader(io.StringIO(body.decode("utf-8", errors="replace")))
            rows = []
            for i, row in enumerate(reader):
                rows.append(row)
                if i >= 5:
                    break

            results.append(
                FetchResult(
                    name=result_name,
                    ok=True,
                    details={
                        "dataset_key": dataset_key,
                        "url": zori_url,
                        "sample_rows": rows,
                        "bytes_sampled": len(body),
                        "tmp_sample": str(tmp_path),
                    },
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                FetchResult(
                    name=result_name,
                    ok=False,
                    details={"dataset_key": dataset_key, "url": zori_url},
                    error=str(exc),
                )
            )

    return results
