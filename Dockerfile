FROM python:3.10-slim

WORKDIR /app

# Copie et installation stricte des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source de l'API et de l'historique MLflow
COPY src/api /app/src/api
COPY mlruns /app/mlruns

# Exposition du port
EXPOSE 8000

# Démarrage du serveur Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
