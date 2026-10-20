from __future__ import annotations

import io
import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.api import main as api
from src.data.make_dataset import FEATURE_COLUMNS

client = TestClient(api.app)


class DeterministicModel:
    feature_names_in_ = np.asarray(FEATURE_COLUMNS)

    def predict_proba(self, frame: pd.DataFrame) -> np.ndarray:
        positive = np.where(frame["Amount"].to_numpy() >= 10, 0.9, 0.1)
        return np.column_stack([1 - positive, positive])


def configure_model(monkeypatch) -> None:
    monkeypatch.setattr(api, "MODEL", DeterministicModel())
    monkeypatch.setattr(api, "MODEL_VERSION", "test-model:abc123")
    monkeypatch.setattr(api, "MODEL_METADATA", {
        "score_semantics": "Test score only.",
        "threshold_selection": {"threshold": 0.5},
        "evaluation_status": "independent_test_evaluation",
    })


def transaction(amount: float = 12.0) -> dict[str, float]:
    return {**{column: 0.0 for column in FEATURE_COLUMNS}, "Amount": amount}


def csv_bytes(rows: list[dict]) -> bytes:
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS).to_csv(index=False).encode()


def test_health_does_not_depend_on_model() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_saved_artifact_prediction_smoke() -> None:
    if api.MODEL is None:
        pytest.skip("A trained local model artifact is required for this integration check.")
    response = client.post("/predict", json=transaction(45.5))
    assert response.status_code == 200
    assert response.json()["model_version"] == api.MODEL_VERSION
    assert 0 <= response.json()["model_score"] <= 1


def test_readiness_reports_missing_model(monkeypatch) -> None:
    monkeypatch.setattr(api, "MODEL", None)
    monkeypatch.setattr(api, "MODEL_LOAD_ERROR", "artifact missing")
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "artifact missing"


def test_individual_prediction_uses_score_and_configured_threshold(monkeypatch) -> None:
    configure_model(monkeypatch)
    response = client.post("/predict", json=transaction())
    assert response.status_code == 200
    result = response.json()
    assert result["predicted_label"] == 1
    assert result["model_score"] == 0.9
    assert result["threshold"] == 0.5
    assert result["model_version"] == "test-model:abc123"
    assert "probability" not in result
    assert "explanations" not in result


def test_non_finite_values_are_rejected(monkeypatch) -> None:
    configure_model(monkeypatch)
    payload = transaction()
    payload["V1"] = float("nan")
    response = client.post(
        "/predict",
        content=json.dumps(payload, allow_nan=True),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_negative_amount_is_rejected_from_observed_data_domain(monkeypatch) -> None:
    configure_model(monkeypatch)
    response = client.post("/predict", json=transaction(-1))
    assert response.status_code == 422


def test_batch_returns_rows_and_downloadable_enriched_csv(monkeypatch) -> None:
    configure_model(monkeypatch)
    valid = transaction(12)
    invalid = transaction(5)
    invalid["V4"] = float("nan")
    response = client.post(
        "/predict/batch",
        files={"file": ("transactions.csv", csv_bytes([valid, invalid]), "text/csv")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["rows_received"] == 2
    assert result["rows_processed"] == 1
    assert result["rows_rejected"] == 1
    assert result["predicted_positive"] == 1
    assert [row["status"] for row in result["results"]] == ["scored", "rejected"]

    download = client.get(result["download_url"])
    assert download.status_code == 200
    enriched = pd.read_csv(io.BytesIO(download.content))
    assert enriched.loc[0, "prediction_status"] == "scored"
    assert enriched.loc[0, "predicted_label"] == 1
    assert enriched.loc[1, "prediction_status"] == "rejected"
    assert pd.notna(enriched.loc[1, "row_error"])


def test_batch_rejects_schema_mismatch(monkeypatch) -> None:
    configure_model(monkeypatch)
    response = client.post(
        "/predict/batch",
        files={"file": ("transactions.csv", b"Amount,Class\n1,0\n", "text/csv")},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "schema_mismatch"


def test_batch_rejects_malformed_and_empty_files(monkeypatch) -> None:
    configure_model(monkeypatch)
    malformed = client.post(
        "/predict/batch", files={"file": ("bad.csv", b'"unterminated', "text/csv")}
    )
    empty = client.post(
        "/predict/batch", files={"file": ("empty.csv", b"", "text/csv")}
    )
    assert malformed.status_code == 422
    assert malformed.json()["detail"]["code"] == "malformed_csv"
    assert empty.status_code == 422
    assert empty.json()["detail"]["code"] == "empty_file"
