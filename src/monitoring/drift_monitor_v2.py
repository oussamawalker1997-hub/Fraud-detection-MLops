
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset
from scipy.stats import ks_2samp
from statsmodels.stats.multitest import multipletests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports" / "monitoring_v2"

SAMPLE_SIZE = 5000
RANDOM_STATE = 42

FDR_ALPHA = 0.05
KS_THRESHOLD = 0.10
GLOBAL_DRIFT_THRESHOLD = 0.50

EXCLUDED_COLUMNS = ("Class", "Time")


def load_features(filename: str) -> pd.DataFrame:
    """Load a reproducible sample of numerical model features."""
    path = DATA_DIR / filename

    if not path.is_file():
        raise FileNotFoundError(f"Missing dataset: {path}")

    data = pd.read_csv(path)

    missing = set(EXCLUDED_COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"Missing expected columns: {sorted(missing)}")

    features = data.drop(columns=list(EXCLUDED_COLUMNS))

    if features.empty or len(features) < SAMPLE_SIZE:
        raise ValueError(f"Insufficient data in {filename}")

    if features.isna().any().any():
        raise ValueError(f"Missing feature values in {filename}")

    if not all(
        pd.api.types.is_numeric_dtype(dtype)
        for dtype in features.dtypes
    ):
        raise ValueError(f"Non-numeric features in {filename}")

    if not np.isfinite(features.to_numpy(dtype=float)).all():
        raise ValueError(f"Non-finite feature values in {filename}")

    return features.sample(
        n=SAMPLE_SIZE,
        random_state=RANDOM_STATE,
    ).reset_index(drop=True)


def calculate_ks_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
) -> dict:
    """Compute per-feature KS statistics and BH-adjusted p-values."""
    if list(reference.columns) != list(current.columns):
        raise ValueError("Feature columns do not match")

    if reference.empty or current.empty:
        raise ValueError("Empty dataset")

    if not all(
        pd.api.types.is_numeric_dtype(dtype)
        for dtype in reference.dtypes
    ) or not all(
        pd.api.types.is_numeric_dtype(dtype)
        for dtype in current.dtypes
    ):
        raise ValueError("KS monitoring requires numeric features")

    columns = list(reference.columns)

    statistics = []
    p_values = []

    for column in columns:
        statistic, p_value = ks_2samp(
            reference[column].to_numpy(),
            current[column].to_numpy(),
        )
        statistics.append(float(statistic))
        p_values.append(float(p_value))

    rejected, adjusted_p_values, _, _ = multipletests(
        p_values,
        alpha=FDR_ALPHA,
        method="fdr_bh",
    )

    details = {}
    drifted_count = 0

    for index, column in enumerate(columns):
        significant = bool(rejected[index])
        meaningful = statistics[index] >= KS_THRESHOLD
        detected = significant and meaningful

        if detected:
            drifted_count += 1

        details[column] = {
            "ks_statistic": statistics[index],
            "p_value": p_values[index],
            "adjusted_p_value": float(adjusted_p_values[index]),
            "significant_after_bh": significant,
            "above_ks_threshold": meaningful,
            "drift_detected": detected,
        }

    share = drifted_count / len(columns)

    return {
        "total_features": len(columns),
        "drifted_features": drifted_count,
        "drift_share": share,
        "global_drift_detected": share > GLOBAL_DRIFT_THRESHOLD,
        "thresholds": {
            "fdr_alpha": FDR_ALPHA,
            "ks_statistic": KS_THRESHOLD,
            "global_drift_share": GLOBAL_DRIFT_THRESHOLD,
        },
        "columns": details,
    }


def generate_evidently_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generate an HTML report using Evidently 0.7.23."""
    report = Report(metrics=[DataDriftPreset()])

    snapshot = report.run(
        current_data=current,
        reference_data=reference,
    )

    snapshot.save_html(str(output_path))


def run_scenario(
    name: str,
    reference: pd.DataFrame,
    current: pd.DataFrame,
    output_dir: Path,
) -> dict:
    """Run statistical monitoring and produce an Evidently report."""
    results = calculate_ks_drift(reference, current)

    html_path = output_dir / f"{name}.html"

    generate_evidently_report(
        reference,
        current,
        html_path,
    )

    results["scenario"] = name
    results["html_report"] = str(html_path)

    print(f"\nScenario: {name}")
    print(
        f"Flagged features: "
        f"{results['drifted_features']}/"
        f"{results['total_features']}"
    )
    print(
        f"Global drift alert: "
        f"{results['global_drift_detected']}"
    )
    print(f"HTML report: {html_path}")

    return results


def main() -> None:
    print("=== FRAUD DETECTION - DRIFT MONITORING ===")

    reference = load_features("train.csv")
    current = load_features("test.csv")

    if list(reference.columns) != list(current.columns):
        raise ValueError("Train/test feature mismatch")

    print(f"Reference rows: {len(reference)}")
    print(f"Current rows: {len(current)}")
    print(f"Monitored features: {len(reference.columns)}")
    print("Excluded from alerts: Class, Time")

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output_dir = REPORTS_DIR / run_id
    output_dir.mkdir(parents=True, exist_ok=False)

    real_results = run_scenario(
        "chronological_train_vs_test",
        reference,
        current,
        output_dir,
    )

    # Synthetic stress test only: not representative of real fraud.
    simulated_current = current + 10000.0

    simulated_results = run_scenario(
        "synthetic_extreme_shift",
        reference,
        simulated_current,
        output_dir,
    )

    summary = {
        "monitoring_type": "experimental_batch_data_drift",
        "evidently_version": "0.7.23",
        "sample_size_per_dataset": SAMPLE_SIZE,
        "random_state": RANDOM_STATE,
        "excluded_columns": list(EXCLUDED_COLUMNS),
        "methodology": (
            "Two-sample KS per numerical feature, "
            "Benjamini-Hochberg FDR correction, "
            "and experimental KS magnitude threshold."
        ),
        "limitations": [
            "This is not a production monitoring service.",
            "The KS threshold has not been calibrated for production.",
            "The synthetic scenario is not real transaction data.",
            "Data drift does not establish model performance drift.",
            "Evidently may use different drift tests and thresholds.",
        ],
        "results": {
            "chronological_train_vs_test": real_results,
            "synthetic_extreme_shift": simulated_results,
        },
    }

    json_path = output_dir / "drift_summary.json"

    with json_path.open("x", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, ensure_ascii=False)

    print("\n=== MONITORING COMPLETED ===")
    print(f"JSON summary: {json_path}")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    main()
