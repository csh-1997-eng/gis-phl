from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
import textwrap

import pandas as pd
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TRAIN_SCRIPT = REPO_ROOT / "experiments/exp_001_baseline_rent_growth/src/train.py"


def _build_synthetic_inputs(base_dir: Path) -> tuple[Path, Path]:
    periods = pd.date_range("2022-01-31", periods=30, freq="ME")
    apt_rows = []
    for geo_index, geo_id in enumerate(("geo:test:a", "geo:test:b"), start=1):
        for period_index, period in enumerate(periods):
            apt_rows.append(
                {
                    "entity_id": f"apt:{geo_index}:{period_index}",
                    "geography_entity_id": geo_id,
                    "period": period.strftime("%Y-%m-%d"),
                    "rent_growth_1m": 0.01 + (0.001 * geo_index) + (0.0002 * period_index),
                    "rent_index": 100 + (geo_index * 5) + period_index,
                }
            )
    econ_rows = [
        {
            "period": period.strftime("%Y-%m-%d"),
            "unemployment_rate": 4.0 + (0.01 * idx),
        }
        for idx, period in enumerate(periods)
    ]

    apt_path = base_dir / "apartment_market.csv"
    econ_path = base_dir / "economic.csv"
    pd.DataFrame(apt_rows).to_csv(apt_path, index=False)
    pd.DataFrame(econ_rows).to_csv(econ_path, index=False)
    return apt_path, econ_path


def test_exp001_train_logs_mlflow_and_writes_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mlflow = pytest.importorskip("mlflow")
    from mlflow.client import MlflowClient
    from experiments.tracking import load_run_spec

    tracking_dir = tmp_path / "mlruns"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", str(tracking_dir))

    apt_path, econ_path = _build_synthetic_inputs(tmp_path)
    artifacts_dir = tmp_path / "artifacts"
    run_spec_path = tmp_path / "run_spec.yaml"
    run_spec_path.write_text(
        textwrap.dedent(
            """
            question: Does exp_001 run end to end on synthetic data?
            hypothesis: The training script should finish, emit artifacts, and create one MLflow run.
            reasoning:
              summary: Smoke test for the tracked training entrypoint.
              expected_signal: One FINISHED run with holdout metrics and the supplied run spec.
              risks:
                - Synthetic data may create degenerate regression behavior.
            evaluation:
              primary_metric: holdout.linear_regression.mae
              success_criteria: Training completes and logs at least one holdout metric.
              secondary_metrics:
                - holdout.linear_regression.rmse
              baselines:
                - naive_lag1
              validation_design: Synthetic single-split smoke test.
            """
        ).strip(),
        encoding="utf-8",
    )
    load_run_spec(run_spec_path)

    subprocess.run(
        [
            sys.executable,
            str(TRAIN_SCRIPT),
            "--apt-path",
            str(apt_path),
            "--econ-path",
            str(econ_path),
            "--artifacts-dir",
            str(artifacts_dir),
            "--train-end-date",
            "2024-02-29",
            "--run-spec-path",
            str(run_spec_path),
            "--mlflow-experiment",
            "smoke-tests",
        ],
        cwd=REPO_ROOT,
        check=True,
        env={**os.environ, "MLFLOW_TRACKING_URI": str(tracking_dir)},
    )

    assert (artifacts_dir / "metrics.json").exists()
    assert (artifacts_dir / "dataset_summary.csv").exists()
    assert (artifacts_dir / "predictions.csv").exists()

    mlflow.set_tracking_uri(str(tracking_dir))
    client = MlflowClient()
    experiment = client.get_experiment_by_name("smoke-tests")
    assert experiment is not None
    runs = client.search_runs(
        [experiment.experiment_id],
        filter_string="tags.`repo.experiment_key` = 'exp_001'",
        order_by=["attributes.start_time DESC"],
        max_results=1,
    )
    assert len(runs) == 1
    assert runs[0].data.metrics["holdout.linear_regression.mae"] >= 0.0
    assert runs[0].data.tags["spec.question"] == "Does exp_001 run end to end on synthetic data?"
