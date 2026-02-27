"""Zillow source probe."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from sources.common import FetchResult, TitleParser, http_get_bytes, write_bytes


def _page_metadata_result(name: str, url: str, tmp_path: Path) -> FetchResult:
    try:
        body = http_get_bytes(url, max_bytes=200_000)
        write_bytes(tmp_path, body)
        parser = TitleParser()
        parser.feed(body.decode("utf-8", errors="replace"))
        return FetchResult(
            name=name,
            ok=True,
            details={
                "url": url,
                "title": parser.title,
                "bytes_sampled": len(body),
                "tmp_sample": str(tmp_path),
            },
        )
    except Exception as exc:  # noqa: BLE001
        return FetchResult(name=name, ok=False, details={"url": url}, error=str(exc))


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir

    results = [
        _page_metadata_result(
            "zillow_research_portal",
            "https://www.zillow.com/research/data/",
            tmp_dir / "research_portal_head.html",
        ),
        _page_metadata_result(
            "zillow_zori_methodology",
            "https://www.zillow.com/research/methodology-zori-repeat-rent-27092/",
            tmp_dir / "zori_methodology_head.html",
        ),
    ]

    zori_url = "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv"
    try:
        body = http_get_bytes(zori_url, max_bytes=350_000)
        write_bytes(tmp_dir / "zori_head.csv", body)
        reader = csv.reader(io.StringIO(body.decode("utf-8", errors="replace")))
        rows = []
        for i, row in enumerate(reader):
            rows.append(row)
            if i >= 5:
                break
        results.append(
            FetchResult(
                name="zillow_zori_sample",
                ok=True,
                details={
                    "url": zori_url,
                    "sample_rows": rows,
                    "bytes_sampled": len(body),
                    "tmp_sample": str(tmp_dir / "zori_head.csv"),
                },
            )
        )
    except Exception as exc:  # noqa: BLE001
        results.append(FetchResult(name="zillow_zori_sample", ok=False, details={"url": zori_url}, error=str(exc)))

    return results
