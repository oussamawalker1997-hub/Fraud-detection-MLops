import os
import pandas as pd
import xgboost as xgb
import mlflow
import mlflow.xgboost
from sklearn.metrics import classification_report, confusion_matrix, average_precision_score, roc_auc_score

# Configuration de MLflow
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment("fraud_detection_xgboost")

def train_model():
    print("[*] Chargement des véritables données d'entraînement...")
    # Remplacement de la simulation par le véritable dataset
    try:
        train_df = pd.read_csv('data/processed/train.csv')
        val_df = pd.read_csv('data/processed/val.csv')
    except FileNotFoundError:
        print("[ERREUR] Fichiers CSV introuvables dans data/processed/. Assurez-vous d'avoir exécuté le script de préparation des données.")
        return

    X_train, y_train = train_df.drop(columns=['Class']), train_df['Class']
    X_test, y_test = val_df.drop(columns=['Class']), val_df['Class']
    
    scale_pos_weight = sum(y_train == 0) / sum(y_train == 1)

    with mlflow.start_run():
        params = {
            "objective": "binary:logistic",
            "eval_metric": "aucpr",
            "max_depth": 4,
            "learning_rate": 0.1,
            "n_estimators": 150,
            "scale_pos_weight": scale_pos_weight,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42
        }
        
        mlflow.log_params(params)
        print("[*] Entraînement du modèle XGBoost sur données réelles...")
        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        pr_auc = average_precision_score(y_test, y_proba)
        roc_auc = roc_auc_score(y_test, y_proba)
        
        print("\n--- Résultats de l'évaluation ---")
        print(f"PR-AUC : {pr_auc:.4f}")
        print(f"ROC-AUC : {roc_auc:.4f}")
        print("\nMatrice de confusion :")
        print(confusion_matrix(y_test, y_pred))
        
        mlflow.log_metric("pr_auc", pr_auc)
        mlflow.log_metric("roc_auc", roc_auc)
        
        # CORRECTION : La signature est désormais basée sur y_proba (décimales) et non y_pred (entiers)
        signature = mlflow.models.signature.infer_signature(X_train, y_proba)
        mlflow.xgboost.log_model(model, "fraud_model", signature=signature)
        print("\n[SUCCÈS] Modèle probabiliste authentique enregistré dans MLflow.")

if __name__ == "__main__":
    os.makedirs("src/training", exist_ok=True)
    train_model()