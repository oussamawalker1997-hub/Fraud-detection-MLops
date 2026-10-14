import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow
import os


# Définir explicitement le chemin de suivi MLflow
mlflow.set_tracking_uri("file:///app/mlruns")

# Exemple de chargement (adapte l'URI selon ton modèle exact)
# model = mlflow.pyfunc.load_model("runs:/<run_id>/model")
# Exemple de chargement du modèle
model_uri = "mlruns/..." # Ajustez selon votre structure MLflow
model = mlflow.pyfunc.load_model(model_uri)

app = FastAPI(
    title="Fraud Detection API",
    description="API d'inférence temps réel pour la détection de fraude.",
    version="1.0.0"
)

# Chargement dynamique du modèle au démarrage de l'API
try:
    experiment = mlflow.get_experiment_by_name("Fraud_Detection_XGBoost")
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    best_run_id = runs.loc[runs['metrics.pr_auc'].idxmax()]['run_id']
    model_uri = f"runs:/{best_run_id}/xgboost-model"
    
    # pyfunc charge dynamiquement l'artefact avec une interface standard .predict()
    model = mlflow.pyfunc.load_model(model_uri)
    print(f"[*] Modèle chargé avec succès depuis le run : {best_run_id}")
except Exception as e:
    model = None
    print(f"[ERREUR] Impossible de charger le modèle : {e}")

# Schéma strict des données d'entrée
class Transaction(BaseModel):
    Time: float
    V1: float
    V2: float
    V3: float
    V4: float
    V5: float
    V6: float
    V7: float
    V8: float
    V9: float
    V10: float
    V11: float
    V12: float
    V13: float
    V14: float
    V15: float
    V16: float
    V17: float
    V18: float
    V19: float
    V20: float
    V21: float
    V22: float
    V23: float
    V24: float
    V25: float
    V26: float
    V27: float
    V28: float
    Amount: float

@app.get("/")
def health_check():
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé. Vérifiez MLflow.")
    return {"status": "healthy", "model_uri": model_uri}

@app.post("/predict")
def predict_fraud(transaction: Transaction):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé.")
    
    # Conversion du JSON validé vers DataFrame
    input_data = pd.DataFrame([transaction.model_dump()])
    
    # Prédiction
    prediction = model.predict(input_data)
    is_fraud = int(prediction[0])
    
    return {
        "is_fraud": is_fraud,
        "message": "Transaction frauduleuse détectée !" if is_fraud == 1 else "Transaction légitime."
    }
