import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import mlflow

app = FastAPI(
    title="Fraud Detection API",
    description="API d'inférence temps réel pour la détection de fraude.",
    version="1.0.0"
)

model = None
model_uri = "not_set"

if os.getenv("TESTING") == "True":
    model_uri = "test_mode"
    print("[INFO] Mode test actif : chargement ignoré.")
else:
    try:
        # --- LA SOLUTION DÉFINITIVE ---
        # On ignore complètement la base de données (mlflow.db) et get_experiment_by_name.
        # On scanne directement le dossier décompressé pour trouver le dossier contenant 'MLmodel'
        print("Recherche dynamique du modèle dans /app/mlruns...")
        for root_dir, dirs, files in os.walk("/app/mlruns"):
            if "MLmodel" in files:
                model_uri = root_dir
                break
        
        if model_uri != "not_set":
            # On charge directement le chemin physique absolu du modèle !
            model = mlflow.pyfunc.load_model(model_uri)
            print(f"[*] Modèle chargé avec succès depuis : {model_uri}")
        else:
            model_uri = "model_file_not_found"
            print("[ERREUR] Le fichier MLmodel est introuvable dans le dossier /app/mlruns")
    except Exception as e:
        model_uri = f"error_loading: {e}"
        print(f"[ERREUR CRITIQUE] Impossible de charger le modèle : {e}")

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
        # J'ai ajouté l'affichage de l'erreur directement sur la page web pour la voir sans aller dans les logs
        raise HTTPException(status_code=503, detail=f"Modèle non chargé. Raison : {model_uri}")
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
