# Project Status

## Current state (2026-10-19)

The project is a local FastAPI + React/Vite fraud scoring demo. A canonical data/training path, actual scored API, CSV results/download, frontend integration, and a local model artifact/evaluation report have now been implemented and exercised. It is still not production-ready: dataset provenance/license are unknown, output scores are uncalibrated, the F1 threshold is only a demonstration choice, and deployed behavior is unverified.

### Repository identity and working state

- Local root: `C:\Users\oussa\fraud-detection-mlops`.
- `origin`: `https://github.com/oussamawalker1997-hub/fraud-detection-mlops.git` (matches the user-provided repository).
- Outer checkout branch: `main`, tracking `origin/main`.
- Pre-existing local changes: `.github/workflows/main.yml`, `requirements.txt`, and the `fraud-detection-mlops` submodule pointer. Preserve these changes.
- The nested `fraud-detection-mlops` checkout is the same GitHub repository at `b57cf61` on `main`; the outer checkout currently points to a different nested commit. Do not update or reset the pointer without user direction.
- No project memory documents existed at audit start.
- This working session generated a local model (`models/fraud_model.joblib`) and evaluation/search outputs. The model and evaluation JSON are available in the workspace; choose artifact versioning/distribution before publishing changes.

## Architecture observed

- `src/api/main.py`: FastAPI app, environment-based API key check, MLflow artifact discovery, individual scoring, background batch scoring, static report serving.
- `src/data/ingest_data.py`: basic raw CSV schema/missing-value summary.
- `src/data/make_dataset.py`: random stratified 70/15/15 split.
- `src/models/train_model.py` and `src/training/train.py`: separate XGBoost training paths with fixed parameters and MLflow logging.
- `data/raw/creditcard.csv` and processed train/validation/test CSVs: local data files.
- `mlruns/`, `mlflow.db`, and `mlruns.zip`: multiple tracked/local model artifacts and experiment state.
- `frontend/src/App.tsx`: manual prediction UI, CSV upload status, local prediction history.
- `tests/test_api.py`: API health and mocked single-prediction format checks.
- `Dockerfile` and `.github/workflows/main.yml`: container build and CI test/build workflow.

## Verified findings and completed repairs

1. **Repaired:** API now loads only `models/fraud_model.joblib` paired with `reports/evaluation_metrics.json`, verifies the artifact SHA-256 and feature schema, and reports readiness/model version. Multiple old MLflow artifacts are no longer searched at startup.
2. **Repaired:** API/UI report an uncalibrated model score, validation-selected threshold, model version, and predicted label. Rule-generated “explanations” and “confirmed fraud” language were removed.
3. **Repaired:** individual and batch input validation returns structured 4xx errors; Time and Amount must be non-negative based on observed feature semantics/data domain.
4. **Repaired:** synchronous bounded CSV processing reports row outcomes, counts, duration, and writes an enriched CSV behind an ID-validated download endpoint. Frontend displays results and download link.
5. **Repaired:** frontend uses configured API base URL, displays actual saved test metrics, and calls its local browser history “session prediction history.” Hardcoded key, invented scenario metadata, and the fake live-feed label were removed.
6. Dataset facts: 284,807 raw rows; 284,315 class 0 / 492 class 1; no missing values; 1,081 exact duplicates; monotonic `Time` from 0 to 172,792; `Amount` minimum 0. Provenance/license remain unverified and are explicitly documented.
7. **Repaired:** processed splits are deduplicated chronological 70/15/15 partitions with equal `Time` values kept together. Generated split totals are 198,609 / 42,560 / 42,557 with 366 / 55 / 52 positive labels; time ranges do not overlap. This replaces the earlier random split with 188/217/48 duplicate row intersections.
8. **Repaired:** canonical training uses a logistic baseline, 8-iteration randomized XGBoost search with three chronological time-series CV folds, validation-only AP model selection and F1 threshold choice, and one independent test evaluation. Search configurations and metrics are saved. The single older training entry point delegates to the canonical pipeline.
9. **Repaired locally:** initial test collection was blocked by the wrong `multipart` package. The repository venv was corrected to use the declared `python-multipart`; 11 tests pass. A Starlette/httpx deprecation warning remains.
10. `.gitignore` was UTF-16 encoded; Git did not apply many intended patterns. It is now UTF-8 with the existing intent retained, the model artifact explicitly included, and generated batch outputs ignored.

## Verified local training results

- Selected model: `xgboost_randomized_search`; 8 randomized settings; best timestamp-grouped CV average precision 0.7883.
- Validation: average precision 0.8492; threshold 0.671081; precision 0.9773; recall 0.7818; F1 0.8687.
- Independent chronological test: 42,557 rows / 52 positives; average precision 0.7665; ROC-AUC 0.9888; precision 0.8810; recall 0.7115; F1 0.7872; 5 false positives / 15 false negatives.
- These results are local to the supplied dataset snapshot and selected split. Scores are not calibrated; the threshold has no documented business-cost basis.

## Unresolved

- Dataset provenance, exact source/version, and license need evidence/documentation.
- Dataset source, version, and license need evidence; `data/raw` is ignored and not bundled.
- The new model is a local generated artifact. Versioning/transport policy must be settled before publishing a source revision or rebuilding elsewhere.
- Scores are not calibrated; no business review costs or operating requirements were supplied, so the F1-selected threshold is demonstrative.
- GitHub Actions CI has not yet been executed remotely. On 2026-10-20, Docker image build, container startup, API health/readiness checks, individual normal/fraud predictions, 10-row batch scoring, and CSV download all succeeded locally using Docker Desktop. This does not establish production readiness or reproducibility from a clean GitHub checkout.
- No deployed service, authenticated access layer, genuine event source, or production monitoring is configured.

## Next recommended task

Resolve dataset provenance/license and establish an artifact release/versioning process; then run the Docker image from a clean environment and complete a browser-to-API CSV upload/download demonstration. After those, define an operational review-cost target before selecting a deployment threshold or calibrating scores.

## Cloud Run and GCS validation (2026-10-21)

This section supersedes earlier statements that cloud deployment
and remote model inference had not been validated.

- Git branch: `feature/gcs-artifact-loading`.
- Tested commit: `0f4ea91`.
- Cloud Build: `b1337eb4-baf9-44a0-9284-7682c5a7a17c`, SUCCESS.
- Cloud Run test revision: `fraud-detection-api-00022-yas`.
- Production revision `00019-b66` retained 100% main traffic.
- Test revision `00022-yas` received 0% main traffic.
- `/health` and `/ready` returned HTTP 200.
- XGBoost model loaded from a read-only GCS mount.
- Synthetic batch prediction returned HTTP 200.
- Generated CSV was persisted in the private reports bucket.
- CSV download through the API returned HTTP 200.
- API and GCS copies were identical by SHA-256.
- Missing report returned HTTP 404.
- Anonymous readiness and report-download requests returned HTTP 403.
- Python suite: 22 passed, 1 skipped.
- GCS lifecycle deletes `batch/` objects after 7 days.
- Soft Delete provides a separate 7-day recovery period.

Remaining limitations:

- Model scores are uncalibrated.
- No live transaction stream or deployed drift-monitoring pipeline.
- No per-user ownership checks on downloaded reports.
- No public multi-user production readiness claim.
- GitHub Actions was verified remotely on commit `1edb728`:
  all four jobs passed (API and Data Pipeline, Evidently Monitoring,
  Frontend, and Cloud Run Development Proxy).
- This CI success does not establish public production readiness.
