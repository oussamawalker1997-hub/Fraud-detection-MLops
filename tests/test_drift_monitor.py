
"""Unit tests for the experimental data drift monitoring module."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.multitest import multipletests


# Import the standalone monitoring module without modifying
# the API implementation or its environment configuration.
MONITORING_DIR = Path(__file__).resolve().parents[1] / "src" / "monitoring"
sys.path.insert(0, str(MONITORING_DIR))

from drift_monitor_v2 import calculate_ks_drift  # noqa: E402


def test_identical_data_has_no_drift():
    """Identical datasets must not trigger a drift alert."""
    reference = pd.DataFrame({
        "V1": np.arange(100, dtype=float),
        "Amount": np.linspace(0, 1000, 100),
    })

    current = reference.copy()

    result = calculate_ks_drift(reference, current)

    assert result["total_features"] == 2
    assert result["drifted_features"] == 0
    assert result["drift_share"] == 0.0
    assert result["global_drift_detected"] is False

    for column in result["columns"].values():
        assert column["ks_statistic"] == 0.0
        assert column["adjusted_p_value"] == pytest.approx(1.0)
        assert column["drift_detected"] is False


def test_large_distribution_shift_is_detected():
    """Strong synthetic distribution changes must be detected."""
    reference = pd.DataFrame({
        "V1": np.linspace(0, 1, 200),
        "V2": np.linspace(1, 2, 200),
        "Amount": np.linspace(10, 100, 200),
    })

    current = reference + 10000.0

    result = calculate_ks_drift(reference, current)

    assert result["total_features"] == 3
    assert result["drifted_features"] == 3
    assert result["drift_share"] == pytest.approx(1.0)
    assert result["global_drift_detected"] is True

    for column in result["columns"].values():
        assert column["ks_statistic"] == pytest.approx(1.0)
        assert column["significant_after_bh"] is True
        assert column["above_ks_threshold"] is True
        assert column["drift_detected"] is True


def test_benjamini_hochberg_adjusted_p_values():
    """Reported adjusted p-values must match statsmodels."""
    reference = pd.DataFrame({
        "stable": np.linspace(0, 1, 200),
        "shifted": np.linspace(0, 1, 200),
        "other": np.linspace(0, 1, 200),
    })

    current = reference.copy()
    current["shifted"] += 10.0
    current["other"] += 0.1

    result = calculate_ks_drift(reference, current)

    names = list(result["columns"])
    raw_p_values = [
        result["columns"][name]["p_value"]
        for name in names
    ]

    rejected, adjusted, _, _ = multipletests(
        raw_p_values,
        alpha=0.05,
        method="fdr_bh",
    )

    for index, name in enumerate(names):
        details = result["columns"][name]

        assert details["adjusted_p_value"] == pytest.approx(
            adjusted[index]
        )
        assert details["significant_after_bh"] == bool(
            rejected[index]
        )


def test_different_feature_columns_are_rejected():
    """Reference and current datasets must share the same schema."""
    reference = pd.DataFrame({
        "V1": [1.0, 2.0, 3.0],
        "V2": [4.0, 5.0, 6.0],
    })

    current = pd.DataFrame({
        "V1": [1.0, 2.0, 3.0],
        "V3": [4.0, 5.0, 6.0],
    })

    with pytest.raises(ValueError, match="Feature columns do not match"):
        calculate_ks_drift(reference, current)
