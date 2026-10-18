FROM python:3.13-slim

WORKDIR /app

# Installer les dépendances système nécessaires (curl pour télécharger le modèle)
RUN apt-get update && apt-get install -y curl ca-certificates unzip && rm -rf /var/lib/apt/lists/*

# Copier et installer les exigences Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'archive locale
COPY mlruns.zip .

# Décompresser en ignorant l'erreur Windows (exit code 1)
RUN unzip mlruns.zip -d . || true

# Nettoyer l'archive
RUN rm mlruns.zip

# AJOUT STRATÉGIQUE : Copier la base de données MLflow dans le conteneur
COPY mlflow.db .

# Copier le code source de l'API
COPY src /app/src

# Exposer le port et lancer l'application avec Uvicorn sur le port 8080 (requis pour Cloud Run)
EXPOSE 8080
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
