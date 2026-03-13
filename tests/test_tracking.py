from __future__ import annotations

import json
from pathlib import Path
import textwrap

import pytest

from experiments.tracking import build_param_values, extract_metric_values, load_run_spec, log_mlflow_run
from experiments.tracking import resolve_run_name


def _sample_metrics_payload() -> dict:
    return {
        "scope": {"philly_geo_id": "geo:zori:city:13271"},
        "holdout": {
            "split": {
                "train_end_date": "2024-12-31",
                "train_rows": 100,
                "validation_rows": 12,
            },
            "naive_lag1": {
                "mae": 0.2,
                "rmse": 0.3,
                "directional_accuracy": 0.5,
                "spearman_corr": 0.1,
            },
            "linear_regression": {
                "mae": 0.1,
                "rmse": 0.15,
                "directional_accuracy": 0.7,
                "spearman_corr": 0.4,
            },
        },
        "rolling": {
            "n_folds_requested": 2,
            "n_folds_executed": 1,
            "folds": [
                {
                    "split": {"fold": 1, "train_end_date": "2024-10-31"},
                    "naive_lag1": {"mae": 0.25},
                    "linear_regression": {"mae": 0.12},
                }
            ],
            "aggregate": {
                "naive_lag1": {"mae_mean": 0.25},
                "linear_regression": {"mae_mean": 0.12},
            },
        },
    }


def _sample_run_spec_text() -> str:
    return textwrap.dedent(
        """
        question: Does this test run log correctly?
        hypothesis: The tracked run should store params metrics and artifacts.
        reasoning:
          summary: Unit test coverage for MLflow logging.
          expected_signal: A completed run with stable metric keys should be recorded.
          risks:
            - MLflow may be unavailable in the local environment.
        evaluation:
          primary_metric: holdout.linear_regression.mae
          success_criteria: A run is created with the expected metric and tags.
          secondary_metrics:
            - holdout.linear_regression.rmse
          baselines:
            - naive_lag1
          validation_design: Synthetic unit test payload.
        """
    ).strip()


def test_load_run_spec_requires_expected_fields(tmp_path: Path) -> None:
    run_spec_path = tmp_path / "run_spec.yaml"
    run_spec_path.write_text("question: missing-most-fields\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Run spec is missing required fields"):
        load_run_spec(run_spec_path)


def test_extract_metric_values_and_param_values() -> None:
    payload = _sample_metrics_payload()

    metrics = extract_metric_values(payload)
    params = build_param_values(
        metrics_payload=payload,
        cli_args={"train_end_date": "2024-12-31", "rolling_folds": 2},
        additional_params={"feature_cols": ["lag1", "lag3"]},
    )

    assert metrics["holdout.linear_regression.mae"] == pytest.approx(0.1)
    assert metrics["rolling.aggregate.linear_regression.mae_mean"] == pytest.approx(0.12)
    assert metrics["rolling.folds.fold_1.naive_lag1.mae"] == pytest.approx(0.25)
    assert params["scope.philly_geo_id"] == "geo:zori:city:13271"
    assert params["holdout.split.train_end_date"] == "2024-12-31"
    assert params["run.feature_cols"] == "[\"lag1\", \"lag3\"]"


def test_resolve_run_name_prefers_explicit_name_then_variant() -> None:
    assert resolve_run_name(default_run_name="legacy_name", variant="v2_clean_city_keys") == "v2_clean_city_keys"
    assert resolve_run_name(
        default_run_name="legacy_name",
        variant="v2_clean_city_keys",
        run_name="manual_override",
    ) == "manual_override"
    assert resolve_run_name(default_run_name="legacy_name") == "legacy_name"


def test_log_mlflow_run_records_tags_metrics_and_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mlflow = pytest.importorskip("mlflow")
    from mlflow.client import MlflowClient

    tracking_dir = tmp_path / "mlruns"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", str(tracking_dir))

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    (artifacts_dir / "metrics.json").write_text(
        json.dumps(_sample_metrics_payload(), indent=2),
        encoding="utf-8",
    )
    (artifacts_dir / "dataset_summary.csv").write_text(
        "row_count,geo_count\n100,1\n",
        encoding="utf-8",
    )

    run_spec_path = tmp_path / "run_spec.yaml"
    run_spec_path.write_text(_sample_run_spec_text(), encoding="utf-8")
    run_spec = load_run_spec(run_spec_path)

    run_id = log_mlflow_run(
        experiment_key="exp_test",
        run_name="exp_test_run",
        run_spec=run_spec,
        run_spec_path=run_spec_path,
        metrics_payload=_sample_metrics_payload(),
        cli_args={"train_end_date": "2024-12-31"},
        artifacts_dir=artifacts_dir,
        mlflow_experiment="unit-tests",
        additional_params={"feature_cols": ["lag1"]},
        run_tags={
            "variant": "v2_clean_city_keys",
            "stage": "baseline",
            "target": "r1m_next",
            "geo_scope": "philly_city",
            "feature_set": "lags_plus_econ",
            "ontology_version": "2026-03-11-city-key-fix",
        },
    )

    mlflow.set_tracking_uri(str(tracking_dir))
    client = MlflowClient()
    run = client.get_run(run_id)

    assert run.data.metrics["holdout.linear_regression.mae"] == pytest.approx(0.1)
    assert run.data.tags["repo.experiment_key"] == "exp_test"
    assert run.data.tags["spec.evaluation.primary_metric"] == "holdout.linear_regression.mae"
    assert run.data.tags["variant"] == "v2_clean_city_keys"
    assert run.data.tags["stage"] == "baseline"
    assert run.data.tags["target"] == "r1m_next"
    assert run.data.tags["geo_scope"] == "philly_city"
    assert run.data.tags["feature_set"] == "lags_plus_econ"
    assert run.data.tags["ontology_version"] == "2026-03-11-city-key-fix"

    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    local_artifact = Path(client.download_artifacts(run_id, "run_spec/run_spec.yaml", str(download_dir)))
    assert local_artifact.read_text(encoding="utf-8").startswith("question:")
