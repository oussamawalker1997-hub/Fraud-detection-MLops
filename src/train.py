import os
import pandas as pd
import numpy as np
import xgboost as xgb
import mlflow
import mlflow.xgboost
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, 
    confusion_matrix, 
    average_precision_score,
    roc_auc_score
)
from sklearn.datasets import make_classification

# Configuration de MLflow
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("fraud_detection_xgboost")

def load_data():
    """
    Charge les données. Pour la reproductibilité du portfolio, 
    nous générons un dataset synthétique fortement déséquilibré.
    (Remplacez par pd.read_csv('data/transactions.csv') pour un dataset réel).
    """
    print("Génération des données (simulation de fraude)...")
    X, y = make_classification(
        n_samples=100000, 
        n_features=30, 
        n_informative=5, 
        n_redundant=2, 
        weights=[0.995], # 99.5% de transactions normales, 0.5% de fraudes
        flip_y=0.01, 
        random_state=42
    )
    
    feature_names = [f"feature_{i}" for i in range(1, 31)]
    df_X = pd.DataFrame(X, columns=feature_names)
    df_y = pd.Series(y, name="is_fraud")
    
    return df_X, df_y

def train_model():
    # 1. Chargement et séparation des données
    X, y = load_data()
    
    # Stratify=y est crucial pour conserver le ratio de fraude dans le train et le test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Calcul du poids pour gérer le déséquilibre des classes
    # scale_pos_weight = nombre_d_exemples_negatifs / nombre_d_exemples_positifs
    neg_cases = sum(y_train == 0)
    pos_cases = sum(y_train == 1)
    scale_pos_weight = neg_cases / pos_cases

    print(f"Entraînement sur {len(X_train)} échantillons, Test sur {len(X_test)} échantillons.")
    print(f"Ratio de fraude : {y.mean():.4f} - scale_pos_weight calculé : {scale_pos_weight:.2f}")

    # 2. Démarrage du tracking MLflow
    with mlflow.start_run():
        
        # Hyperparamètres
        params = {
            "objective": "binary:logistic",
            "eval_metric": "aucpr", # Precision-Recall AUC (idéal pour la fraude)
            "max_depth": 5,
            "learning_rate": 0.05,
            "n_estimators": 100,
            "scale_pos_weight": scale_pos_weight,
            "random_state": 42
        }
        
        # Logging des paramètres
        mlflow.log_params(params)
        
        # Initialisation et entraînement du modèle
        print("Entraînement du modèle XGBoost en cours...")
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        # 3. Prédictions et Évaluation
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        # Calcul des métriques
        pr_auc = average_precision_score(y_test, y_proba)
        roc_auc = roc_auc_score(y_test, y_proba)
        
        print("\n--- Résultats de l'évaluation ---")
        print(f"PR-AUC (Precision-Recall Area Under Curve) : {pr_auc:.4f}")
        print(f"ROC-AUC : {roc_auc:.4f}")
        print("\nMatrice de confusion :")
        print(confusion_matrix(y_test, y_pred))
        print("\nRapport de classification :")
        print(classification_report(y_test, y_pred))
        
        # Logging des métriques dans MLflow
        mlflow.log_metric("pr_auc", pr_auc)
        mlflow.log_metric("roc_auc", roc_auc)
        
        # Sauvegarde du modèle dans MLflow
        signature = mlflow.models.signature.infer_signature(X_train, y_pred)
        mlflow.xgboost.log_model(model, "fraud_model", signature=signature)
        
        print(f"\nModèle et métriques sauvegardés dans MLflow (Run ID: {mlflow.active_run().info.run_id})")

if __name__ == "__main__":
    # S'assurer que le dossier src/training/ existe
    os.makedirs("src/training", exist_ok=True)
    train_model()
