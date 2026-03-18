#!/usr/bin/env python3
"""Download full Zillow city/MSA ZORI feeds and filter them by state."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36 "
    "gis-phl-zillow-extract/0.1"
)
TIMEOUT_SECONDS = 90

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TARGETED_OUTPUT_DIR = REPO_ROOT / "ingestion/tmp/targeted_extracts/zillow"
DEFAULT_FULL_OUTPUT_DIR = REPO_ROOT / "ingestion/tmp/full_extracts/zillow"
DEFAULT_DATASET_KEYS = ("city", "metro")

ZORI_FEEDS = {
    "city": "https://files.zillowstatic.com/research/public_csvs/zori/City_zori_uc_sfrcondomfr_sm_month.csv",
    "metro": "https://files.zillowstatic.com/research/public_csvs/zori/Metro_zori_uc_sfrcondomfr_sm_month.csv",
    "zip": "https://files.zillowstatic.com/research/public_csvs/zori/Zip_zori_uc_sfrcondomfr_sm_month.csv",
}


def download_to_path(url: str, output_path: Path) -> None:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with urlopen(req, timeout=TIMEOUT_SECONDS) as resp:  # noqa: S310
        output_path.write_bytes(resp.read())


def read_zillow_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False)


def filter_by_states(df: pd.DataFrame, states: set[str]) -> pd.DataFrame:
    state_series = df.get("StateName")
    if state_series is None:
        return df.iloc[0:0].copy()
    normalized = state_series.fillna("").astype(str).str.upper().str.strip()
    return df.loc[normalized.isin(states)].copy()


def build_summary(dataset_key: str, full_df: pd.DataFrame, filtered_df: pd.DataFrame, states: list[str]) -> dict[str, object]:
    summary: dict[str, object] = {
        "dataset_key": dataset_key,
        "requested_states": states,
        "full_row_count": int(len(full_df)),
        "filtered_row_count": int(len(filtered_df)),
        "full_unique_regions": int(full_df["RegionID"].nunique()) if "RegionID" in full_df.columns else None,
        "filtered_unique_regions": int(filtered_df["RegionID"].nunique()) if "RegionID" in filtered_df.columns else None,
    }
    if "StateName" in filtered_df.columns:
        summary["filtered_states"] = (
            filtered_df["StateName"].fillna("").astype(str).str.upper().value_counts().sort_index().to_dict()
        )
    else:
        summary["filtered_states"] = {}
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download full Zillow city/MSA feeds and filter by state")
    parser.add_argument(
        "--states",
        nargs="+",
        required=True,
        help="State abbreviations to retain, for example PA NJ DE MD NY",
    )
    parser.add_argument(
        "--dataset-keys",
        nargs="+",
        default=list(DEFAULT_DATASET_KEYS),
        choices=sorted(ZORI_FEEDS.keys()),
        help="Zillow feed types to download",
    )
    parser.add_argument(
        "--targeted-output-dir",
        type=Path,
        default=DEFAULT_TARGETED_OUTPUT_DIR,
        help="Directory to write state-filtered Zillow CSVs",
    )
    parser.add_argument(
        "--full-output-dir",
        type=Path,
        default=DEFAULT_FULL_OUTPUT_DIR,
        help="Directory to write full raw Zillow CSVs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    states = [state.upper() for state in args.states]
    state_set = set(states)

    summaries: list[dict[str, object]] = []
    for dataset_key in args.dataset_keys:
        url = ZORI_FEEDS[dataset_key]
        raw_path = args.full_output_dir / f"{dataset_key}_zori_full.csv"
        filtered_path = args.targeted_output_dir / f"{dataset_key}_zori_state_filtered.csv"

        download_to_path(url, raw_path)
        full_df = read_zillow_csv(raw_path)
        filtered_df = filter_by_states(full_df, state_set)
        filtered_path.parent.mkdir(parents=True, exist_ok=True)
        filtered_df.to_csv(filtered_path, index=False)

        summaries.append(build_summary(dataset_key, full_df, filtered_df, states))

    summary_path = args.targeted_output_dir / "zillow_state_filtered_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps({"datasets": summaries}, indent=2), encoding="utf-8")

    print(f"Wrote filtered Zillow extracts to: {args.targeted_output_dir}")
    for item in summaries:
        print(
            f"- {item['dataset_key']}: {item['filtered_row_count']} rows "
            f"across {item['filtered_unique_regions']} regions"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
