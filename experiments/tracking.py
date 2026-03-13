"""Shared MLflow tracking and run-spec helpers for experiments."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_MLFLOW_EXPERIMENT = "gis-phl"
DEFAULT_TRACKING_DIR = Path(__file__).resolve().parent / "mlruns"
REQUIRED_RUN_SPEC_FIELDS = (
    "question",
    "hypothesis",
    "reasoning.summary",
    "reasoning.expected_signal",
    "reasoning.risks",
    "evaluation.primary_metric",
    "evaluation.success_criteria",
    "evaluation.secondary_metrics",
    "evaluation.baselines",
    "evaluation.validation_design",
)


def resolve_run_name(
    *,
    default_run_name: str,
    variant: str | None = None,
    run_name: str | None = None,
) -> str:
    if run_name:
        return run_name.strip()
    if variant:
        return variant.strip()
    return default_run_name


def resolve_tracking_uri() -> str:
    """Return the configured MLflow tracking URI."""
    return os.environ.get("MLFLOW_TRACKING_URI", str(DEFAULT_TRACKING_DIR.resolve()))


def _lookup_path(payload: dict[str, Any], dotted_path: str) -> Any:
    current: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def validate_run_spec(payload: dict[str, Any]) -> None:
    missing = [path for path in REQUIRED_RUN_SPEC_FIELDS if _lookup_path(payload, path) in (None, "", [])]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"Run spec is missing required fields: {missing_str}")


def load_run_spec(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Run spec at {path} must deserialize to a mapping.")
    validate_run_spec(payload)
    return payload


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return "null"
    if isinstance(value, (bool, int, float)):
        return str(value)
    return json.dumps(value, sort_keys=True)


def flatten_for_logging(payload: dict[str, Any], prefix: str = "") -> dict[str, str]:
    items: dict[str, str] = {}
    for key, value in payload.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            items.update(flatten_for_logging(value, full_key))
            continue
        items[full_key] = _stringify(value)
    return items


def normalize_metrics_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy metrics into the shared envelope used by MLflow and evaluation."""
    if "holdout" in payload:
        normalized = {
            "scope": payload.get("scope", {}),
            "holdout": payload["holdout"],
        }
        if "rolling" in payload:
            normalized["rolling"] = payload["rolling"]
        return normalized

    holdout = {
        "split": payload.get("split", {}),
        "naive_lag1": payload.get("naive_lag1", {}),
        "linear_regression": payload.get("linear_regression", {}),
    }
    return {"scope": payload.get("scope", {}), "holdout": holdout}


def extract_metric_values(payload: dict[str, Any]) -> dict[str, float]:
    """Return only numeric model metrics with stable dotted keys."""
    normalized = normalize_metrics_payload(payload)
    metrics: dict[str, float] = {}

    holdout = normalized.get("holdout", {})
    for model_name, values in holdout.items():
        if model_name == "split" or not isinstance(values, dict):
            continue
        for metric_name, value in values.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                metrics[f"holdout.{model_name}.{metric_name}"] = float(value)

    rolling = normalized.get("rolling", {})
    aggregate = rolling.get("aggregate", {})
    for model_name, values in aggregate.items():
        if not isinstance(values, dict):
            continue
        for metric_name, value in values.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                metrics[f"rolling.aggregate.{model_name}.{metric_name}"] = float(value)

    for index, fold in enumerate(rolling.get("folds", []), start=1):
        if not isinstance(fold, dict):
            continue
        fold_id = _lookup_path(fold, "split.fold") or index
        for model_name, values in fold.items():
            if model_name == "split" or not isinstance(values, dict):
                continue
            for metric_name, value in values.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    metrics[f"rolling.folds.fold_{fold_id}.{model_name}.{metric_name}"] = float(value)

    return metrics


def build_param_values(
    *,
    metrics_payload: dict[str, Any],
    cli_args: dict[str, Any],
    additional_params: dict[str, Any] | None = None,
) -> dict[str, str]:
    normalized = normalize_metrics_payload(metrics_payload)
    params = {
        "scope": normalized.get("scope", {}),
        "holdout": {"split": normalized.get("holdout", {}).get("split", {})},
        "cli": cli_args,
    }
    rolling = normalized.get("rolling")
    if isinstance(rolling, dict):
        params["rolling"] = {
            key: value
            for key, value in rolling.items()
            if key not in {"folds", "aggregate"}
        }
    if additional_params:
        params["run"] = additional_params
    return flatten_for_logging(params)


def build_tag_values(
    *,
    experiment_key: str,
    run_spec: dict[str, Any],
    run_spec_path: Path,
    artifacts_dir: Path,
    run_tags: dict[str, Any] | None = None,
) -> dict[str, str]:
    tags = {
        "repo.experiment_key": experiment_key,
        "repo.run_spec_path": str(run_spec_path),
        "repo.artifacts_dir": str(artifacts_dir),
    }
    if run_tags:
        tags.update({key: _stringify(value) for key, value in run_tags.items()})
    tags.update(flatten_for_logging(run_spec, prefix="spec"))
    return tags


def _require_mlflow():
    try:
        import mlflow
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "MLflow is not installed. Add it to the active environment or pass --no-mlflow."
        ) from exc
    return mlflow


def log_mlflow_run(
    *,
    experiment_key: str,
    run_name: str,
    run_spec: dict[str, Any],
    run_spec_path: Path,
    metrics_payload: dict[str, Any],
    cli_args: dict[str, Any],
    artifacts_dir: Path,
    mlflow_experiment: str | None = None,
    additional_params: dict[str, Any] | None = None,
    run_tags: dict[str, Any] | None = None,
) -> str:
    """Log one completed training invocation to MLflow."""
    mlflow = _require_mlflow()
    tracking_uri = resolve_tracking_uri()
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(mlflow_experiment or DEFAULT_MLFLOW_EXPERIMENT)

    normalized_metrics = normalize_metrics_payload(metrics_payload)
    params = build_param_values(
        metrics_payload=normalized_metrics,
        cli_args=cli_args,
        additional_params=additional_params,
    )
    tags = build_tag_values(
        experiment_key=experiment_key,
        run_spec=run_spec,
        run_spec_path=run_spec_path,
        artifacts_dir=artifacts_dir,
        run_tags=run_tags,
    )
    metric_values = extract_metric_values(normalized_metrics)

    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags(tags)
        if params:
            mlflow.log_params(params)
        for key, value in metric_values.items():
            mlflow.log_metric(key, value)
        mlflow.log_artifact(str(run_spec_path), artifact_path="run_spec")
        mlflow.log_artifacts(str(artifacts_dir), artifact_path="artifacts")
        mlflow.log_text(
            json.dumps(normalized_metrics, indent=2),
            artifact_file="tracking/normalized_metrics.json",
        )
        return run.info.run_id
