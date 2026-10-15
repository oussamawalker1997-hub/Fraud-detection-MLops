import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow

# Définir explicitement le chemin de suivi MLflow
mlflow.set_tracking_uri("file:///app/mlruns")

app = FastAPI(
    title="Fraud Detection API",
    description="API d'inférence temps réel pour la détection de fraude.",
    version="1.0.0"
)

# Chargement conditionnel (ignoré en mode test unitaire)
if os.getenv("TESTING") == "True":
    model = None
    model_uri = "test_mode"
    print("[INFO] Mode test actif : chargement MLflow ignoré.")
else:
    try:
        experiment = mlflow.get_experiment_by_name("Fraud_Detection_XGBoost")
        if experiment:
            runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
            if not runs.empty:
                best_run_id = runs.loc[runs['metrics.pr_auc'].idxmax()]['run_id']
                model_uri = f"runs:/{best_run_id}/xgboost-model"
                model = mlflow.pyfunc.load_model(model_uri)
                print(f"[*] Modèle chargé avec succès depuis le run : {best_run_id}")
            else:
                model = None
                model_uri = "no_runs_found"
        else:
            model = None
            model_uri = "experiment_not_found"
    except Exception as e:
        model = None
        model_uri = "error_loading"
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
    if model is None and os.getenv("TESTING") != "True":
        raise HTTPException(status_code=503, detail="Modèle non chargé. Vérifiez MLflow.")
    return {"status": "healthy", "model_uri": model_uri}

@app.post("/predict")
def predict_fraud(transaction: Transaction):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé.")
    
    input_data = pd.DataFrame([transaction.model_dump()])
    prediction = model.predict(input_data)
    is_fraud = int(prediction[0])
    
    return {
        "is_fraud": is_fraud,
        "message": "Transaction frauduleuse détectée !" if is_fraud == 1 else "Transaction légitime."
    }
