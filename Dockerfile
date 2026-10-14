FROM python:3.10-slim

WORKDIR /app

# Plus besoin de unzip, nous utiliserons Python
RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Téléchargement et extraction cross-platform avec Python
RUN curl -fSL -o mlruns.zip "https://github.com/oussamawalker1997-hub/Fraud-detection-MLops/releases/download/v1.0.0/mlruns.zip" && \
    python -m zipfile -e mlruns.zip /app/ && \
    rm mlruns.zip

# Copie du code source de l'API
COPY src/api /app/src/api

# Exposition du port
EXPOSE 8080

# Démarrage du serveur
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
