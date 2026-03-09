"""HUD Fair Market Rents source probe."""

from __future__ import annotations

import csv
import io
from pathlib import Path
from urllib.parse import urlparse

from sources.common import FetchResult, http_get_bytes, scrape_links_from_html, write_bytes


FMR_PORTAL_URL = "https://www.huduser.gov/portal/datasets/fmr.html"


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _candidate_score(url: str) -> tuple[int, int]:
    lower = url.lower()
    score = 0
    if "county" in lower:
        score += 4
    if "fmr" in lower:
        score += 3
    if "50" in lower:
        score += 2
    if lower.endswith(".csv"):
        score += 10
    if "2026" in lower:
        score += 4
    elif "2025" in lower:
        score += 3
    elif "2024" in lower:
        score += 2
    return score, -len(url)


def _is_tabular_download(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith((".csv", ".txt", ".zip", ".xlsx", ".xls"))


def probe(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    del output_dir
    results: list[FetchResult] = []
    portal_links: list[str] = []

    # Scrape the portal page for discovered download candidates (not emitted as a result).
    try:
        body = http_get_bytes(FMR_PORTAL_URL, max_bytes=250_000)
        write_bytes(tmp_dir / "fmr_portal_head.html", body)
        portal_links = scrape_links_from_html(FMR_PORTAL_URL, body.decode("utf-8", errors="replace"))
    except Exception:  # noqa: BLE001
        pass

    static_candidates = [
        "https://www.huduser.gov/portal/datasets/fmr/fmr2026/fy2026fmr_50_county_rev.csv",
        "https://www.huduser.gov/portal/datasets/fmr/fmr2025/fy2025fmr_50_county_rev.csv",
        "https://www.huduser.gov/portal/datasets/fmr/fmr2024/fy2024fmr_50_county_rev.csv",
    ]
    discovered_candidates = [link for link in portal_links if _is_tabular_download(link)]
    discovered_candidates = sorted(discovered_candidates, key=_candidate_score, reverse=True)
    file_candidates = _dedupe(discovered_candidates + static_candidates)

    name = "hud_fmr_county_sample"
    errors: list[str] = []
    for url in file_candidates:
        try:
            body = http_get_bytes(url, max_bytes=250_000)
            parsed = urlparse(url).path.lower()
            rows: list[list[str]] = []
            tmp_sample = tmp_dir / "fmr_county_head.bin"
            if parsed.endswith(".csv") or parsed.endswith(".txt"):
                tmp_sample = tmp_dir / "fmr_county_head.csv"
                reader = csv.reader(io.StringIO(body.decode("utf-8", errors="replace")))
                for i, row in enumerate(reader):
                    rows.append(row)
                    if i >= 5:
                        break
                if not rows:
                    raise RuntimeError("CSV sample was empty")
            write_bytes(tmp_sample, body)
            results.append(
                FetchResult(
                    name=name,
                    ok=True,
                    details={
                        "url": url,
                        "candidate_urls_tried": file_candidates,
                        "sample_rows": rows,
                        "bytes_sampled": len(body),
                        "tmp_sample": str(tmp_sample),
                    },
                )
            )
            break
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{url} -> {exc}")
    else:
        results.append(
            FetchResult(
                name=name,
                ok=False,
                details={"candidate_urls_tried": file_candidates, "candidate_link_count": len(portal_links)},
                error="All URL candidates failed: " + " | ".join(errors[:8]),
            )
        )

    return results
