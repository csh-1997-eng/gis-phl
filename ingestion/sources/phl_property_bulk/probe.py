"""Philadelphia property bulk download probe."""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

from sources.common import FetchResult, http_get_bytes, scrape_links_from_html, write_bytes


def _looks_like_data_url(url: str) -> bool:
    lower = url.lower()
    if lower.endswith((".css", ".js", ".html", ".htm")):
        return False
    if "api/v2/sql" in lower:
        return True
    return any(
        token in lower
        for token in (
            ".csv",
            ".geojson",
            ".zip",
            ".shp",
            "format=csv",
            "format=geojson",
            "format=shp",
        )
    )


def _with_query_limit(url: str, limit: int = 200) -> str:
    lower = url.lower()
    if "api/v2/sql" not in lower:
        return url
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    query_values = params.get("q")
    if not query_values:
        return url
    sql = query_values[0]
    if " limit " not in sql.lower():
        sql = sql.rstrip().rstrip(";") + f" LIMIT {limit}"
    params["q"] = [sql]
    new_query = urlencode(params, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))


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

        candidates = sorted(set(link for link in links if _looks_like_data_url(link)))
        # Prefer direct CSV API export when available.
        candidates = sorted(
            candidates,
            key=lambda link: ("format=csv" in link.lower() or link.lower().endswith(".csv"), "api/v2/sql" in link.lower()),
            reverse=True,
        )
        candidate = candidates[0] if candidates else None

        details: dict[str, object] = {
            "url": url,
            "asset_url_detected": candidate,
            "candidate_link_count": len(candidates),
            "bytes_sampled": len(page_body),
            "tmp_sample": str(tmp_dir / "property_download_page.html"),
        }

        if candidate:
            fetch_url = _with_query_limit(candidate)
            sample = http_get_bytes(fetch_url, max_bytes=250_000)
            write_bytes(tmp_dir / "property_asset_head.bin", sample)
            details["asset_url_fetched"] = fetch_url
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
        else:
            return [FetchResult(name=name, ok=False, details=details, error="No downloadable property dataset URL found on page")]

        return [FetchResult(name=name, ok=True, details=details)]
    except Exception as exc:  # noqa: BLE001
        return [FetchResult(name=name, ok=False, details={"url": url}, error=str(exc))]
