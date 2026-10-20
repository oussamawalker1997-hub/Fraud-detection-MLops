# Implementation Plan

This plan follows the verified audit in `PROJECT_STATUS.md`. Existing working-tree changes must be preserved.

## P0 — Serving correctness and misleading outputs

1. **Complete locally:** Replace first-file MLflow discovery with explicit paired artifact/metadata loading, hash/schema checks, and readiness diagnostics. Validate feature order and output shape/range.
   - Acceptance: startup is not ready if the configured artifact is absent or schema-incompatible; valid predictions identify the loaded artifact; no other artifact can be selected by directory traversal order.
2. **Complete locally:** Remove fabricated rule-based explanations and unsupported “confirmed fraud” language. Return uncalibrated score semantics honestly.
   - Acceptance: API and UI distinguish model prediction from confirmed fraud and document threshold/score semantics.
3. **Complete locally:** Repair API input/error handling, finite numeric checks, schema errors, bounded input, and configurable frontend origin/base URL. The demo API remains unauthenticated and local-only.
   - Acceptance: malformed, non-finite, missing, and incompatible inputs produce structured client errors; secrets are not embedded in shipped frontend code.

## P1 — Data integrity and genuine modeling

1. **Partially complete:** Validate exact schema, target, missingness, finite values, duplicate count, and feature range; document that source/version/license remain unverified.
2. **Complete locally:** Deduplicate before an ordered 70/15/15 chronological split and keep equal timestamps together. Document later-period performance change.
3. **Complete locally:** Train logistic baseline and tuned XGBoost with time-series CV, randomized search on train only, model selection on validation AP, and F1 threshold selection on validation only.
4. **Complete locally:** Evaluate once on the independent test set and persist metrics, confusion counts, threshold, search results, data hash, and artifact hash.
   - Acceptance: the run is reproducible from documented commands; no test rows influence fitting, search, calibration, or threshold selection; all reported numbers are generated from saved evaluation outputs.

## P2 — API/frontend and CSV workflow

1. **Complete locally:** Load the trained model and expose health/readiness, prediction, and evaluation metadata endpoints.
2. **Complete locally:** Synchronous bounded CSV processing returns row-level errors and writes a downloadable result.
3. **Complete locally:** Render metrics, scores, processing counts/duration, row outcomes, and export link in the frontend.
   - Acceptance: valid upload to downloadable output works end-to-end; empty/malformed/schema-invalid/invalid-row cases are explicit and tested.

## P3 — Reproducibility and operations

1. **Complete locally:** Repair API tests and add data-split, saved-model, validation, and batch/download integration coverage; 11 tests pass.
2. **Partially complete:** Document reproducible commands and package the paired model/metrics in Docker context. Docker image build, container startup, health/readiness endpoints, individual predictions, batch scoring, and CSV download were successfully validated locally on 2026-10-20. GitHub Actions CI remains unverified because no remote workflow run has been completed.
3. **Deferred:** Existing drift monitors remain disconnected from any real event stream.
   - Acceptance: test report records commands, environment, actual outcomes, and limitations; Docker/CI do not use hidden external artifact assumptions.
