import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import os

def generate_drift_report(reference_csv_path, current_csv_path, output_html_path):
    print(f"[*] Analyse de la dérive entre {reference_csv_path} et {current_csv_path}...")
    
    # Chargement des données
    ref_data = pd.read_csv(reference_csv_path)
    curr_data = pd.read_csv(current_csv_path)
    
    # Création du rapport Evidently avec le preset Data Drift
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref_data, current_data=curr_data)
    
    # Sauvegarde dans le dossier monté par FastAPI
    os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
    report.save_html(output_html_path)
    print(f"[+] Rapport généré avec succès : {output_html_path}")

if __name__ == "__main__":
    # Exemple d'exécution (les chemins seront à adapter selon ton volume Docker)
    generate_drift_report(
        reference_csv_path="data/train_reference.csv",
        current_csv_path="data/latest_transactions.csv",
        output_html_path="reports/data_drift.html"
    )
