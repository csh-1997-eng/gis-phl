"""SEPTA GTFS-RT probe."""

from __future__ import annotations

import os
import re
from pathlib import Path

from sources.common import FetchResult, first_successful_url, http_get_bytes, write_bytes


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    name = "septa_gtfs_rt_probe"
    url_candidates = [
        "https://www3.septa.org/api/gtfsrt/septa-pa-us/TripUpdate.pb",
        "https://www3.septa.org/api/gtfsrt/TripUpdate.pb",
        "https://www3.septa.org/api/gtfsrt/septa-pa-us/VehiclePosition.pb",
        "https://www3.septa.org/api/gtfsrt/VehiclePosition.pb",
    ]
    env_candidates = [item.strip() for item in os.getenv("SEPTA_GTFS_RT_URLS", "").split(",") if item.strip()]
    if env_candidates:
        url_candidates = env_candidates + url_candidates
    try:
        url, body = first_successful_url(url_candidates, max_bytes=4096)
        write_bytes(tmp_dir / "gtfs_rt_probe.pb", body)
        return [
            FetchResult(
                name=name,
                ok=True,
                details={
                    "url": url,
                    "bytes_sampled": len(body),
                    "first_32_hex": body[:32].hex(),
                    "tmp_sample": str(tmp_dir / "gtfs_rt_probe.pb"),
                },
            )
        ]
    except Exception as exc:  # noqa: BLE001
        # Attempt to discover current feed URLs from SEPTA developer page.
        try:
            dev_url = "https://www3.septa.org/developer/"
            dev_body = http_get_bytes(dev_url, max_bytes=300_000)
            dev_text = dev_body.decode("utf-8", errors="replace")
            discovered = sorted(set(re.findall(r"https://[^\"'\\s]+\\.pb", dev_text)))
            if discovered:
                url, body = first_successful_url(discovered, max_bytes=4096)
                write_bytes(tmp_dir / "gtfs_rt_probe.pb", body)
                write_bytes(tmp_dir / "gtfs_rt_metadata_sample.html", dev_body)
                return [
                    FetchResult(
                        name=name,
                        ok=True,
                        details={
                            "url": url,
                            "bytes_sampled": len(body),
                            "first_32_hex": body[:32].hex(),
                            "discovered_feed_candidates": discovered,
                            "tmp_sample": str(tmp_dir / "gtfs_rt_probe.pb"),
                            "metadata_tmp_sample": str(tmp_dir / "gtfs_rt_metadata_sample.html"),
                        },
                    )
                ]
        except Exception:
            pass

        metadata_candidates = [
            "https://www3.septa.org/developer/",
            "https://catalog.data.gov/dataset/septa-gtfs-real-time-alerts-and-updates",
        ]
        for meta_url in metadata_candidates:
            try:
                meta_body = http_get_bytes(meta_url, max_bytes=150_000)
                write_bytes(tmp_dir / "gtfs_rt_metadata_sample.html", meta_body)
                return [
                    FetchResult(
                        name=name,
                        ok=True,
                        details={
                            "probe_mode": "metadata_only",
                            "metadata_url": meta_url,
                            "bytes_sampled": len(meta_body),
                            "feed_url_candidates_tried": url_candidates,
                            "feed_error": str(exc),
                            "tmp_sample": str(tmp_dir / "gtfs_rt_metadata_sample.html"),
                        },
                    )
                ]
            except Exception:
                continue

        return [
            FetchResult(
                name=name,
                ok=False,
                details={"url_candidates": url_candidates},
                error=str(exc),
            )
        ]
