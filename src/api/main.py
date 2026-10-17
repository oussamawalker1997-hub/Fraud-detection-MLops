import os
import pandas as pd
import uuid
from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile, File, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List
import mlflow

app = FastAPI(
    title="Fraud Intelligence API",
    description="API d'inférence temps réel et batch pour la détection de fraude.",
    version="1.1.0"
)

# 1. Configuration CORS stricte (Sécurité)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Ports standards React/Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Configuration de l'authentification par clé d'API
API_KEY = os.getenv("API_KEY", "mlops-dev-key-2026")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != API_KEY:
        raise HTTPException(status_code=403, detail="Accès refusé : Clé d'API invalide.")
    return api_key_header

reports_path = "/app/reports" if os.path.exists("/app/reports") else "reports"
if os.path.exists(reports_path):
    app.mount("/reports", StaticFiles(directory=reports_path), name="reports")

model = None
model_uri = "not_set"

if os.getenv("TESTING") == "True":
    model_uri = "test_mode"
else:
    try:
        for root_dir, dirs, files in os.walk("/app"):
            if "MLmodel" in files:
                model_uri = root_dir
                break
        
        if model_uri != "not_set":
            model = mlflow.pyfunc.load_model(model_uri)
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

# 3. Injection de la dépendance get_api_key sur les routes sensibles
@app.post("/predict")
def predict_fraud(transaction: Transaction, api_key: str = Depends(get_api_key)):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé.")
    
    input_data = pd.DataFrame([transaction.model_dump()])
    
    try:
        if hasattr(model, "_model_impl") and hasattr(model._model_impl, "predict_proba"):
            probs = model._model_impl.predict_proba(input_data)
            risk_score = float(probs[0][1])
        elif hasattr(model, "unwrap_python_model"):
            unwrapped = model.unwrap_python_model()
            if hasattr(unwrapped, "predict_proba"):
                probs = unwrapped.predict_proba(input_data)
                risk_score = float(probs[0][1])
            else:
                risk_score = float(unwrapped.predict(input_data)[0])
        else:
            prediction = model.predict(input_data)
            risk_score = float(prediction[0][1] if prediction.ndim > 1 else prediction[0])
            
    except Exception as e:
        prediction = model.predict(input_data)
        risk_score = float(prediction[0])
    
    is_fraud = int(risk_score > 0.5)
    
    return {
        "is_fraud": is_fraud,
        "risk_score": float(risk_score), 
        "risk_level": "CRITICAL" if risk_score > 0.7 else ("WARNING" if risk_score > 0.3 else "SAFE"),
        "message": "Transaction frauduleuse détectée !" if is_fraud == 1 else "Transaction légitime."
    }

def process_batch_in_background(df: pd.DataFrame, required_columns: set, job_id: str):
    try:
        predictions = model.predict(df[list(required_columns)])
        df['is_fraud_prediction'] = predictions.astype(int)
        
        output_path = f"{reports_path}/batch_result_{job_id}.csv"
        df.to_csv(output_path, index=False)
    except Exception as e:
        print(f"[ERROR] Échec du job {job_id}: {str(e)}")

@app.post("/predict/batch")
async def predict_fraud_batch(background_tasks: BackgroundTasks, file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé.")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers CSV sont acceptés.")
        
    try:
        df = pd.read_csv(file.file)
        required_columns = set(Transaction.model_fields.keys())
        
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise HTTPException(status_code=400, detail=f"Colonnes manquantes : {missing}")

        job_id = str(uuid.uuid4())[:8]
        background_tasks.add_task(process_batch_in_background, df, required_columns, job_id)
        
        return {
            "status": "accepted",
            "message": "Le fichier est en cours de traitement en arrière-plan.",
            "job_id": job_id,
            "results_url": f"/reports/batch_result_{job_id}.csv"
        }
        
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Erreur lors de la lecture initiale : {str(e)}")
