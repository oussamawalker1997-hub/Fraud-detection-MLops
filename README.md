# Fraud Detection MLOps Demo

A reproducible local fraud-scoring demo built around a FastAPI service, a React/Vite interface, and a trained scikit-learn/XGBoost artifact. Scores are model outputs, not calibrated probabilities. A predicted positive is a model flag, not confirmed fraud.

## Current verified model run

The saved model artifact and `reports/evaluation_metrics.json` in this local workspace were generated from `data/raw/creditcard.csv` with the training command below. The file has 284,807 rows, 492 positive labels, no missing values, and 1,081 exact duplicate rows. Its provenance and license have not been verified, so obtain and document those before redistribution or production use.

The pipeline removes exact duplicate rows and creates chronological 70/15/15 train/validation/test partitions, keeping equal `Time` values together. Model search uses three expanding time-series folds within training only, also keeping equal timestamps together; best CV average precision was 0.7883. The model and decision threshold are selected on validation average precision and F1 respectively; the test partition is used once after those choices are frozen.

Recorded local test results (42,557 rows, 52 positive labels):

| Metric | Result |
| --- | ---: |
| Average precision | 0.7665 |
| ROC-AUC | 0.9888 |
| Precision | 0.8810 |
| Recall | 0.7115 |
| F1 | 0.7872 |
| False positives | 5 |
| False negatives | 15 |
| Validation-selected threshold | 0.6711 |

These are results from this local historical split, not a production guarantee. Validation average precision was 0.8492, so the later test period shows a meaningful performance drop. The raw score is uncalibrated and should not be interpreted as a probability. The F1-selected threshold is a demonstration choice, not a business-approved operating point.

## Reproduce the model

Place the intended dataset at `data/raw/creditcard.csv` with columns `Time`, `V1`–`V28`, `Amount`, and `Class`. The source and license are not bundled or established by this repository.

From the repository root:

```powershell
python -m pip install -r requirements-dev.txt
python -m src.data.make_dataset
python -m src.training.train
python -m pytest tests/test_api.py tests/test_data_pipeline.py -q
```

Training writes `models/fraud_model.joblib`, `reports/evaluation_metrics.json`, and `reports/hyperparameter_search.csv`. The generated model and evaluation JSON are present in this local workspace so the application can run without retraining. Re-training replaces those local artifacts; keep the model and metadata together because the API verifies their hash. Decide how to version or distribute these generated files before publishing a source revision.

## Monitoring tests

Run these tests in a separate Python 3.12 virtual environment to keep the Evidently dependencies isolated from the main API environment:

```powershell
python -m pip install -r requirements-monitoring.txt
python -m pytest tests/test_drift_monitor.py -q
```

## Run locally

Install the pinned dependencies in `requirements.txt`, then start the API and frontend in separate terminals:

```powershell
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8080
cd frontend
npm ci
npm run dev
```

The API binds locally in this example. For a different frontend origin, set `CORS_ORIGINS` to a comma-separated list before starting the API. Set `VITE_API_URL` in the frontend build environment if the API is not at `http://localhost:8080`.

The API has no authentication and is intended for a trusted local demonstration only. Do not expose it to an untrusted network. Production deployment requires authentication, rate/size controls appropriate to its environment, and a reviewed operating threshold.

## API

- `GET /health`: process health.
- `GET /ready`: model readiness, artifact version, feature schema, and threshold.
- `GET /metrics`: saved independent test evaluation and search metadata.
- `POST /predict`: one JSON object with exactly the 30 feature fields.
- `POST /predict/batch`: multipart CSV upload. Returns row-level predictions/errors and processing counts.
- `GET /predict/batch/{result_id}/download`: enriched CSV for a completed batch.

The batch CSV must contain exactly `Time`, `V1`–`V28`, and `Amount`. It must not contain the `Class` label. Invalid rows are rejected individually; malformed files or incompatible schemas receive structured 4xx responses.

## Docker

Before building the Docker image, obtain the dataset from an authorized source and run the data preparation and training commands above. The build requires locally generated models/fraud_model.joblib and reports/evaluation_metrics.json; these files are not currently tracked by Git. The API verifies the model artifact hash against its evaluation metadata at startup:

```powershell
docker build -t fraud-detection-api:local .
docker run --rm -p 8080:8080 fraud-detection-api:local
```

## Limits and next steps

- This project has only been verified locally; no deployed service or live transaction source is configured.
- The input dataset’s provenance/license remains unresolved.
- Scores are not calibrated, and F1 threshold selection is not based on a documented fraud-review cost model.
- The chronological split is useful for a future-period demonstration, but it covers this dataset’s short source period only.
- Existing drift-monitoring utilities are not connected to a real production event stream.
- See `PROJECT_STATUS.md`, `IMPLEMENTATION_PLAN.md`, `DECISIONS.md`, and `TEST_REPORT.md` for current decisions, evidence, and unresolved work.
