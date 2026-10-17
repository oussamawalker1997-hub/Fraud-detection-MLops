import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import os

def generate_drift_report(reference_csv_path, current_csv_path, output_html_path):
    print(f"[*] Analyse de la dérive entre {reference_csv_path} et {current_csv_path}...")
    
    try:
        ref_data = pd.read_csv(reference_csv_path)
        curr_data = pd.read_csv(current_csv_path)
        
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=ref_data, current_data=curr_data)
        
        os.makedirs(os.path.dirname(output_html_path), exist_ok=True)
        report.save_html(output_html_path)
        print(f"[+] Rapport généré avec succès : {output_html_path}")
    except Exception as e:
        print(f"[ERROR] Impossible de générer le rapport de dérive : {e}")

if __name__ == "__main__":
    # Exécution depuis la racine du projet
    generate_drift_report(
        reference_csv_path="data/processed/train.csv", 
        current_csv_path="data/processed/test.csv", 
        output_html_path="reports/data_drift.html"
    )
