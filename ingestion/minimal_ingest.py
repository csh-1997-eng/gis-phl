#!/usr/bin/env python3
"""Run minimal source probes via per-source modules."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sources.acs_5y.probe import probe as probe_acs_5y
from sources.bls_labor_cpi.probe import probe as probe_bls_labor_cpi
from sources.common import FetchResult
from sources.fred.probe import probe as probe_fred
from sources.hud_fmr.probe import probe as probe_hud_fmr
from sources.lehd_lodes.probe import probe as probe_lehd_lodes
from sources.ntad_amtrak.probe import probe as probe_ntad_amtrak
from sources.opendataphilly_crime_incidents.probe import probe as probe_odp_crime
from sources.opendataphilly_li_property_history.probe import probe as probe_odp_li
from sources.opendataphilly_rental_suitability.probe import probe as probe_odp_rental
from sources.phl_property_bulk.probe import probe as probe_phl_property_bulk
from sources.septa_gtfs.probe import probe as probe_septa_gtfs
from sources.septa_gtfs_rt.probe import probe as probe_septa_gtfs_rt
from sources.zillow.probe import probe as probe_zillow

DEFAULT_OUTPUT_DIR = Path("ingestion/tmp/minimal_samples")
DEFAULT_TMP_DIR = Path("ingestion/tmp/source_samples")


def run_all(output_dir: Path, tmp_dir: Path) -> list[FetchResult]:
    source_runs = [
        ("septa_gtfs", probe_septa_gtfs),
        ("septa_gtfs_rt", probe_septa_gtfs_rt),
        ("phl_property_bulk", probe_phl_property_bulk),
        ("opendataphilly_rental_suitability", probe_odp_rental),
        ("opendataphilly_li_property_history", probe_odp_li),
        ("opendataphilly_crime_incidents", probe_odp_crime),
        ("zillow", probe_zillow),
        ("acs_5y", probe_acs_5y),
        ("lehd_lodes", probe_lehd_lodes),
        ("hud_fmr", probe_hud_fmr),
        ("bls_labor_cpi", probe_bls_labor_cpi),
        ("fred", probe_fred),
        ("ntad_amtrak", probe_ntad_amtrak),
    ]

    results: list[FetchResult] = []
    for source_name, source_probe in source_runs:
        source_tmp = tmp_dir / source_name
        source_tmp.mkdir(parents=True, exist_ok=True)
        source_results = source_probe(output_dir=output_dir, tmp_dir=source_tmp)
        results.extend(source_results)

    return results


def save_results(results: list[FetchResult], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "results": [r.to_dict() for r in results],
    }
    out_path = output_dir / "minimal_ingestion_report.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch minimal sample data from project sources")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where ingestion report is written",
    )
    parser.add_argument(
        "--tmp-dir",
        type=Path,
        default=DEFAULT_TMP_DIR,
        help="Directory where per-source probe samples are cached",
    )
    args = parser.parse_args()

    results = run_all(output_dir=args.output_dir, tmp_dir=args.tmp_dir)
    out_path = save_results(results, args.output_dir)

    ok_count = sum(1 for r in results if r.ok)
    print(f"Wrote {out_path}")
    print(f"Temporary source samples: {args.tmp_dir}")
    print(f"Successful sources: {ok_count}/{len(results)}")
    for result in results:
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {result.name}")
        if result.error:
            print(f"  error: {result.error}")

    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
