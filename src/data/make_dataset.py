"""Validate, deduplicate, and chronologically split the credit-card data."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import numpy as np

FEATURE_COLUMNS = ["Time", *[f"V{i}" for i in range(1, 29)], "Amount"]
TARGET_COLUMN = "Class"
EXPECTED_COLUMNS = [*FEATURE_COLUMNS, TARGET_COLUMN]


def prepare_and_split_data(
    input_filepath: str | Path,
    output_dir: str | Path,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> dict[str, dict[str, float | int]]:
    """Write chronological, duplicate-free splits, keeping equal timestamps together."""
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("Split fractions must be between zero and one.")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Train and validation fractions must sum to less than one.")

    source = Path(input_filepath)
    if not source.is_file():
        raise FileNotFoundError(f"Dataset file not found: {source}")
    df = pd.read_csv(source)
    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Expected columns in this exact order: {EXPECTED_COLUMNS}; got {list(df.columns)}"
        )
    if df.empty:
        raise ValueError("Dataset is empty.")
    if df.isna().any().any():
        bad = df.columns[df.isna().any()].tolist()
        raise ValueError(f"Missing values found in columns: {bad}")
    if not set(df[TARGET_COLUMN].unique()).issubset({0, 1}):
        raise ValueError("Target Class must contain only 0 and 1.")
    numeric = df[EXPECTED_COLUMNS].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        raise ValueError("All feature and target columns must be numeric.")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Infinite values are not supported.")

    original_count = len(df)
    df = numeric.drop_duplicates(keep="first").sort_values("Time", kind="stable").reset_index(drop=True)
    if df[TARGET_COLUMN].nunique() != 2:
        raise ValueError("Both target classes must remain after duplicate removal.")

    # Choose timestamp boundaries nearest the requested proportions without splitting
    # simultaneous records across train, validation, and test.
    timestamp_sizes = df.groupby("Time", sort=True).size()
    unique_times = timestamp_sizes.index.to_numpy()
    cumulative = timestamp_sizes.cumsum().to_numpy()
    train_target = len(df) * train_fraction
    validation_target = len(df) * (train_fraction + validation_fraction)
    train_end = int(abs(cumulative - train_target).argmin()) + 1
    validation_end = int(abs(cumulative - validation_target).argmin()) + 1
    train_end = min(max(train_end, 1), len(unique_times) - 2)
    validation_end = min(max(validation_end, train_end + 1), len(unique_times) - 1)
    train_cutoff = unique_times[train_end - 1]
    validation_cutoff = unique_times[validation_end - 1]

    splits = {
        "train": df.loc[df["Time"] <= train_cutoff],
        "val": df.loc[(df["Time"] > train_cutoff) & (df["Time"] <= validation_cutoff)],
        "test": df.loc[df["Time"] > validation_cutoff],
    }
    for name, part in splits.items():
        if part.empty or part[TARGET_COLUMN].nunique() != 2:
            raise ValueError(f"Chronological {name} split must contain both target classes.")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary: dict[str, dict[str, float | int]] = {
        "dataset": {"raw_rows": original_count, "deduplicated_rows": len(df), "removed_duplicates": original_count - len(df)}
    }
    for name, part in splits.items():
        part.to_csv(output / f"{name}.csv", index=False)
        summary[name] = {
            "rows": len(part),
            "frauds": int(part[TARGET_COLUMN].sum()),
            "fraud_rate": float(part[TARGET_COLUMN].mean()),
            "time_min": float(part["Time"].min()),
            "time_max": float(part["Time"].max()),
        }
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/creditcard.csv")
    parser.add_argument("--output", default="data/processed")
    args = parser.parse_args()
    for split_name, stats in prepare_and_split_data(args.input, args.output).items():
        print(f"{split_name}: {stats}")
