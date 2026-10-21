# Fraud Detection MLOps — Recruiter Demo

## 1. Purpose

Demonstrate a working fraud detection application:

React -> Vite development proxy -> authenticated Cloud Run proxy
-> private FastAPI -> XGBoost -> private Google Cloud Storage.

This is a controlled demonstration, not a public production deployment.

## 2. Prerequisites

- Google Cloud Shell with project access
- Google Cloud CLI authenticated with permission to invoke the service
- Node.js and npm
- Repository checked out on feature/gcs-artifact-loading
- Private Cloud Run revision tagged api-gcs-test

Google Cloud project: project-e660b9f9-5c55-4bdd-ab0
Region: europe-west1
Service: fraud-detection-api

## 3. Terminal 1 — Cloud Run IAM proxy

From Cloud Shell:

    gcloud run services proxy fraud-detection-api \
      --project=project-e660b9f9-5c55-4bdd-ab0 \
      --region=europe-west1 \
      --tag=api-gcs-test \
      --port=8080

Keep this terminal running.

## 4. Terminal 2 — React frontend

    cd ~/fraud-detection-gcs-build/frontend
    npm ci --allow-remote=all
    VITE_API_URL=/api npm run dev -- \
      --host 127.0.0.1 --port 5173 --strictPort

Open the frontend using Cloud Shell Web Preview for port 5173.

The Vite development proxy forwards /api requests to the
authenticated proxy on 127.0.0.1:8080.

Do not embed Google Cloud credentials in frontend code.
Do not publish this development proxy as a public service.

## 5. Demonstration sequence

1. Show the model readiness indicator.
2. Explain the saved independent test-set metrics.
3. Submit a synthetic transaction with 30 input features.
4. Show the model score and decision threshold.
5. Import a CSV with Time, V1-V28, and Amount columns.
6. Show processed, rejected, and flagged transaction counts.
7. Download the enriched CSV and inspect its output columns.
8. Explain that batch reports are persisted in private GCS.

## 6. Verified model results

Model: xgboost_randomized_search:dfd3ee1ed7e0

Decision threshold: 0.6710811257362366

Independent test set:
- Rows: 42,557
- Actual fraud cases: 52
- True positives: 37
- False negatives: 15
- False positives: 5
- True negatives: 42,500
- Average precision: approximately 0.7665
- ROC-AUC: approximately 0.9888
- Precision: approximately 0.881
- Recall: approximately 0.7115
- F1: approximately 0.787

The model score is not a calibrated fraud probability.
These are offline test-set metrics, not live production results.

## 7. Evidence from the verified demo

- React frontend rendered successfully with Tailwind CSS 4.
- Single-transaction scoring worked in the browser.
- Three synthetic CSV transactions were processed successfully.
- Zero rows were rejected in that batch.
- The enriched CSV was downloaded and opened successfully.
- A 455-byte CSV report was observed in the private reports bucket:
  batch/batch_f28903a68f3d4ceab45a954e836e0d9e.csv
- GitHub Actions run 39690379830 succeeded:
  22 passed, 1 skipped across both jobs.

## 8. Architecture and limitations

Model artifacts are mounted read-only from private GCS storage.
Batch reports are written to a separate private GCS bucket.

The tested Cloud Run revision is accessible through IAM.
The development frontend relies on a local authenticated proxy.

Not yet implemented or validated:
- Public multi-user authentication and report ownership isolation
- Live payment transaction ingestion
- End-to-end production monitoring and alerting
- Model score calibration
- Production traffic migration to the tested revision

The verified test revision receives 0% of main Cloud Run traffic
at the time of the original deployment validation.

## 9. Suggested recruiter explanation

"This project implements a reproducible fraud detection pipeline
using XGBoost and an independent chronological test split.
I containerized the inference API with Docker and deployed it
privately to Google Cloud Run. The trained model is loaded from
read-only Cloud Storage, while enriched batch prediction reports
are persisted in a separate private bucket.

I added automated API, data pipeline, GCS integration, and
monitoring tests in GitHub Actions. The React frontend allows
single-transaction predictions and CSV batch processing.

The system is validated as a controlled cloud demonstration.
Before public production use, I would implement user-level
authorization, monitoring and alerting, and operational controls."
