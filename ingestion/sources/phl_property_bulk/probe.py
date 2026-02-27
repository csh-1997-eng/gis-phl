"""Philadelphia property bulk download probe."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from urllib.parse import urljoin

from sources.common import FetchResult, http_get_bytes, scrape_links_from_html, write_bytes


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    name = "phl_property_bulk_download"
    url = "https://cityofphiladelphia.github.io/property-download/"
    try:
        page_body = http_get_bytes(url, max_bytes=300_000)
        write_bytes(tmp_dir / "property_download_page.html", page_body)
        page = page_body.decode("utf-8", errors="replace")
        links = scrape_links_from_html(url, page)
        raw_url_matches = re.findall(r"https?://[^\"'\\s>]+", page)
        token_matches = re.findall(
            r"(?:/[^\"'\\s>]+(?:download|csv|geojson|zip|shp)[^\"'\\s>]*)",
            page,
        )
        links.extend(raw_url_matches)
        links.extend(urljoin(url, token) for token in token_matches)

        candidate = None
        for link in links:
            lower = link.lower()
            if (
                any(lower.endswith(ext) for ext in (".csv", ".geojson", ".zip", ".shp"))
                or "download" in lower
                or "format=csv" in lower
                or "format=geojson" in lower
            ):
                candidate = link
                break

        details: dict[str, object] = {
            "url": url,
            "asset_url_detected": candidate,
            "candidate_link_count": len(links),
            "bytes_sampled": len(page_body),
            "tmp_sample": str(tmp_dir / "property_download_page.html"),
        }

        if candidate:
            sample = http_get_bytes(candidate, max_bytes=250_000)
            write_bytes(tmp_dir / "property_asset_head.bin", sample)
            details["asset_bytes_sampled"] = len(sample)
            details["asset_tmp_sample"] = str(tmp_dir / "property_asset_head.bin")
            decoded = sample.decode("utf-8", errors="replace")
            if candidate.lower().endswith(".csv") or "," in decoded.splitlines()[0]:
                reader = csv.reader(io.StringIO(sample.decode("utf-8", errors="replace")))
                rows = []
                for i, row in enumerate(reader):
                    rows.append(row)
                    if i >= 5:
                        break
                details["asset_sample_rows"] = rows
            else:
                details["asset_first_64_hex"] = sample[:64].hex()

        return [FetchResult(name=name, ok=True, details=details)]
    except Exception as exc:  # noqa: BLE001
        return [FetchResult(name=name, ok=False, details={"url": url}, error=str(exc))]
