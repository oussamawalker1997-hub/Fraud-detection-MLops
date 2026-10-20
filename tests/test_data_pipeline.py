from __future__ import annotations

import pandas as pd
import pytest

from src.data.make_dataset import EXPECTED_COLUMNS, prepare_and_split_data
from src.training.train import _chronological_group_splits


def small_dataset() -> pd.DataFrame:
    rows = []
    for index in range(12):
        row = {column: float(index) for column in EXPECTED_COLUMNS[:-1]}
        row["Class"] = index % 2
        rows.append(row)
    return pd.DataFrame(rows, columns=EXPECTED_COLUMNS)


def test_split_removes_exact_duplicates_and_preserves_time_order(tmp_path) -> None:
    source = tmp_path / "raw.csv"
    data = small_dataset()
    data = pd.concat([data, data.iloc[[2]]], ignore_index=True)
    data.to_csv(source, index=False)

    summary = prepare_and_split_data(source, tmp_path / "processed", 0.5, 0.25)
    assert summary["dataset"]["removed_duplicates"] == 1
    splits = {
        name: pd.read_csv(tmp_path / "processed" / f"{name}.csv")
        for name in ("train", "val", "test")
    }
    assert splits["train"]["Time"].max() < splits["val"]["Time"].min()
    assert splits["val"]["Time"].max() < splits["test"]["Time"].min()
    assert all(set(part["Class"].unique()) == {0, 1} for part in splits.values())
    assert not set(splits["train"].itertuples(index=False, name=None)).intersection(
        splits["test"].itertuples(index=False, name=None)
    )


def test_split_rejects_wrong_schema(tmp_path) -> None:
    source = tmp_path / "raw.csv"
    small_dataset().rename(columns={"Class": "label"}).to_csv(source, index=False)
    with pytest.raises(ValueError, match="Expected columns"):
        prepare_and_split_data(source, tmp_path / "processed")


def test_split_rejects_missing_values(tmp_path) -> None:
    source = tmp_path / "raw.csv"
    data = small_dataset()
    data.loc[0, "V1"] = float("nan")
    data.to_csv(source, index=False)
    with pytest.raises(ValueError, match="Missing values"):
        prepare_and_split_data(source, tmp_path / "processed")


def test_cv_folds_are_expanding_and_keep_equal_times_together() -> None:
    frame = small_dataset()
    frame["Time"] = [index // 2 for index in range(len(frame))]
    X = frame.drop(columns="Class")
    y = frame["Class"]
    folds = _chronological_group_splits(X, y)
    for train_indices, validation_indices in folds:
        assert X.iloc[train_indices]["Time"].max() < X.iloc[validation_indices]["Time"].min()
        assert y.iloc[validation_indices].nunique() == 2
