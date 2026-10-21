# Fraud Detection MLOps Demo

A reproducible local fraud-scoring demo built around a FastAPI service, a React/Vite interface, and a trained scikit-learn/XGBoost artifact. Scores are model outputs, not calibrated probabilities. A predicted positive is a model flag, not confirmed fraud.

## Current verified model run

The saved model artifact and `reports/evaluation_metrics.json` in this local workspace were generated from `data/raw/creditcard.csv` with the training command below. The file has 284,807 rows, 492 positive labels, no missing values, and 1,081 exact duplicate rows. Its contents were verified against the Kaggle/ULB reference dataset after line-ending normalization. The reference source, appl

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


## Dataset provenance and licensing

**Reference dataset:** [Credit Card Fraud Detection — Machine Learning Group, Université libre de Bruxelles (ULB), Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud).

**Kaggle dataset version:** 3.

**Licensing:** Open Data Commons Open Database License (ODbL) for the database and Database Contents License (DbCL) v1.0 for the contents, as displayed on the Kaggle dataset page. Reuse and public distribution must comply with the applicable license terms, including attribution and any relevant obligations for derivative databases.

### Dataset integrity verification

The original Kaggle archive was independently downloaded and compared against the local training dataset on 2026-10-21.

| Verification | Result |
| --- | --- |
| Kaggle CSV SHA-256 | `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89` |
| Local training CSV SHA-256 | `d9ae10699d163a23d8639b64709a1ea597862458af3ce03632602bb30f273f86` |
| Original byte-for-byte comparison | Different |
| Comparison after CRLF-to-LF normalization | Identical |
| Kaggle CRLF line endings | 0 |
| Local CRLF line endings | 284,808 |

The difference is exclusively due to line-ending format. The dataset contents match exactly after line-ending normalization.

The local dataset SHA-256 also matches the `raw_data_sha256` recorded in `reports/evaluation_metrics.json`. The trained model artifact independently matches the `artifact_sha256` recorded in that metadata.

This establishes a reproducible technical link between the public reference dataset, the local training data, the evaluation metadata, and the trained XGBoost artifact. It does not independently establish the historical download location of the local file.

**Data distribution policy:** Raw transaction data and trained model artifacts are excluded from Git. Any deployment or redistribution must respect the applicable licenses, security requirements, and artifact access controls.

## Reproduce the model

Place the intended dataset at `data/raw/creditcard.csv` with columns `Time`, `V1`–`V28`, `Amount`, and `Class`. The reference dataset source, licensing information, and SHA-256 verification are documented in the "Dataset provenance and licensing" section above. The raw CSV is intentionally excluded from Git. Obtain the dataset from the referenced Kaggle source and comply with its applicable license terms.

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


The Docker image contains the API source code and its dependencies, but deliberately excludes the trained model and evaluation metadata.

Build the image from the repository root:

```powershell
docker build -t fraud-detection-api:local .
```

For local inference, provide the previously trained model and its evaluation metadata through read-only bind mounts:

```powershell
docker run --rm -p 127.0.0.1:8080:8080 `
  --mount "type=bind,source=C:\path\to\repo\models,target=/app/models,readonly" `
  --mount "type=bind,source=C:\path\to\repo\reports\evaluation_metrics.json,target=/app/reports/evaluation_metrics.json,readonly" `
  fraud-detection-api:local
```

Replace `C:\path\to\repo` with the actual local repository path. The PowerShell backticks above are line-continuation characters.

The API verifies the model's SHA-256 checksum, recorded evaluation status, feature schema, and decision threshold when loading the artifacts.

If the artifacts are missing or invalid, `/ready` returns HTTP 503 and inference is unavailable.

### Cloud Run artifact configuration

The planned Cloud Run deployment uses a private Google Cloud Storage bucket mounted read-only at `/mnt/artifacts`, with these environment variables:

```text
MODEL_PATH=/mnt/artifacts/models/v1/fraud_model.joblib
METRICS_PATH=/mnt/artifacts/models/v1/evaluation_metrics.json
```

The runtime service account is granted bucket-scoped object-read permissions. Artifacts are not committed to Git or embedded in the Docker image.

The corrected Docker image and external-volume loading have been tested locally. The Cloud Run deployment of API v2.0.0 has not yet been validated end to end. The currently deployed Cloud Run service was found to be running an older API v1.1.0.
## Limits and next steps

- API v2.0.0 and its external artifact loading have been verified locally. but its active revision was observed running the older API v1.1.0. Deployment of API v2.0.0 and end-to-end cloud inference remain unverified. No live transaction source is configured.
- The local training CSV matches the Kaggle/ULB reference dataset after CRLF-to-LF normalization. Reference licensing is documented above; deployment and redistribution must still comply with applicable license conditions.
- Scores are not calibrated, and F1 threshold selection is not based on a documented fraud-review cost model.
- The chronological split is useful for a future-period demonstration, but it covers this dataset’s short source period only.
- Existing drift-monitoring utilities are not connected to a real production event stream.
- See `PROJECT_STATUS.md`, `IMPLEMENTATION_PLAN.md`, `DECISIONS.md`, and `TEST_REPORT.md` for current decisions, evidence, and unresolved work.
