"""OpenDataPhilly rental suitability probe."""

from __future__ import annotations

import csv
import io
from pathlib import Path

from sources.common import FetchResult, http_get_bytes, scrape_links_from_html, write_bytes


DATASET_SLUG = "certified-for-rental-suitability"


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    name = "opendataphilly_rental_suitability"
    dataset_url = f"https://opendataphilly.org/datasets/{DATASET_SLUG}/"
    try:
        page_body = http_get_bytes(dataset_url, max_bytes=350_000)
        write_bytes(tmp_dir / "dataset_page.html", page_body)
        page_text = page_body.decode("utf-8", errors="replace")
        links = scrape_links_from_html(dataset_url, page_text)
        candidate_links = [
            link
            for link in links
            if any(ext in link.lower() for ext in (".csv", ".json", ".geojson", ".zip", "download"))
        ]

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
                sample_body = http_get_bytes(link, max_bytes=250_000)
                write_bytes(tmp_dir / "resource_head.bin", sample_body)
                details["resource_url"] = link
                details["resource_bytes_sampled"] = len(sample_body)
                details["resource_tmp_sample"] = str(tmp_dir / "resource_head.bin")
                decoded = sample_body.decode("utf-8", errors="replace")
                if link.lower().endswith(".csv") or "," in decoded.splitlines()[0]:
                    reader = csv.reader(io.StringIO(decoded))
                    rows = []
                    for i, row in enumerate(reader):
                        rows.append(row)
                        if i >= 5:
                            break
                    details["sample_rows"] = rows
                else:
                    details["sample_text_head"] = decoded[:500]
                return [FetchResult(name=name, ok=True, details=details)]
            except Exception as link_exc:  # noqa: BLE001
                link_errors.append(f"{link} -> {link_exc}")

        details["resource_fetch_errors"] = link_errors[:5]
        details["probe_mode"] = "metadata_only"
        return [FetchResult(name=name, ok=True, details=details)]
    except Exception as exc:  # noqa: BLE001
        return [
            FetchResult(
                name=name,
                ok=False,
                details={"dataset_slug": DATASET_SLUG, "dataset_url": dataset_url},
                error=str(exc),
            )
        ]
