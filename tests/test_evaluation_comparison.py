from __future__ import annotations

import json
from pathlib import Path
import textwrap

import pytest

from evaluation.comparison import load_comparison_frames
from experiments.tracking import load_run_spec, log_mlflow_run


def test_load_comparison_frames_from_files(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "exp_file" / "artifacts"
    artifacts_dir.mkdir(parents=True)
    legacy_metrics = {
        "split": {"train_end_date": "2024-12-31", "train_rows": 10, "validation_rows": 2},
        "naive_lag1": {"mae": 0.3, "rmse": 0.4, "directional_accuracy": 0.5, "spearman_corr": 0.1},
        "linear_regression": {"mae": 0.2, "rmse": 0.25, "directional_accuracy": 0.6, "spearman_corr": 0.2},
    }
    (artifacts_dir / "metrics.json").write_text(json.dumps(legacy_metrics, indent=2), encoding="utf-8")
    (artifacts_dir / "dataset_summary.csv").write_text("row_count,geo_count\n12,1\n", encoding="utf-8")

    frames = load_comparison_frames({"exp_file": artifacts_dir}, source_mode="files")

    assert set(frames["holdout_metrics"]["model"]) == {"naive_lag1", "linear_regression"}
    assert frames["split_summary"].iloc[0]["train_end_date"] == "2024-12-31"
    assert frames["dataset_summary"].iloc[0]["row_count"] == 12


def test_load_comparison_frames_from_mlflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("mlflow")

    tracking_dir = tmp_path / "mlruns"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", str(tracking_dir))

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    metrics = {
        "scope": {"states": ["PA", "NJ", "DE"]},
        "holdout": {
            "split": {"train_end_date": "2024-12-31", "train_rows": 50, "validation_rows": 10},
            "naive_lag1": {"mae": 0.5, "rmse": 0.7, "directional_accuracy": 0.4, "spearman_corr": 0.1},
            "linear_regression": {"mae": 0.25, "rmse": 0.4, "directional_accuracy": 0.6, "spearman_corr": 0.3},
        },
    }
    (artifacts_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (artifacts_dir / "dataset_summary.csv").write_text("row_count,geo_count\n60,5\n", encoding="utf-8")

    run_spec_path = tmp_path / "run_spec.yaml"
    run_spec_path.write_text(
        textwrap.dedent(
            """
            question: Can the comparison loader read MLflow-backed runs?
            hypothesis: The latest tagged run should be selected.
            reasoning:
              summary: Evaluation helper integration test.
              expected_signal: The MLflow loader returns the logged holdout rows.
              risks:
                - MLflow artifact download behavior can vary across versions.
            evaluation:
              primary_metric: holdout.linear_regression.mae
              success_criteria: The comparison frame includes one linear_regression row.
              secondary_metrics:
                - holdout.linear_regression.rmse
              baselines:
                - naive_lag1
              validation_design: Synthetic MLflow loader test.
            """
        ).strip(),
        encoding="utf-8",
    )
    run_spec = load_run_spec(run_spec_path)

    log_mlflow_run(
        experiment_key="exp_mlflow",
        run_name="exp_mlflow_run",
        run_spec=run_spec,
        run_spec_path=run_spec_path,
        metrics_payload=metrics,
        cli_args={"train_end_date": "2024-12-31"},
        artifacts_dir=artifacts_dir,
        mlflow_experiment="comparison-tests",
    )

    frames = load_comparison_frames({"exp_mlflow": tmp_path / "unused"}, source_mode="mlflow")

    assert set(frames["holdout_metrics"]["model"]) == {"naive_lag1", "linear_regression"}
    assert frames["split_summary"].iloc[0]["train_rows"] == 50
    assert frames["dataset_summary"].iloc[0]["geo_count"] == 5
