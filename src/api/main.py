import os
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
<<<<<<< HEAD
from fastapi.staticfiles import StaticFiles
=======
>>>>>>> 25b0d41 (Ajout des autorisations CORS)
from pydantic import BaseModel
from typing import List
import mlflow

app = FastAPI(
    title="Fraud Intelligence API",
    description="API d'inférence temps réel et batch pour la détection de fraude.",
    version="1.1.0"
<<<<<<< HEAD
=======

    app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"], # Ajoute tes ports locaux ici, ou mets ["*"] pour tout accepter
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration CORS pour autoriser le futur Frontend React à communiquer avec l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacer par l'URL exacte du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
>>>>>>> 25b0d41 (Ajout des autorisations CORS)
)

# Configuration CORS pour autoriser le futur Frontend React à communiquer avec l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, remplacer par l'URL exacte du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exposer le dossier des rapports Evidently AI
reports_path = "/app/reports" if os.path.exists("/app/reports") else "reports"
if os.path.exists(reports_path):
    app.mount("/reports", StaticFiles(directory=reports_path), name="reports")
else:
    print(f"[WARNING] Le dossier de rapports {reports_path} n'existe pas.")

model = None
model_uri = "not_set"

# Chargement du modèle (identique et robuste)
if os.getenv("TESTING") == "True":
    model_uri = "test_mode"
    print("[INFO] Mode test actif : chargement ignoré.")
else:
    try:
        for root_dir, dirs, files in os.walk("/app"):
            if "MLmodel" in files:
                model_uri = root_dir
                break
        
        if model_uri != "not_set":
            model = mlflow.pyfunc.load_model(model_uri)
            print(f"[*] Modèle chargé avec succès depuis : {model_uri}")
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

@app.post("/predict")
def predict_fraud(transaction: Transaction):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé.")
    
    input_data = pd.DataFrame([transaction.model_dump()])
    
    # Tentative d'extraction de la probabilité en plus de la classe
    try:
        # Si le modèle est un classifieur standard avec predict_proba
        probabilities = model._model_impl.predict_proba(input_data)
        risk_score = float(probabilities[0][1])
        is_fraud = int(risk_score > 0.5)
    except AttributeError:
        # Fallback si predict_proba n'est pas exposé
        prediction = model.predict(input_data)
        is_fraud = int(prediction[0])
        risk_score = 0.99 if is_fraud == 1 else 0.01
    
    return {
        "is_fraud": is_fraud,
        "risk_score": round(risk_score, 4),
        "risk_level": "CRITICAL" if risk_score > 0.7 else ("WARNING" if risk_score > 0.3 else "SAFE"),
        "message": "Transaction frauduleuse détectée !" if is_fraud == 1 else "Transaction légitime."
    }

@app.post("/predict/batch")
async def predict_fraud_batch(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé.")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers CSV sont acceptés.")
        
    try:
        df = pd.read_csv(file.file)
        
        # Validation basique des colonnes
        required_columns = set(Transaction.model_fields.keys())
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise HTTPException(status_code=400, detail=f"Colonnes manquantes dans le CSV : {missing}")

        # Inférence sur le lot
        predictions = model.predict(df[list(required_columns)])
        df['is_fraud_prediction'] = predictions.astype(int)
        
        # Retourner un résumé et les résultats
        fraud_count = int(df['is_fraud_prediction'].sum())
        total_count = len(df)
        
        return {
            "total_processed": total_count,
            "fraud_detected": fraud_count,
            "fraud_rate": round(fraud_count / total_count, 4) if total_count > 0 else 0,
            "results": df[['Time', 'Amount', 'is_fraud_prediction']].head(100).to_dict(orient="records")
        }
        
    except Exception as e:
<<<<<<< HEAD
         raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du lot : {str(e)}")
=======
         raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du lot : {str(e)}")
>>>>>>> 25b0d41 (Ajout des autorisations CORS)
