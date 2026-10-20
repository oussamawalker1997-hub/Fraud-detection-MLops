"""FastAPI inference service for the explicitly trained fraud model artifact."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import time
import uuid
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.data.make_dataset import FEATURE_COLUMNS

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = Path(os.getenv("MODEL_PATH", str(ROOT / "models" / "fraud_model.joblib")))
METRICS_PATH = Path(os.getenv("METRICS_PATH", str(ROOT / "reports" / "evaluation_metrics.json")))
REPORTS_PATH = Path(os.getenv("REPORTS_PATH", str(ROOT / "reports" / "batch")))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
MAX_BATCH_ROWS = int(os.getenv("MAX_BATCH_ROWS", "50000"))
MODEL = None
MODEL_METADATA: dict = {}
MODEL_VERSION: str | None = None
MODEL_LOAD_ERROR: str | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_artifact() -> None:
    global MODEL, MODEL_METADATA, MODEL_VERSION, MODEL_LOAD_ERROR
    if not MODEL_PATH.is_file() or not METRICS_PATH.is_file():
        MODEL_LOAD_ERROR = "Trained model artifact or evaluation metadata is missing."
        return
    try:
        metadata = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        artifact_hash = _sha256(MODEL_PATH)
        if not hmac.compare_digest(artifact_hash, str(metadata.get("artifact_sha256", ""))):
            raise ValueError("Model artifact hash does not match evaluation metadata.")
        if metadata.get("evaluation_status") != "independent_test_evaluation":
            raise ValueError("Artifact metadata does not record an independent test evaluation.")
        selected = joblib.load(MODEL_PATH)
        feature_names = getattr(selected, "feature_names_in_", None)
        if feature_names is not None and list(feature_names) != FEATURE_COLUMNS:
            raise ValueError("Model feature schema does not match the API schema.")
        threshold = metadata["threshold_selection"]["threshold"]
        if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
            raise ValueError("Configured decision threshold is invalid.")
        MODEL = selected
        MODEL_METADATA = metadata
        MODEL_VERSION = f"{metadata['selected_model']}:{artifact_hash[:12]}"
        MODEL_LOAD_ERROR = None
    except Exception as error:  # Keep the API importable so readiness can report failure.
        MODEL = None
        MODEL_LOAD_ERROR = f"Artifact loading failed: {error}"


_load_artifact()


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    Time: float = Field(ge=0, description="Non-negative elapsed seconds in the source dataset")
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    Amount: float = Field(ge=0, description="The source dataset has no negative transaction amounts")


app = FastAPI(
    title="Fraud Detection API",
    description="Scores credit-card transaction features using a versioned local model artifact.",
    version="2.0.0",
)
origins = [item.strip() for item in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, error: RequestValidationError) -> JSONResponse:
    # Exclude raw input values because invalid JSON-compatible numbers such as NaN
    # cannot be serialized into a standards-compliant JSON error response.
    errors = [
        {key: value for key, value in item.items() if key not in {"input", "ctx", "url"}}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


def _require_model() -> None:
    if MODEL is None:
        raise HTTPException(
            status_code=503,
            detail={"code": "model_not_ready", "message": MODEL_LOAD_ERROR or "Model is unavailable."},
        )


def _score(frame: pd.DataFrame) -> np.ndarray:
    _require_model()
    if list(frame.columns) != FEATURE_COLUMNS:
        raise ValueError("Input feature order does not match the trained model.")
    scores = np.asarray(MODEL.predict_proba(frame), dtype=float)
    if scores.ndim != 2 or scores.shape != (len(frame), 2):
        raise ValueError("The loaded model did not return the expected two-class score matrix.")
    positive_scores = scores[:, 1]
    if not np.isfinite(positive_scores).all() or ((positive_scores < 0) | (positive_scores > 1)).any():
        raise ValueError("The model returned invalid scores.")
    return positive_scores


@app.get("/health")
@app.get("/")
def health() -> dict:
    return {"status": "ok", "api_version": app.version}


@app.get("/ready")
def readiness() -> dict:
    if MODEL is None:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "reason": MODEL_LOAD_ERROR})
    return {
        "status": "ready",
        "model_version": MODEL_VERSION,
        "score_semantics": MODEL_METADATA.get("score_semantics"),
        "threshold": MODEL_METADATA["threshold_selection"]["threshold"],
        "features": FEATURE_COLUMNS,
    }


@app.get("/metrics")
def evaluation_metrics() -> dict:
    _require_model()
    return MODEL_METADATA


@app.post("/predict")
def predict(transaction: Transaction) -> dict:
    _require_model()
    frame = pd.DataFrame([transaction.model_dump()], columns=FEATURE_COLUMNS)
    try:
        score = float(_score(frame)[0])
    except ValueError as error:
        raise HTTPException(status_code=422, detail={"code": "invalid_model_input", "message": str(error)}) from error
    threshold = float(MODEL_METADATA["threshold_selection"]["threshold"])
    return {
        "predicted_label": int(score >= threshold),
        "model_score": score,
        "score_semantics": MODEL_METADATA["score_semantics"],
        "threshold": threshold,
        "model_version": MODEL_VERSION,
        "status": "scored",
    }


@app.post("/predict/batch")
async def predict_batch(file: UploadFile = File(...)) -> dict:
    _require_model()
    if not file.filename or Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(status_code=415, detail={"code": "unsupported_file", "message": "Upload a .csv file."})
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail={"code": "file_too_large", "message": f"Maximum upload size is {MAX_UPLOAD_BYTES} bytes."})
    if not contents.strip():
        raise HTTPException(status_code=422, detail={"code": "empty_file", "message": "The CSV file is empty."})
    started = time.perf_counter()
    try:
        frame = pd.read_csv(io.BytesIO(contents))
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as error:
        raise HTTPException(status_code=422, detail={"code": "malformed_csv", "message": str(error)}) from error
    if frame.empty:
        raise HTTPException(status_code=422, detail={"code": "empty_file", "message": "The CSV has a header but no data rows."})
    if len(frame) > MAX_BATCH_ROWS:
        raise HTTPException(status_code=413, detail={"code": "too_many_rows", "message": f"Maximum batch size is {MAX_BATCH_ROWS} rows."})
    missing = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    extra = [str(column) for column in frame.columns if column not in FEATURE_COLUMNS]
    if missing or extra:
        raise HTTPException(status_code=422, detail={"code": "schema_mismatch", "missing_columns": missing, "extra_columns": extra})

    valid_positions: list[int] = []
    errors: list[dict] = []
    valid_rows: list[dict] = []
    for position, row in enumerate(frame[FEATURE_COLUMNS].to_dict(orient="records"), start=2):
        try:
            transaction = Transaction.model_validate(row)
            valid_rows.append(transaction.model_dump())
            valid_positions.append(position - 2)
        except Exception as error:
            errors.append({"row": position, "status": "rejected", "error": str(error)})

    result_rows: list[dict] = []
    for error in errors:
        result_rows.append(error)
    if valid_rows:
        valid_frame = pd.DataFrame(valid_rows, columns=FEATURE_COLUMNS)
        try:
            scores = _score(valid_frame)
        except ValueError as error:
            raise HTTPException(status_code=422, detail={"code": "invalid_model_input", "message": str(error)}) from error
        threshold = float(MODEL_METADATA["threshold_selection"]["threshold"])
        for row_index, score in zip(valid_positions, scores):
            result_rows.append({
                "row": row_index + 2,
                "status": "scored",
                "predicted_label": int(score >= threshold),
                "model_score": float(score),
                "threshold": threshold,
                "model_version": MODEL_VERSION,
            })
    result_rows.sort(key=lambda result: result["row"])
    result_id = uuid.uuid4().hex
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)
    result_file = REPORTS_PATH / f"batch_{result_id}.csv"
    output = frame.copy()
    output["prediction_status"] = "rejected"
    output["predicted_label"] = pd.NA
    output["model_score"] = pd.NA
    output["row_error"] = pd.NA
    errors_by_row = {item["row"] - 2: item["error"] for item in errors}
    for row_index, message in errors_by_row.items():
        output.loc[row_index, "row_error"] = message
    if valid_rows:
        output.loc[valid_positions, "prediction_status"] = "scored"
        output.loc[valid_positions, "predicted_label"] = [item["predicted_label"] for item in result_rows if item["status"] == "scored"]
        output.loc[valid_positions, "model_score"] = [item["model_score"] for item in result_rows if item["status"] == "scored"]
    output.to_csv(result_file, index=False)
    processed = len(valid_positions)
    rejected = len(errors)
    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    return {
        "status": "completed",
        "result_id": result_id,
        "rows_received": len(frame),
        "rows_processed": processed,
        "rows_rejected": rejected,
        "predicted_positive": sum(item.get("predicted_label") == 1 for item in result_rows),
        "duration_ms": duration_ms,
        "score_semantics": MODEL_METADATA["score_semantics"],
        "model_version": MODEL_VERSION,
        "results": result_rows,
        "download_url": f"/predict/batch/{result_id}/download",
    }


@app.get("/predict/batch/{result_id}/download")
def download_batch(result_id: str) -> FileResponse:
    if len(result_id) != 32 or any(character not in "0123456789abcdef" for character in result_id):
        raise HTTPException(status_code=404, detail={"code": "result_not_found", "message": "Batch result not found."})
    path = REPORTS_PATH / f"batch_{result_id}.csv"
    if not path.is_file():
        raise HTTPException(status_code=404, detail={"code": "result_not_found", "message": "Batch result not found."})
    return FileResponse(path, media_type="text/csv", filename=f"fraud_predictions_{result_id}.csv")
