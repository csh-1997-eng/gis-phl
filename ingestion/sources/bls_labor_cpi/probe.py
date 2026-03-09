"""BLS labor + CPI source probe."""

from __future__ import annotations

from pathlib import Path

from sources.common import FetchResult, http_get_bytes, write_bytes


BLS_EAG_PHILLY_COUNTY_URL = "https://www.bls.gov/eag/eag.pa_philadelphia_co.htm"
BLS_LA_AREA_URL = "https://download.bls.gov/pub/time.series/la/la.area"
BLS_CU_AREA_URL = "https://download.bls.gov/pub/time.series/cu/cu.area"
BLS_EAG_LANDING_URL = "https://www.bls.gov/eag/"
BLS_LA_DIRECTORY_URL = "https://download.bls.gov/pub/time.series/la/"
BLS_CU_DIRECTORY_URL = "https://download.bls.gov/pub/time.series/cu/"


def _matching_lines(text: str, needle: str, limit: int = 12) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        if needle.lower() in line.lower():
            out.append(line)
            if len(out) >= limit:
                break
    return out


def _probe_with_metadata_fallback(
    *,
    name: str,
    primary_url: str,
    metadata_urls: list[str],
    tmp_filename: str,
    max_bytes: int,
    needle: str | None = None,
) -> FetchResult:
    try:
        body = http_get_bytes(primary_url, max_bytes=max_bytes)
        write_bytes(Path(tmp_filename), body)
        details: dict[str, object] = {
            "url": primary_url,
            "bytes_sampled": len(body),
            "tmp_sample": tmp_filename,
        }
        if needle:
            text = body.decode("utf-8", errors="replace")
            details["philly_matches"] = _matching_lines(text, needle)
        return FetchResult(name=name, ok=True, details=details)
    except Exception as primary_exc:  # noqa: BLE001
        metadata_errors: list[str] = []
        for metadata_url in metadata_urls:
            try:
                body = http_get_bytes(metadata_url, max_bytes=180_000)
                meta_path = str(Path(tmp_filename).with_name(Path(tmp_filename).stem + "_metadata.html"))
                write_bytes(Path(meta_path), body)
                return FetchResult(
                    name=name,
                    ok=True,
                    details={
                        "probe_mode": "metadata_only",
                        "url": primary_url,
                        "metadata_url": metadata_url,
                        "bytes_sampled": len(body),
                        "fetch_error": str(primary_exc),
                        "tmp_sample": meta_path,
                    },
                )
            except Exception as meta_exc:  # noqa: BLE001
                metadata_errors.append(f"{metadata_url} -> {meta_exc}")

        return FetchResult(
            name=name,
            ok=False,
            details={"url": primary_url, "metadata_urls_tried": metadata_urls, "metadata_errors": metadata_errors[:3]},
            error=str(primary_exc),
        )


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    results: list[FetchResult] = []

    results.append(
        _probe_with_metadata_fallback(
            name="bls_labor_area_lookup",
            primary_url=BLS_LA_AREA_URL,
            metadata_urls=[BLS_LA_DIRECTORY_URL],
            tmp_filename=str(tmp_dir / "la_area_head.txt"),
            max_bytes=600_000,
            needle="Philadelphia",
        )
    )

    results.append(
        _probe_with_metadata_fallback(
            name="bls_cpi_area_lookup",
            primary_url=BLS_CU_AREA_URL,
            metadata_urls=[BLS_CU_DIRECTORY_URL],
            tmp_filename=str(tmp_dir / "cu_area_head.txt"),
            max_bytes=400_000,
            needle="Philadelphia",
        )
    )

    return results
