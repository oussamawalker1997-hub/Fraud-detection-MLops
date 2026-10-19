import os
import pandas as pd
import uuid
import numpy as np
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List
import mlflow
import xgboost as xgb
import mlflow.xgboost

app = FastAPI(
    title="Fraud Intelligence API",
    description="API d'inférence temps réel et batch pour la détection de fraude.",
    version="1.1.0"
)

# 1. Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Authentification par clé d'API (OpenAPI Security Scheme)
API_KEY = os.getenv("API_KEY", "mlops-dev-key-2026")
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=True)

def get_api_key(api_key: str = Security(api_key_scheme)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Accès refusé : Clé d'API invalide.")
    return api_key

# Exposer le dossier des rapports
reports_path = "/app/reports" if os.path.exists("/app/reports") else "reports"
os.makedirs(reports_path, exist_ok=True)
if os.path.exists(reports_path):
    app.mount("/reports", StaticFiles(directory=reports_path), name="reports")

model = None
model_uri = "not_set"

# Chargement du modèle XGBoost natif (Probabiliste)
if os.getenv("TESTING") == "True":
    model_uri = "test_mode"
else:
    try:
        for root_dir, dirs, files in os.walk("/app"):
            if "MLmodel" in files:
                model_uri = root_dir
                break
        
        if model_uri != "not_set":
            model = mlflow.xgboost.load_model(model_uri)
        else:
            model_uri = "model_file_not_found"
    except Exception as e:
        model_uri = f"error_loading: {e}"

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
        raise HTTPException(status_code=503, detail=f"Modèle non chargé. Raison : {model_uri}")
    return {"status": "healthy", "model_uri": model_uri, "api_version": "1.1.0"}

def get_probability_score(df: pd.DataFrame) -> np.ndarray:
    """Extraction directe des probabilités continues."""
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(df)
        return probs[:, 1] if len(probs.shape) > 1 else probs
    else:
        dmatrix = xgb.DMatrix(df)
        return model.predict(dmatrix)

# 3. Endpoint Temps Réel
@app.post("/predict")
def predict_fraud(transaction: Transaction, api_key: str = Security(get_api_key)):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé.")
    
    ordered_columns = list(Transaction.model_fields.keys())
    input_data = pd.DataFrame([transaction.model_dump()])[ordered_columns]
    
    try:
        scores = get_probability_score(input_data)
        risk_score = float(scores[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'inférence : {str(e)}")
    
    is_fraud = int(risk_score > 0.5)
    
    explanations = []
    if is_fraud == 1:
        if transaction.Amount > 1000:
            explanations.append(f"Montant inhabituellement élevé ({transaction.Amount}$).")
        if transaction.Time < 5000:
            explanations.append("Transaction effectuée à une heure atypique.")
        if transaction.V1 < -2.0 or transaction.V2 > 2.0:
            explanations.append("Anomalie détectée dans la signature comportementale.")
        if not explanations:
            explanations.append("Déviation forte du modèle comportemental global.")
    else:
        explanations.append("Comportement d'achat aligné avec le profil standard du client.")
    
    return {
        "is_fraud": is_fraud,
        "risk_score": risk_score, 
        "risk_level": "CRITICAL" if risk_score > 0.7 else ("WARNING" if risk_score > 0.3 else "SAFE"),
        "message": "Transaction frauduleuse détectée !" if is_fraud == 1 else "Transaction légitime.",
        "explanations": explanations
    }

def process_batch_in_background(df: pd.DataFrame, ordered_columns: list, job_id: str):
    try:
        risk_scores = get_probability_score(df[ordered_columns])
        df['risk_score'] = risk_scores
        df['is_fraud_prediction'] = (risk_scores > 0.5).astype(int)
        output_path = f"{reports_path}/batch_result_{job_id}.csv"
        df.to_csv(output_path, index=False)
        print(f"[*] Job Batch {job_id} terminé avec succès.")
    except Exception as e:
        print(f"[ERROR] Échec du job {job_id}: {str(e)}")

# 4. Endpoint Batch
@app.post("/predict/batch")
async def predict_fraud_batch(background_tasks: BackgroundTasks, file: UploadFile = File(...), api_key: str = Security(get_api_key)):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé.")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers CSV sont acceptés.")
        
    try:
        df = pd.read_csv(file.file)
        ordered_columns = list(Transaction.model_fields.keys())
        required_columns_set = set(ordered_columns)
        
        if not required_columns_set.issubset(df.columns):
            missing = required_columns_set - set(df.columns)
            raise HTTPException(status_code=400, detail=f"Colonnes manquantes : {missing}")

        job_id = str(uuid.uuid4())[:8]
        background_tasks.add_task(process_batch_in_background, df, ordered_columns, job_id)
        
        return {
            "status": "accepted",
            "message": "Le fichier est en cours de traitement en arrière-plan.",
            "job_id": job_id,
            "results_url": f"/reports/batch_result_{job_id}.csv"
        }
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture initiale : {str(e)}")