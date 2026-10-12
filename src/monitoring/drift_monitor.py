import pandas as pd
import warnings
warnings.filterwarnings('ignore')
from scipy.stats import ks_2samp

from evidently import Report
try:
    from evidently.metric_preset import DataDriftPreset
except ImportError:
    from evidently.presets import DataDriftPreset

def calculate_drift_statistically(ref_df, current_df):
    """Méthode MLOps robuste : test KS indépendant pour déclencher l'alerte."""
    drifted_columns = 0
    for col in ref_df.columns:
        # P-value < 0.05 signifie que les distributions sont différentes
        stat, p_value = ks_2samp(ref_df[col], current_df[col])
        if p_value < 0.05:
            drifted_columns += 1
    return (drifted_columns / len(ref_df.columns)) > 0.5

def run_drift_analysis():
    print("[*] Chargement des données...")
    ref_df = pd.read_csv('data/processed/train.csv').sample(n=5000, random_state=42)
    current_df = pd.read_csv('data/processed/test.csv').sample(n=5000, random_state=42)
    
    ref_features = ref_df.drop(columns=['Class'])
    current_features = current_df.drop(columns=['Class'])

    print("\n[*] Scénario 1 : Données normales...")
    # 1. Génération du rapport visuel (Evidently)
    report_normal = Report(metrics=[DataDriftPreset()])
    eval_normal = report_normal.run(reference_data=ref_features, current_data=current_features)
    eval_normal.save_html('reports/drift_normal.html')
    
    # 2. Détection pour l'alerte automatisée (Scipy)
    drift_normal = calculate_drift_statistically(ref_features, current_features)
    print(f"    -> Dérive globale détectée : {drift_normal}")

    print("\n[*] Scénario 2 : Simulation d'une attaque massive...")
    drifted_features = current_features + 10000.0 
    
    # 1. Génération du rapport visuel (Evidently)
    report_drifted = Report(metrics=[DataDriftPreset()])
    eval_drifted = report_drifted.run(reference_data=ref_features, current_data=drifted_features)
    eval_drifted.save_html('reports/drift_alert.html')
    
    # 2. Détection pour l'alerte automatisée (Scipy)
    drift_alert = calculate_drift_statistically(ref_features, drifted_features)
    print(f"    -> Dérive globale détectée : {drift_alert}")

    if drift_alert:
        print("\n[ALERTE MÉTIER] Le système a identifié une dérive anormale via test KS indépendant !")
        print("[SUCCÈS ABSOLU] La brique de monitoring MLOps est validée.")

if __name__ == '__main__':
    run_drift_analysis()
