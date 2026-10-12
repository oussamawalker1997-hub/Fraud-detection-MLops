import pandas as pd
import os
import mlflow
import mlflow.xgboost
from xgboost import XGBClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score

def train():
    print("[*] Chargement des données d'entraînement et de validation...")
    train_df = pd.read_csv('data/processed/train.csv')
    val_df = pd.read_csv('data/processed/val.csv')

    X_train, y_train = train_df.drop(columns=['Class']), train_df['Class']
    X_val, y_val = val_df.drop(columns=['Class']), val_df['Class']

    # Calcul du scale_pos_weight pour gérer le déséquilibre extrême
    scale_pos_weight = (len(y_train) - y_train.sum()) / y_train.sum()

    print("[*] Configuration de MLflow...")
    mlflow.set_experiment("Fraud_Detection_XGBoost")

    with mlflow.start_run():
        params = {
            "max_depth": 5,
            "learning_rate": 0.1,
            "n_estimators": 100,
            "scale_pos_weight": scale_pos_weight,
            "random_state": 42
        }
        mlflow.log_params(params)

        print("[*] Entraînement du modèle XGBoost (cela peut prendre quelques secondes)...")
        model = XGBClassifier(**params)
        model.fit(X_train, y_train)

        print("[*] Évaluation sur le jeu de validation...")
        y_pred = model.predict(X_val)
        y_proba = model.predict_proba(X_val)[:, 1]

        precision = precision_score(y_val, y_pred)
        recall = recall_score(y_val, y_pred)
        f1 = f1_score(y_val, y_pred)
        pr_auc = average_precision_score(y_val, y_proba)

        mlflow.log_metrics({
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "pr_auc": pr_auc
        })

        # Sauvegarde du modèle sous format MLflow
        mlflow.xgboost.log_model(model, "xgboost-model")

        print("\n--- Résultats de Validation ---")
        print(f"Precision : {precision:.4f}")
        print(f"Recall    : {recall:.4f}")
        print(f"F1-Score  : {f1:.4f}")
        print(f"PR-AUC    : {pr_auc:.4f}")
        print("[SUCCÈS] Modèle entraîné et enregistré dans MLflow.")

if __name__ == '__main__':
    train()
