import os
import pandas as pd
import numpy as np
import xgboost as xgb
import mlflow
import mlflow.xgboost
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, average_precision_score, roc_auc_score
from sklearn.datasets import make_classification

# Configuration de MLflow
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("fraud_detection_xgboost")

def load_data():
    print("Génération de données (Profil Mid-Level avec fort Feature Engineering)...")
    X, y = make_classification(
        n_samples=100000, 
        n_features=30, 
        n_informative=15, 
        n_redundant=5, 
        weights=[0.99],   # 99% de transactions normales, 1% de fraudes
        flip_y=0.001,     # Très faible bruit
        class_sep=1.5,    # Simulation de features très discriminantes
        random_state=42
    )
    
    feature_names = [f"feature_{i}" for i in range(1, 31)]
    df_X = pd.DataFrame(X, columns=feature_names)
    df_y = pd.Series(y, name="is_fraud")
    
    return df_X, df_y

def train_model():
    X, y = load_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scale_pos_weight = sum(y_train == 0) / sum(y_train == 1)

    with mlflow.start_run():
        # Hyperparamètres optimisés (Régularisation pour contrer le surapprentissage)
        params = {
            "objective": "binary:logistic",
            "eval_metric": "aucpr",
            "max_depth": 4,               # Réduit pour éviter d'apprendre le bruit
            "learning_rate": 0.1,
            "n_estimators": 150,
            "scale_pos_weight": scale_pos_weight,
            "subsample": 0.8,             # Échantillonnage des données (Robustesse)
            "colsample_bytree": 0.8,      # Échantillonnage des features (Robustesse)
            "random_state": 42
        }
        
        mlflow.log_params(params)
        print("Entraînement du modèle XGBoost optimisé en cours...")
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        pr_auc = average_precision_score(y_test, y_proba)
        roc_auc = roc_auc_score(y_test, y_proba)
        
        print("\n--- Résultats de l'évaluation ---")
        print(f"PR-AUC (Precision-Recall Area Under Curve) : {pr_auc:.4f}")
        print(f"ROC-AUC : {roc_auc:.4f}")
        print("\nMatrice de confusion :")
        print(confusion_matrix(y_test, y_pred))
        print("\nRapport de classification :")
        print(classification_report(y_test, y_pred))
        
        mlflow.log_metric("pr_auc", pr_auc)
        mlflow.log_metric("roc_auc", roc_auc)
        
        signature = mlflow.models.signature.infer_signature(X_train, y_pred)
        mlflow.xgboost.log_model(model, "fraud_model", signature=signature)

if __name__ == "__main__":
    os.makedirs("src/training", exist_ok=True)
    train_model()
