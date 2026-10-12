import pandas as pd
import os
import sys
from sklearn.model_selection import train_test_split

def prepare_and_split_data(input_filepath: str, output_dir: str):
    print("[*] Démarrage du partitionnement stratifié des données...")
    
    if not os.path.exists(input_filepath):
        print(f"[ERREUR] Impossible de trouver le fichier source : {input_filepath}")
        sys.exit(1)
        
    os.makedirs(output_dir, exist_ok=True)
    
    df = pd.read_csv(input_filepath)
    X = df.drop(columns=['Class'])
    y = df['Class']
    
    # Étape 1 : Séparer le jeu d'entraînement (70%) et un jeu temporaire (30%)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    
    # Étape 2 : Séparer le jeu temporaire en Validation (15%) et Test (15%)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
    )
    
    # Reconstitution des datasets complets pour sauvegarde
    train_df = pd.concat([X_train, y_train], axis=1)
    val_df = pd.concat([X_val, y_val], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)
    
    # Sauvegarde
    print("[*] Sauvegarde des fichiers dans data/processed/ ...")
    train_df.to_csv(os.path.join(output_dir, "train.csv"), index=False)
    val_df.to_csv(os.path.join(output_dir, "val.csv"), index=False)
    test_df.to_csv(os.path.join(output_dir, "test.csv"), index=False)
    
    # Vérifications métier
    print("\n--- Bilan du Split Stratifié ---")
    print(f"Train : {len(train_df)} lignes | Fraudes : {y_train.sum()} ({y_train.mean()*100:.3f}%)")
    print(f"Val   : {len(val_df)} lignes | Fraudes : {y_val.sum()} ({y_val.mean()*100:.3f}%)")
    print(f"Test  : {len(test_df)} lignes | Fraudes : {y_test.sum()} ({y_test.mean()*100:.3f}%)")
    print("[SUCCÈS] Les données sont préparées et isolées.")

if __name__ == '__main__':
    prepare_and_split_data(
        input_filepath='data/raw/creditcard.csv',
        output_dir='data/processed'
    )
