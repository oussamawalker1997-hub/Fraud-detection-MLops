import os
os.environ["TESTING"] = "True"

from fastapi.testclient import TestClient
from unittest.mock import patch
from src.api.main import app

client = TestClient(app)

def test_health_check():
    """Vérifie que l'API répond au endpoint racine."""
    response = client.get("/")
    assert response.status_code in [200, 503]

@patch("src.api.main.model")
def test_predict_endpoint_format(mock_model):
    """Vérifie que l'API traite bien les requêtes en simulant le modèle (Mock)."""
    mock_model.predict.return_value = [0]

    payload = {
        "Time": 0.0,
        "V1": 0.0, "V2": 0.0, "V3": 0.0, "V4": 0.0, "V5": 0.0,
        "V6": 0.0, "V7": 0.0, "V8": 0.0, "V9": 0.0, "V10": 0.0,
        "V11": 0.0, "V12": 0.0, "V13": 0.0, "V14": 0.0, "V15": 0.0,
        "V16": 0.0, "V17": 0.0, "V18": 0.0, "V19": 0.0, "V20": 0.0,
        "V21": 0.0, "V22": 0.0, "V23": 0.0, "V24": 0.0, "V25": 0.0,
        "V26": 0.0, "V27": 0.0, "V28": 0.0,
        "Amount": 100.0
    }
    
    # Ajout du header de sécurité pour passer l'authentification
    headers = {"X-API-Key": "mlops-dev-key-2026"}
    
    response = client.post("/predict", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "is_fraud" in data
    assert "message" in data
    assert data["is_fraud"] in [0, 1]
