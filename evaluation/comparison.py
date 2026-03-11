"""Shared loaders for cross-experiment comparison from files or MLflow."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pandas as pd

from experiments.tracking import normalize_metrics_payload, resolve_tracking_uri


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPERIMENTS = {
    "exp_001": REPO_ROOT / "experiments/exp_001_baseline_rent_growth/artifacts",
    "exp_002": REPO_ROOT / "experiments/exp_002_philly_consistent_baseline/artifacts",
    "exp_003": REPO_ROOT / "experiments/exp_003_philly_region_zip_panel/artifacts",
}


def _load_metrics_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return normalize_metrics_payload(payload)


def _frames_from_payload(exp_name: str, payload: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    holdout = payload.get("holdout", {})
    scope = payload.get("scope", {})
    rolling = payload.get("rolling", {})

    metric_rows: list[dict[str, Any]] = []
    for model_name in ("naive_lag1", "linear_regression"):
        values = holdout.get(model_name)
        if isinstance(values, dict):
            row = {"experiment": exp_name, "model": model_name}
            row.update(values)
            metric_rows.append(row)

    split_row = {"experiment": exp_name}
    split_row.update(holdout.get("split", {}))
    split_row.update(scope)

    rolling_rows: list[dict[str, Any]] = []
    for model_name, values in rolling.get("aggregate", {}).items():
        if isinstance(values, dict):
            row = {"experiment": exp_name, "model": model_name}
            row.update(values)
            rolling_rows.append(row)

    return (
        pd.DataFrame(metric_rows),
        pd.DataFrame([split_row]),
        pd.DataFrame(rolling_rows),
    )


def load_experiment_from_files(exp_name: str, artifacts_dir: Path) -> dict[str, pd.DataFrame]:
    payload = _load_metrics_payload(artifacts_dir / "metrics.json")
    holdout_df, split_df, rolling_df = _frames_from_payload(exp_name, payload)
    dataset_df = pd.DataFrame()
    dataset_path = artifacts_dir / "dataset_summary.csv"
    if dataset_path.exists():
        dataset_df = pd.read_csv(dataset_path)
        dataset_df.insert(0, "experiment", exp_name)
    return {
        "holdout_metrics": holdout_df,
        "split_summary": split_df,
        "rolling_summary": rolling_df,
        "dataset_summary": dataset_df,
    }


def _require_mlflow():
    try:
        import mlflow
        from mlflow.client import MlflowClient
    except ModuleNotFoundError as exc:
        raise RuntimeError("MLflow is not installed in the active environment.") from exc
    return mlflow, MlflowClient


def _download_text_artifact(client: Any, run_id: str, artifact_path: str, temp_dir: Path) -> str | None:
    try:
        local_path = Path(client.download_artifacts(run_id, artifact_path, str(temp_dir)))
    except Exception:
        return None
    return local_path.read_text(encoding="utf-8")


def _download_csv_artifact(client: Any, run_id: str, artifact_path: str, temp_dir: Path) -> pd.DataFrame:
    local_path = Path(client.download_artifacts(run_id, artifact_path, str(temp_dir)))
    return pd.read_csv(local_path)


def load_experiment_from_mlflow(exp_name: str) -> dict[str, pd.DataFrame] | None:
    mlflow, MlflowClient = _require_mlflow()
    mlflow.set_tracking_uri(resolve_tracking_uri())
    client = MlflowClient()
    experiment_ids = [exp.experiment_id for exp in client.search_experiments()]
    if not experiment_ids:
        return None

    runs = client.search_runs(
        experiment_ids=experiment_ids,
        filter_string=f"tags.`repo.experiment_key` = '{exp_name}' and attributes.status = 'FINISHED'",
        order_by=["attributes.start_time DESC"],
        max_results=1,
    )
    if not runs:
        return None

    run = runs[0]
    with TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        metrics_text = _download_text_artifact(client, run.info.run_id, "artifacts/metrics.json", temp_dir)
        if metrics_text is None:
            metrics_text = _download_text_artifact(client, run.info.run_id, "tracking/normalized_metrics.json", temp_dir)
        if metrics_text is None:
            return None

        payload = normalize_metrics_payload(json.loads(metrics_text))
        holdout_df, split_df, rolling_df = _frames_from_payload(exp_name, payload)
        dataset_df = pd.DataFrame()
        try:
            dataset_df = _download_csv_artifact(client, run.info.run_id, "artifacts/dataset_summary.csv", temp_dir)
            dataset_df.insert(0, "experiment", exp_name)
        except Exception:
            dataset_df = pd.DataFrame()

    return {
        "holdout_metrics": holdout_df,
        "split_summary": split_df,
        "rolling_summary": rolling_df,
        "dataset_summary": dataset_df,
    }


def load_comparison_frames(
    experiments: dict[str, Path] | None = None,
    *,
    source_mode: str = "auto",
) -> dict[str, pd.DataFrame]:
    if source_mode not in {"auto", "files", "mlflow"}:
        raise ValueError("source_mode must be one of: auto, files, mlflow")

    experiments = experiments or DEFAULT_EXPERIMENTS

    holdout_frames: list[pd.DataFrame] = []
    split_frames: list[pd.DataFrame] = []
    rolling_frames: list[pd.DataFrame] = []
    dataset_frames: list[pd.DataFrame] = []

    for exp_name, artifacts_dir in experiments.items():
        source_frames: dict[str, pd.DataFrame] | None = None

        if source_mode in {"auto", "mlflow"}:
            source_frames = load_experiment_from_mlflow(exp_name)
            if source_mode == "mlflow" and source_frames is None:
                raise FileNotFoundError(f"No MLflow run found for {exp_name}.")

        if source_frames is None and source_mode in {"auto", "files"}:
            source_frames = load_experiment_from_files(exp_name, artifacts_dir)

        if source_frames is None:
            continue

        holdout_frames.append(source_frames["holdout_metrics"])
        split_frames.append(source_frames["split_summary"])
        if not source_frames["rolling_summary"].empty:
            rolling_frames.append(source_frames["rolling_summary"])
        if not source_frames["dataset_summary"].empty:
            dataset_frames.append(source_frames["dataset_summary"])

    return {
        "holdout_metrics": pd.concat(holdout_frames, ignore_index=True) if holdout_frames else pd.DataFrame(),
        "split_summary": pd.concat(split_frames, ignore_index=True) if split_frames else pd.DataFrame(),
        "rolling_summary": pd.concat(rolling_frames, ignore_index=True) if rolling_frames else pd.DataFrame(),
        "dataset_summary": pd.concat(dataset_frames, ignore_index=True) if dataset_frames else pd.DataFrame(),
    }
