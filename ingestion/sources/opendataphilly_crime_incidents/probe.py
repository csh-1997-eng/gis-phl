"""OpenDataPhilly crime incidents probe."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from sources.common import FetchResult, http_get_bytes, scrape_links_from_html, write_bytes


DATASET_SLUG = "crime-incidents"


def _looks_like_resource_url(url: str) -> bool:
    lower = url.lower()
    return any(
        token in lower
        for token in (
            ".csv",
            ".json",
            ".geojson",
            ".zip",
            ".shp",
            "format=csv",
            "format=json",
            "format=geojson",
            "download",
        )
    )


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    name = "opendataphilly_crime_incidents"
    dataset_url = f"https://opendataphilly.org/datasets/{DATASET_SLUG}/"
    try:
        page_body = http_get_bytes(dataset_url, max_bytes=350_000)
        write_bytes(tmp_dir / "dataset_page.html", page_body)
        page_text = page_body.decode("utf-8", errors="replace")

        links = scrape_links_from_html(dataset_url, page_text)
        links.extend(re.findall(r"https?://[^\"'\\s>]+", page_text))
        candidate_links = [link for link in links if _looks_like_resource_url(link)]
        # Favor CSV API resources first for deterministic sampling.
        candidate_links = sorted(
            set(candidate_links),
            key=lambda link: (("format=csv" in link.lower()) or link.lower().endswith(".csv"), "api/v2/sql" in link.lower()),
            reverse=True,
        )

        if not candidate_links:
            dataset_ids = sorted(set(re.findall(r"/datasets/([a-f0-9_]{20,})", page_text, flags=re.IGNORECASE)))
            for dataset_id in dataset_ids:
                candidate_links.append(
                    f"https://hub.arcgis.com/api/v3/datasets/{dataset_id}/downloads/data?format=csv&spatialRefId=3857&where=1%3D1"
                )

        details: dict[str, object] = {
            "dataset_slug": DATASET_SLUG,
            "dataset_url": dataset_url,
            "bytes_sampled": len(page_body),
            "candidate_link_count": len(candidate_links),
            "tmp_sample": str(tmp_dir / "dataset_page.html"),
        }

        link_errors: list[str] = []
        for link in candidate_links[:10]:
            try:
                sample = http_get_bytes(link, max_bytes=250_000)
                write_bytes(tmp_dir / "resource_head.bin", sample)
                details["resource_url"] = link
                details["resource_bytes_sampled"] = len(sample)
                details["resource_tmp_sample"] = str(tmp_dir / "resource_head.bin")
                decoded = sample.decode("utf-8", errors="replace")
                lines = decoded.splitlines()
                if link.lower().endswith(".csv") or (lines and "," in lines[0]):
                    reader = csv.reader(io.StringIO(decoded))
                    rows = []
                    for i, row in enumerate(reader):
                        rows.append(row)
                        if i >= 5:
                            break
                    details["sample_rows"] = rows
                else:
                    details["sample_text_head"] = decoded[:600]
                return [FetchResult(name=name, ok=True, details=details)]
            except Exception as link_exc:  # noqa: BLE001
                link_errors.append(f"{link} -> {link_exc}")

        details["resource_fetch_errors"] = link_errors[:8]
        return [
            FetchResult(
                name=name,
                ok=False,
                details=details,
                error="No downloadable crime incidents resource could be fetched",
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [FetchResult(name=name, ok=False, details={"dataset_slug": DATASET_SLUG, "dataset_url": dataset_url}, error=str(exc))]
