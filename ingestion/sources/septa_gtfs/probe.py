"""SEPTA GTFS probe."""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

from sources.common import FetchResult, first_successful_url, write_bytes


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    name = "septa_gtfs"
    url_candidates = [
        "https://www3.septa.org/developer/gtfs_public.zip",
        "https://www3.septa.org/developer/google_transit.zip",
        "https://www3.septa.org/hackathon/google_transit.zip",
    ]
    try:
        url, body = first_successful_url(url_candidates)
        full_zip_path = tmp_dir / "gtfs_public.zip"
        write_bytes(full_zip_path, body)
        nested_written_path: Path | None = None

        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            names = zf.namelist()
            sample_tables: dict[str, list[list[str]]] = {}
            for member in ["agency.txt", "stops.txt", "routes.txt", "trips.txt"]:
                if member in names:
                    text = zf.read(member).decode("utf-8", errors="replace")
                    reader = csv.reader(io.StringIO(text))
                    sample_rows = []
                    for i, row in enumerate(reader):
                        sample_rows.append(row)
                        if i >= 5:
                            break
                    sample_tables[member] = sample_rows

            # Some SEPTA endpoints now return a wrapper ZIP containing another ZIP.
            if not sample_tables:
                nested_zip_members = [member for member in names if member.lower().endswith(".zip")]
                for nested_member in nested_zip_members:
                    try:
                        nested_body = zf.read(nested_member)
                        nested_written_path = tmp_dir / "gtfs_nested.zip"
                        write_bytes(nested_written_path, nested_body)
                        with zipfile.ZipFile(io.BytesIO(nested_body)) as nested_zf:
                            nested_names = nested_zf.namelist()
                            for member in ["agency.txt", "stops.txt", "routes.txt", "trips.txt"]:
                                if member not in nested_names:
                                    continue
                                text = nested_zf.read(member).decode("utf-8", errors="replace")
                                reader = csv.reader(io.StringIO(text))
                                sample_rows = []
                                for i, row in enumerate(reader):
                                    sample_rows.append(row)
                                    if i >= 5:
                                        break
                                sample_tables[f"{nested_member}:{member}"] = sample_rows
                            if sample_tables:
                                break
                    except Exception:
                        continue

        return [
            FetchResult(
                name=name,
                ok=True,
                details={
                    "url": url,
                    "zip_bytes": len(body),
                    "zip_member_count": len(names),
                    "zip_members_preview": names[:20],
                    "sample_tables": sample_tables,
                    "tmp_sample": str(full_zip_path),
                    "tmp_nested_zip": str(nested_written_path) if nested_written_path else None,
                },
            )
        ]
    except Exception as exc:  # noqa: BLE001
        return [
            FetchResult(
                name=name,
                ok=False,
                details={"url_candidates": url_candidates},
                error=str(exc),
            )
        ]
