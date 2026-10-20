"""Train, compare, and independently evaluate the fraud scoring pipeline.

Run from the repository root with:
    python -m src.training.train

Model selection and threshold selection use validation data only. The test set is
loaded only after both decisions are frozen.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from src.data.make_dataset import FEATURE_COLUMNS, TARGET_COLUMN

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
SEED = 42
N_ITER = 8
N_SPLITS = 3


def _read_split(name: str) -> tuple[pd.DataFrame, pd.Series]:
    frame = pd.read_csv(DATA_DIR / f"{name}.csv")
    expected = [*FEATURE_COLUMNS, TARGET_COLUMN]
    if list(frame.columns) != expected:
        raise ValueError(f"{name} schema mismatch; expected {expected}")
    if frame.empty or frame.isna().any().any():
        raise ValueError(f"{name} must be non-empty and contain no missing values")
    if not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise ValueError(f"{name} contains non-finite values")
    if set(frame[TARGET_COLUMN].unique()) != {0, 1}:
        raise ValueError(f"{name} must contain both Class values 0 and 1")
    return frame[FEATURE_COLUMNS], frame[TARGET_COLUMN].astype(int)


def _threshold_for_best_f1(y_true: pd.Series, scores: np.ndarray) -> float:
    candidates = np.unique(np.r_[0.0, scores, 1.0])
    values = [f1_score(y_true, scores >= threshold, zero_division=0) for threshold in candidates]
    # In an exact F1 tie, use the higher threshold to reduce false-positive volume.
    best = max(range(len(values)), key=lambda index: (values[index], candidates[index]))
    return float(candidates[best])


def _evaluate(y_true: pd.Series, scores: np.ndarray, threshold: float) -> dict:
    predicted = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "precision": float(precision_score(y_true, predicted, zero_division=0)),
        "recall": float(recall_score(y_true, predicted, zero_division=0)),
        "f1": float(f1_score(y_true, predicted, zero_division=0)),
        "average_precision": float(average_precision_score(y_true, scores)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "accuracy": float(accuracy_score(y_true, predicted)),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "rows": int(len(y_true)),
        "positive_labels": int(y_true.sum()),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _chronological_group_splits(X: pd.DataFrame, y: pd.Series) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create expanding chronological folds without splitting equal timestamps."""
    time_blocks = np.array_split(np.sort(X["Time"].unique()), N_SPLITS + 1)
    if any(len(block) == 0 for block in time_blocks):
        raise ValueError("Not enough distinct Time groups for chronological cross-validation")
    folds = []
    for fold_index in range(1, N_SPLITS + 1):
        train_times = np.concatenate(time_blocks[:fold_index])
        validation_times = time_blocks[fold_index]
        train_indices = np.flatnonzero(X["Time"].isin(train_times).to_numpy())
        validation_indices = np.flatnonzero(X["Time"].isin(validation_times).to_numpy())
        if not len(train_indices) or not len(validation_indices):
            raise ValueError(f"Chronological CV fold {fold_index} is empty")
        if y.iloc[validation_indices].nunique() != 2:
            raise ValueError(f"Chronological CV fold {fold_index} lacks a target class")
        folds.append((train_indices, validation_indices))
    return folds


def train() -> dict:
    X_train, y_train = _read_split("train")
    X_val, y_val = _read_split("val")

    # Expanding folds keep all rows with equal Time in the same fold.
    folds = _chronological_group_splits(X_train, y_train)

    baseline = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=SEED, solver="lbfgs"
        ),
    )
    baseline.fit(X_train, y_train)
    baseline_scores = baseline.predict_proba(X_val)[:, 1]
    baseline_threshold = _threshold_for_best_f1(y_val, baseline_scores)
    baseline_validation = _evaluate(y_val, baseline_scores, baseline_threshold)

    positive_weight = float((y_train == 0).sum() / (y_train == 1).sum())
    candidate = XGBClassifier(
        objective="binary:logistic",
        eval_metric="aucpr",
        tree_method="hist",
        scale_pos_weight=positive_weight,
        random_state=SEED,
        n_jobs=1,
        verbosity=0,
    )
    search_space = {
        "n_estimators": [100, 200, 350],
        "max_depth": [2, 3, 4, 5],
        "learning_rate": [0.03, 0.06, 0.1],
        "min_child_weight": [1, 3, 6],
        "subsample": [0.7, 0.85, 1.0],
        "colsample_bytree": [0.7, 0.85, 1.0],
        "reg_lambda": [1.0, 3.0, 8.0],
    }
    search = RandomizedSearchCV(
        estimator=candidate,
        param_distributions=search_space,
        n_iter=N_ITER,
        scoring="average_precision",
        cv=folds,
        random_state=SEED,
        n_jobs=1,
        refit=True,
        return_train_score=False,
        error_score="raise",
    )
    search.fit(X_train, y_train)
    tuned = search.best_estimator_
    tuned_val_scores = tuned.predict_proba(X_val)[:, 1]
    tuned_threshold = _threshold_for_best_f1(y_val, tuned_val_scores)
    tuned_validation = _evaluate(y_val, tuned_val_scores, tuned_threshold)

    if tuned_validation["average_precision"] >= baseline_validation["average_precision"]:
        selected_name, selected_model = "xgboost_randomized_search", tuned
        selected_threshold = tuned_threshold
        selected_validation = tuned_validation
    else:
        selected_name, selected_model = "logistic_regression_baseline", baseline
        selected_threshold = baseline_threshold
        selected_validation = baseline_validation

    # Test data is deliberately opened only after search, model selection, and
    # threshold selection are complete.
    X_test, y_test = _read_split("test")
    test_scores = selected_model.predict_proba(X_test)[:, 1]
    test_metrics = _evaluate(y_test, test_scores, selected_threshold)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    model_path = OUTPUT_DIR / "fraud_model.joblib"
    joblib.dump(selected_model, model_path)
    search_records = pd.DataFrame(search.cv_results_).sort_values("rank_test_score")
    search_records.to_csv(REPORT_DIR / "hyperparameter_search.csv", index=False)
    metrics = {
        "evaluation_status": "independent_test_evaluation",
        "selected_model": selected_name,
        "score_semantics": "Uncalibrated model score; do not interpret as a calibrated probability.",
        "threshold_selection": {
            "method": "maximize validation F1; ties choose the higher threshold",
            "threshold": selected_threshold,
            "validation": selected_validation,
        },
        "validation_comparison": {
            "logistic_regression_baseline": baseline_validation,
            "xgboost_randomized_search": tuned_validation,
        },
        "test": test_metrics,
        "search": {
            "method": "RandomizedSearchCV",
            "metric": "average_precision",
            "n_iter": N_ITER,
            "cv": "3 expanding chronological folds within train; equal Time groups kept together",
            "best_cv_average_precision": float(search.best_score_),
            "best_params": search.best_params_,
            "search_space": search_space,
        },
        "data": {
            "split_strategy": "deduplicated chronological 70/15/15, equal Time values kept together",
            "train_rows": int(len(y_train)),
            "validation_rows": int(len(y_val)),
            "test_rows": int(len(y_test)),
            "raw_data_sha256": _sha256(ROOT / "data" / "raw" / "creditcard.csv"),
        },
        "seed": SEED,
        "artifact": str(model_path.relative_to(ROOT)),
        "artifact_sha256": _sha256(model_path),
    }
    (REPORT_DIR / "evaluation_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    train()
