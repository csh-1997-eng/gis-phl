from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES_DIR = REPO_ROOT / "ingestion/sources"
DEFAULT_SOURCE_SAMPLES_DIR = REPO_ROOT / "ingestion/tmp/samples"
DEFAULT_MINIMAL_REPORT_PATH = REPO_ROOT / "ingestion/tmp/samples/source_audit/minimal_ingestion_report.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "ingestion/tmp/samples/source_audit/artifacts"

REPORT_NAME_MAP = {
    "septa_gtfs": ("septa_gtfs",),
    "septa_gtfs_rt": ("septa_gtfs_rt_probe",),
    "phl_property_bulk": ("phl_property_bulk_download",),
    "opendataphilly_rental_suitability": ("opendataphilly_rental_suitability",),
    "opendataphilly_li_property_history": (
        "li_property_history_li_permits",
        "li_property_history_li_violations",
        "li_property_history_li_appeals",
    ),
    "opendataphilly_crime_incidents": ("opendataphilly_crime_incidents",),
    "zillow": ("zillow_zori_sample_metro", "zillow_zori_sample_city", "zillow_zori_sample_zip"),
    "acs_5y": ("acs_5y_variables", "acs_5y_philly_zcta_sample"),
    "lehd_lodes": ("lehd_lodes_directory",),
    "hud_fmr": ("hud_fmr_county_sample",),
    "bls_labor_cpi": ("bls_labor_area_lookup", "bls_cpi_area_lookup"),
    "fred": ("fred_philly_unemployment",),
    "ntad_amtrak": ("ntad_amtrak_stations",),
}


def load_minimal_report(path: Path) -> dict:
    return json.loads(path.read_text())


def classify_error(message: str) -> str:
    if not message:
        return ""
    if "CERTIFICATE_VERIFY_FAILED" in message:
        return "ssl_certificate"
    if "urlopen error" in message:
        return "network_or_http"
    if "All URL candidates failed" in message:
        return "all_candidates_failed"
    return "other"


def summarize_live_probe_status(report_items: list[dict]) -> str:
    if not report_items:
        return "not_checked"
    success_count = sum(bool(item.get("ok")) for item in report_items)
    if success_count == len(report_items):
        return "ok"
    error_messages = [item.get("error") or "" for item in report_items]
    ssl_failures = sum("CERTIFICATE_VERIFY_FAILED" in message for message in error_messages)
    if ssl_failures == len(report_items):
        return "blocked_by_ssl"
    return "failed"


def build_source_inventory(
    sources_dir: Path,
    source_samples_dir: Path,
    minimal_report_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    report = load_minimal_report(minimal_report_path)
    result_lookup = {item["name"]: item for item in report["results"]}

    source_rows: list[dict[str, object]] = []
    probe_rows: list[dict[str, object]] = []
    sample_rows: list[dict[str, object]] = []

    source_dirs = sorted(path for path in sources_dir.iterdir() if path.is_dir() and not path.name.startswith("__"))
    for source_dir in source_dirs:
        source_name = source_dir.name
        readme_path = source_dir / "README.md"
        probe_path = source_dir / "probe.py"
        sample_dir = source_samples_dir / source_name
        sample_files = sorted(path for path in sample_dir.glob("*") if path.is_file()) if sample_dir.exists() else []
        report_names = REPORT_NAME_MAP.get(source_name, ())
        report_items = [result_lookup[name] for name in report_names if name in result_lookup]

        for item in report_items:
            probe_rows.append(
                {
                    "source_name": source_name,
                    "probe_name": item["name"],
                    "ok": bool(item.get("ok")),
                    "error_class": classify_error(item.get("error", "")),
                    "error": item.get("error", ""),
                    "details_json": json.dumps(item.get("details", {}), sort_keys=True),
                }
            )

        for sample_file in sample_files:
            sample_rows.append(
                {
                    "source_name": source_name,
                    "sample_file": sample_file.name,
                    "suffix": sample_file.suffix,
                    "size_bytes": int(sample_file.stat().st_size),
                }
            )

        readme_text = readme_path.read_text() if readme_path.exists() else ""
        error_messages = [item.get("error") or "" for item in report_items]
        source_rows.append(
            {
                "source_name": source_name,
                "has_readme": readme_path.exists(),
                "has_probe_script": probe_path.exists(),
                "has_next_steps_section": "## Next Steps" in readme_text,
                "sample_dir_exists": sample_dir.exists(),
                "sample_file_count": len(sample_files),
                "sample_total_bytes": int(sum(path.stat().st_size for path in sample_files)),
                "sample_examples": ", ".join(path.name for path in sample_files[:3]),
                "report_names": ", ".join(report_names),
                "report_check_count": len(report_items),
                "report_success_count": sum(bool(item.get("ok")) for item in report_items),
                "report_error_count": sum(not bool(item.get("ok")) for item in report_items),
                "report_ssl_failure_count": sum("CERTIFICATE_VERIFY_FAILED" in message for message in error_messages),
                "live_probe_status": summarize_live_probe_status(report_items),
            }
        )

    sources = pd.DataFrame(source_rows).sort_values("source_name")
    probes = pd.DataFrame(probe_rows).sort_values(["source_name", "probe_name"])
    samples = pd.DataFrame(sample_rows).sort_values(["source_name", "sample_file"])
    return sources, probes, samples


def build_audit_summary(source_inventory: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "metric": "source_count",
            "value": int(len(source_inventory)),
        },
        {
            "metric": "sources_with_readme",
            "value": int(source_inventory["has_readme"].sum()),
        },
        {
            "metric": "sources_with_probe_script",
            "value": int(source_inventory["has_probe_script"].sum()),
        },
        {
            "metric": "sources_with_local_samples",
            "value": int(source_inventory["sample_file_count"].gt(0).sum()),
        },
        {
            "metric": "sources_live_probe_ok",
            "value": int(source_inventory["live_probe_status"].eq("ok").sum()),
        },
        {
            "metric": "sources_live_probe_blocked_by_ssl",
            "value": int(source_inventory["live_probe_status"].eq("blocked_by_ssl").sum()),
        },
        {
            "metric": "sources_live_probe_failed_otherwise",
            "value": int(source_inventory["live_probe_status"].eq("failed").sum()),
        },
    ]
    return pd.DataFrame(rows)


def main(
    sources_dir: Path = DEFAULT_SOURCES_DIR,
    source_samples_dir: Path = DEFAULT_SOURCE_SAMPLES_DIR,
    minimal_report_path: Path = DEFAULT_MINIMAL_REPORT_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    source_inventory, probe_results, sample_inventory = build_source_inventory(
        sources_dir=sources_dir,
        source_samples_dir=source_samples_dir,
        minimal_report_path=minimal_report_path,
    )
    audit_summary = build_audit_summary(source_inventory)

    source_inventory.to_csv(output_dir / "source_inventory.csv", index=False)
    probe_results.to_csv(output_dir / "source_probe_results.csv", index=False)
    sample_inventory.to_csv(output_dir / "source_sample_inventory.csv", index=False)
    audit_summary.to_csv(output_dir / "source_audit_summary.csv", index=False)

    print(f"Wrote source audit outputs to: {output_dir}")


if __name__ == "__main__":
    main()
