import pandas as pd
import os
import sys

def validate_raw_data(filepath: str):
    print(f"[*] Vérification du chemin : {filepath}")
    if not os.path.exists(filepath):
        print(f"[ERREUR] Fichier introuvable. As-tu bien placé creditcard.csv dans {filepath} ?")
        sys.exit(1)
        
    print("[*] Chargement des données en mémoire...")
    df = pd.read_csv(filepath)
    
    print(f"[*] Dimensions du dataset : {df.shape[0]} lignes, {df.shape[1]} colonnes")
    if df.shape[1] != 31:
        print("[ALERTE] Le nombre de colonnes attendu est de 31 (Time, V1-V28, Amount, Class).")
        sys.exit(1)
        
    frauds = df['Class'].sum()
    total = len(df)
    imbalance_ratio = (frauds / total) * 100
    print(f"[*] Distribution cible : {frauds} fraudes sur {total} transactions ({imbalance_ratio:.3f}%)")
    
    missing_values = df.isnull().sum().sum()
    if missing_values > 0:
        print(f"[ALERTE] {missing_values} valeurs manquantes détectées.")
    else:
        print("[SUCCÈS] Validation de base réussie : Schéma correct, aucune valeur manquante.")

if __name__ == '__main__':
    validate_raw_data('data/raw/creditcard.csv')
