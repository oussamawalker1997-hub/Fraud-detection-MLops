FROM python:3.10-slim

WORKDIR /app

# Installer les dépendances système nécessaires (curl pour télécharger le modèle)
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Copier et installer les exigences Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Télécharger et décompresser le modèle MLflow depuis les releases GitHub
RUN curl -fSL -o mlruns.zip "https://github.com/oussamawalker1997-hub/Fraud-detection-MLops/releases/download/v1.0.0/mlruns.zip" && \
    unzip mlruns.zip -d . && \
    rm mlruns.zip

# Copier le code source de l'API
COPY src /app/src

# Exposer le port et lancer l'application avec Uvicorn sur le port 8080 (requis pour Cloud Run)
EXPOSE 8080
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
