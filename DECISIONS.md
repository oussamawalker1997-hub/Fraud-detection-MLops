# Decisions

## 2026-10-19 — Preserve local state and audit before changes

- The user explicitly identified `C:\Users\oussa\fraud-detection-mlops` as the local source of truth and provided the matching GitHub URL.
- The outer checkout's `origin` matches that URL. It contains existing uncommitted changes to `.github/workflows/main.yml`, `requirements.txt`, and a nested same-repository submodule pointer. These are preserved.
- The nested checkout currently points to `b57cf61`, while the outer checkout records another commit. Do not reset or move either state as part of routine work.

## 2026-10-19 — No score or performance claims without an evaluated artifact

- Current artifacts are multiple and some use generic feature signatures; startup discovery order cannot establish the intended production/demo model. Require explicit artifact identity and schema validation before serving.
- XGBoost `predict_proba` output is not assumed calibrated. API/UI terminology should say score unless calibration is separately fit on training/validation data and assessed on the independent test set.
- Rule-generated explanations are not model explanations and will not be presented as such.

## 2026-10-19 — Split integrity is a prerequisite

- The raw data contains exact duplicate rows and existing partitions share exact rows. Rebuild splits only after resolving duplicates and documenting the temporal versus stratified evaluation rationale.
- Never use the test set for model search, calibration, threshold selection, or feature decisions.

## 2026-10-19 — Local evaluation and serving contract

- Use deduplicated chronological 70/15/15 partitions with equal timestamps grouped together. This reflects the observed `Time` ordering and avoids the exact duplicate overlap in the previous row-random split. The resulting distribution shift is disclosed.
- Use a class-weighted logistic regression baseline and tune XGBoost with three expanding chronological folds and average precision. Select model using validation average precision; choose a demonstration threshold by validation F1 because no review-cost target was supplied.
- Persist model and its metric metadata as a pair. The API verifies model SHA-256 and exact feature order before readiness. Keep the pair together when retraining or packaging.
- Process bounded CSV batches synchronously for this local demonstration; this provides immediate result rows and a generated download without claiming durable background-job infrastructure.
- The browser demo is not an authentication boundary. Remove the embedded default API key and document the API as local-only rather than shipping a client-side secret.
- Enforce non-negative `Time` and `Amount`: `Time` is elapsed duration and the observed data has no negative `Amount` values. Keep V feature domains open except for numeric finiteness because the anonymized feature semantics are not available.
