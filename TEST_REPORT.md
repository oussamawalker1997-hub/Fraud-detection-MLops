# Test Report

## 2026-10-19 implementation verification

### Data split and model training

- Command: `venv\Scripts\python.exe -m src.data.make_dataset`.
- Result: raw 284,807 rows; 1,081 exact duplicates removed; chronological partitions: train 198,609 rows / 366 positives, validation 42,560 / 55, test 42,557 / 52. Equal `Time` values stayed within one partition.
- Command: `venv\Scripts\python.exe -m src.training.train`.
- Result: completed with seed 42; logistic baseline compared with 8 randomized XGBoost configurations; 3 expanding chronological CV folds with equal timestamps grouped; best CV average precision 0.7882575406. Selected model was `xgboost_randomized_search` based on validation AP.
- Threshold: 0.6710811257, chosen by validation F1 only.
- Validation comparison: logistic baseline average precision 0.8366500173, precision 0.9130, recall 0.7636, F1 0.8317; tuned XGBoost average precision 0.8491924764, precision 0.9773, recall 0.7818, F1 0.8687.
- Independent test result: 42,557 rows / 52 positives; average precision 0.7664958070; ROC-AUC 0.9887913639; precision 0.8809523810; recall 0.7115384615; F1 0.7872340426; accuracy 0.9995300421; TN=42,500, FP=5, FN=15, TP=37.
- Artifacts: `models/fraud_model.joblib`, `reports/evaluation_metrics.json`, `reports/hyperparameter_search.csv`. API verified the metadata’s model hash at import and loaded the fitted model.

### Python tests

- Initial collection failed because the existing virtual environment had the unrelated `multipart` package instead of `python-multipart`.
- The repository virtual environment was repaired by uninstalling `multipart` and installing the already-declared `python-multipart` dependency. The first attempt used the sandbox’s restricted OS temp directory and failed; retrying with temp under the writable Codex workspace succeeded.
- Command: `venv\Scripts\python.exe -m pytest tests/ -q --basetemp='C:\Users\oussa\Documents\Codex\2026-10-19\files-pasted-by-the-user-codex\work\pytest-run-final'`.
- Result: 13 passed, 1 Starlette/httpx deprecation warning. Coverage includes saved-artifact prediction, readiness, finite/domain input rejection, chronological data preparation and CV folds, CSV validation, row errors, and enriched CSV download.
- Environment note: an explicit `--basetemp` under the writable workspace is needed in this sandbox because pytest cannot create its normal temp directory under the protected OS temp path.

### Frontend and source checks

- Command: `npm run build` in `frontend/`.
- Result: TypeScript compilation and Vite production build succeeded.
- Command: `venv\Scripts\python.exe -m compileall -q src tests`.
- Result: succeeded.

### Docker

- `docker --version`: Docker CLI 29.8.2 is installed.
- `docker build -t fraud-detection-api:local .`: could not proceed; Docker first lacked access to the protected buildx config lock. Using a writable `DOCKER_CONFIG` then failed with permission denied on `npipe:////./pipe/docker_engine`.
- Historical result: the restricted execution environment could not access the Docker engine. This limitation was subsequently resolved for local validation on 2026-10-20; the image build and container startup succeeded on Windows Docker Desktop, as documented below.

## Baseline audit results

- Raw data: 284,807 rows, 31 columns, no missing values, 1,081 exact duplicate rows, class counts 284,315/492, `Time` monotonic from 0 to 172,792.
- Original random splits shared exact row hashes across partitions: 188 train/validation, 217 train/test, 48 validation/test.
- Initial test collection failed because FastAPI detected `multipart` in place of `python-multipart`; corrected locally as recorded above.

## Remaining verification

- Run Docker build and API/browser batch flow outside the restricted Docker engine environment.
- CI has not been run.
- Dataset provenance/license and production operating threshold remain unresolved.

## 2026-10-20 Docker validation update

The earlier Docker access failure was specific to the restricted execution environment. Subsequent tests on the local Windows Docker Desktop engine succeeded.

- Docker Engine 29.8.2, Linux containers via WSL2.
- Image build succeeded: `docker build -t fraud-detection-api:local-test .`.
- Container started successfully on host port 8081, preserving the existing service on port 8080.
- `GET /health`: HTTP 200, API version 2.0.0.
- `GET /ready`: HTTP 200, model version `xgboost_randomized_search:dfd3ee1ed7e0`.
- `POST /predict`: HTTP 200 for one normal and one fraudulent test transaction; both matched their known labels.
- `POST /predict/batch`: HTTP 200; 10 rows received and processed, zero rejected.
- Batch CSV download: HTTP 200, `text/csv`, 5,753 bytes.
- These checks demonstrate local functionality, not production readiness or a successful clean GitHub checkout.
- GitHub Actions jobs have not yet been executed remotely.

## 2026-10-21 Cloud Run and GCS integration validation

### Source and build

- Branch: `feature/gcs-artifact-loading`.
- Tested source commit: `0f4ea91`.
- Cloud Build ID: `b1337eb4-baf9-44a0-9284-7682c5a7a17c`.
- Cloud Build final status: SUCCESS.
- Image digest: `sha256:304f9a8ca63dc54492198a8ceeecb4a8f6e533b2a79c22f74cedb1ce4e50226e`.

### Automated tests

- Command: `REPORTS_BUCKET="" .venv/bin/python -m pytest tests/ -v`.
- Result: 22 passed, 1 skipped, 0 failed.
- The skipped test requires a local trained model artifact.
- Six GCS tests used mocks, including the CSV API upload/download workflow.
- These unit tests do not independently verify IAM or real GCS writes.

### Private Cloud Run validation

- Service: `fraud-detection-api`.
- Test revision: `fraud-detection-api-00022-yas`.
- Main production traffic remained 100% on `00019-b66`.
- Test revision received 0% of main traffic.
- `/health`: HTTP 200.
- `/ready`: HTTP 200.
- Loaded model: `xgboost_randomized_search:dfd3ee1ed7e0`.
- Synthetic CSV batch prediction: HTTP 200, one row processed.
- Actual GCS report creation confirmed.
- Authenticated CSV download: HTTP 200.
- Nonexistent report: HTTP 404.
- Anonymous readiness and report download: HTTP 403.

### GCS persistence evidence

- Reports bucket: `fraud-mlops-reports-723029796275`.
- Object: `batch/batch_cd5ba15160df454f996d042c94d65eb6.csv`.
- Object size: 326 bytes.
- API and GCS downloads were byte-for-byte identical.
- SHA-256: `bcf19f244e4ec71529b8f2d85fc62ad507711c99653730a74b1e5f5f7948f890`.
- Lifecycle rule: delete objects under `batch/` after 7 days.
- Soft Delete: separate 7-day recovery period.

### Remaining limitations

- No per-user ownership authorization for report downloads.
- Model scores are not calibrated fraud probabilities.
- No real-time production transaction stream.
- Private test validation does not establish public production readiness.
