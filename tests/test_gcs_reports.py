from unittest.mock import MagicMock

import pandas as pd
import pytest
from fastapi import HTTPException
from google.api_core.exceptions import NotFound

from src.api import main as api


@pytest.fixture
def fake_gcs(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(api, "REPORTS_BUCKET", "test-reports-bucket")
    monkeypatch.setattr(api.storage, "Client", lambda: client)
    return client, client.bucket.return_value.blob.return_value


def test_gcs_report_upload(fake_gcs):
    client, blob = fake_gcs
    frame = pd.DataFrame({"Amount": [100.0], "predicted_label": [0]})
    result_id = "a" * 32

    api._save_batch_report(result_id, frame)

    client.bucket.assert_called_with("test-reports-bucket")
    client.bucket.return_value.blob.assert_called_with(
        f"batch/batch_{result_id}.csv"
    )
    blob.upload_from_string.assert_called_once()
    assert blob.upload_from_string.call_args.kwargs == {
        "content_type": "text/csv",
        "if_generation_match": 0,
    }


def test_gcs_report_download(fake_gcs):
    _, blob = fake_gcs
    blob.download_as_bytes.return_value = b"Amount,predicted_label\n100,0\n"

    result = api._get_batch_report("b" * 32)

    assert result == b"Amount,predicted_label\n100,0\n"


def test_gcs_missing_report(fake_gcs):
    _, blob = fake_gcs
    blob.download_as_bytes.side_effect = NotFound("Not found")

    assert api._get_batch_report("c" * 32) is None


def test_gcs_upload_failure_returns_503(fake_gcs):
    _, blob = fake_gcs
    blob.upload_from_string.side_effect = RuntimeError("Storage unavailable")

    with pytest.raises(HTTPException) as error:
        api._save_batch_report("d" * 32, pd.DataFrame({"Amount": [1]}))

    assert error.value.status_code == 503
    assert error.value.detail["code"] == "report_storage_unavailable"


def test_gcs_download_failure_returns_503(fake_gcs):
    _, blob = fake_gcs
    blob.download_as_bytes.side_effect = RuntimeError("Storage unavailable")

    with pytest.raises(HTTPException) as error:
        api._get_batch_report("e" * 32)

    assert error.value.status_code == 503
    assert error.value.detail["code"] == "report_storage_unavailable"


def test_batch_api_upload_and_download_with_mock_gcs(fake_gcs, monkeypatch):
    import io
    from fastapi.testclient import TestClient
    from src.data.make_dataset import FEATURE_COLUMNS

    client_mock, blob = fake_gcs

    class DeterministicModel:
        def predict_proba(self, frame):
            import numpy as np
            scores = np.full(len(frame), 0.1)
            return np.column_stack([1 - scores, scores])

    monkeypatch.setattr(api, "MODEL", DeterministicModel())
    monkeypatch.setattr(api, "MODEL_VERSION", "test-model:gcs")
    monkeypatch.setattr(
        api,
        "MODEL_METADATA",
        {
            "score_semantics": "Test score only.",
            "threshold_selection": {"threshold": 0.5},
        },
    )

    transaction = {column: 0.0 for column in FEATURE_COLUMNS}
    transaction["Time"] = 100.0
    transaction["Amount"] = 25.0

    csv_data = pd.DataFrame(
        [transaction], columns=FEATURE_COLUMNS
    ).to_csv(index=False).encode("utf-8")

    client = TestClient(api.app)

    response = client.post(
        "/predict/batch",
        files={"file": ("transactions.csv", csv_data, "text/csv")},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["rows_received"] == 1
    assert result["rows_processed"] == 1
    assert result["rows_rejected"] == 0

    blob.upload_from_string.assert_called_once()
    stored_csv = blob.upload_from_string.call_args.args[0]
    blob.download_as_bytes.return_value = stored_csv.encode("utf-8")

    download = client.get(result["download_url"])

    assert download.status_code == 200
    assert "text/csv" in download.headers["content-type"]

    exported = pd.read_csv(io.BytesIO(download.content))
    assert len(exported) == 1
    assert exported.loc[0, "prediction_status"] == "scored"
    assert exported.loc[0, "predicted_label"] == 0
    assert exported.loc[0, "model_score"] == pytest.approx(0.1)

    client_mock.bucket.return_value.blob.assert_called_with(
        f"batch/batch_{result['result_id']}.csv"
    )
