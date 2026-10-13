FROM python:3.10-slim

WORKDIR /app

# Installation des utilitaires
RUN apt-get update && apt-get install -y curl unzip ca-certificates && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Séparation des étapes pour identifier le blocage exact
RUN curl -fSL -o mlruns.zip "https://github.com/oussamawalker1997-hub/Fraud-detection-MLops/releases/download/v1.0.0/mlruns.zip"
RUN ls -lh mlruns.zip
RUN unzip -q mlruns.zip -d /app/
RUN rm mlruns.zip

# Copie du code source de l'API
COPY src/api /app/src/api

# Exposition du port
EXPOSE 8000

# Démarrage du serveur
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
