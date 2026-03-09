"""Census LEHD LODES source probe."""

from __future__ import annotations

import csv
import gzip
import io
from pathlib import Path

from sources.common import FetchResult, http_get_bytes, scrape_links_from_html, write_bytes


def _sample_rows_from_gz(data: bytes, max_rows: int = 5) -> list[list[str]]:
    """Stream-decompress a (possibly truncated) gzip buffer and return sample CSV rows."""
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
        chunks: list[bytes] = []
        while True:
            try:
                chunk = gz.read(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            except EOFError:
                break
    text = b"".join(chunks).decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows: list[list[str]] = []
    for i, row in enumerate(reader):
        rows.append(row)
        if i >= max_rows:
            break
    return rows


BASE_URL = "https://lehd.ces.census.gov/data/lodes/LODES8/"


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    name = "lehd_lodes_directory"
    try:
        body = http_get_bytes(BASE_URL, max_bytes=300_000)
        write_bytes(tmp_dir / "lodes_directory_head.html", body)
        text = body.decode("utf-8", errors="replace")
        links = scrape_links_from_html(BASE_URL, text)
        pa_dir_links = [link for link in links if link.lower().rstrip("/").endswith("/pa")]
        if not pa_dir_links:
            raise RuntimeError("PA directory link was not found in LODES8 index")
        pa_dir_url = pa_dir_links[0]

        pa_body = http_get_bytes(pa_dir_url, max_bytes=350_000)
        write_bytes(tmp_dir / "pa_directory_head.html", pa_body)
        pa_text = pa_body.decode("utf-8", errors="replace")
        pa_links = scrape_links_from_html(pa_dir_url, pa_text)
        csv_gz_links = [link for link in pa_links if link.lower().endswith(".csv.gz")]
        pa_candidates = [link for link in csv_gz_links if "jt00" in link.lower()]

        # In LODES8, most jt00 extracts live under od/rac/wac subdirectories.
        pa_subdirs = [
            link
            for link in pa_links
            if link.lower().rstrip("/").endswith(("/od", "/rac", "/wac"))
        ]
        subdir_scan_counts: dict[str, int] = {}
        for subdir_url in pa_subdirs:
            subdir_body = http_get_bytes(subdir_url, max_bytes=350_000)
            subdir_name = subdir_url.rstrip("/").split("/")[-1]
            write_bytes(tmp_dir / f"pa_{subdir_name}_directory_head.html", subdir_body)
            subdir_text = subdir_body.decode("utf-8", errors="replace")
            subdir_links = scrape_links_from_html(subdir_url, subdir_text)
            subdir_csv = [link for link in subdir_links if link.lower().endswith(".csv.gz")]
            subdir_scan_counts[subdir_name] = len(subdir_csv)
            pa_candidates.extend(link for link in subdir_csv if "jt00" in link.lower())
            csv_gz_links.extend(subdir_csv)

        details: dict[str, object] = {
            "url": BASE_URL,
            "pa_directory_url": pa_dir_url,
            "bytes_sampled": len(body),
            "csv_gz_link_count": len(csv_gz_links),
            "pa_jt00_candidate_count": len(pa_candidates),
            "tmp_sample": str(tmp_dir / "lodes_directory_head.html"),
            "pa_directory_tmp_sample": str(tmp_dir / "pa_directory_head.html"),
            "pa_subdir_counts": subdir_scan_counts,
        }

        if not pa_candidates:
            xwalk_candidates = [link for link in csv_gz_links if link.lower().endswith("pa_xwalk.csv.gz")]
            if xwalk_candidates:
                resource_url = xwalk_candidates[0]
                resource = http_get_bytes(resource_url, max_bytes=250_000)
                write_bytes(tmp_dir / "pa_lodes_head.csv.gz", resource)
                details["resource_url"] = resource_url
                details["resource_bytes_sampled"] = len(resource)
                details["resource_tmp_sample"] = str(tmp_dir / "pa_lodes_head.csv.gz")
                details["probe_mode"] = "xwalk_fallback"
                details["sample_rows"] = _sample_rows_from_gz(resource)
                return [FetchResult(name=name, ok=True, details=details)]
            raise RuntimeError("No PA jt00 .csv.gz file candidates found in LODES8/pa, od/, rac/, or wac/")

        resource_url = sorted(pa_candidates)[0]
        resource = http_get_bytes(resource_url, max_bytes=250_000)
        write_bytes(tmp_dir / "pa_lodes_head.csv.gz", resource)
        details["resource_url"] = resource_url
        details["resource_bytes_sampled"] = len(resource)
        details["resource_tmp_sample"] = str(tmp_dir / "pa_lodes_head.csv.gz")
        details["sample_rows"] = _sample_rows_from_gz(resource)

        return [FetchResult(name=name, ok=True, details=details)]
    except Exception as exc:  # noqa: BLE001
        return [FetchResult(name=name, ok=False, details={"url": BASE_URL}, error=str(exc))]
