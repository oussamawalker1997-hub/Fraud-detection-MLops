[![CI/CD Docker Build](https://github.com/oussamawalker1997-hub/fraud-detection-mlops/actions/workflows/main.yml/badge.svg)](https://github.com/oussamawalker1997-hub/fraud-detection-mlops/actions)

This project implements a production-ready Machine Learning API for real-time fraud detection...
# Real-Time Fraud Detection System: End-to-End MLOps Pipeline

## 📌 Project Overview
This project implements a production-ready Machine Learning API for real-time fraud detection. It goes beyond a simple Jupyter Notebook by focusing on **software engineering best practices, MLOps, and CI/CD automation**. 

The architecture is designed to be scalable, reproducible, and completely decoupled, separating the source code from heavy model artifacts.

## 🏗️ Architecture & Technologies

*   **Machine Learning:** XGBoost, Scikit-Learn
*   **API & Serving:** FastAPI, Uvicorn
*   **Experiment Tracking & Model Registry:** MLflow
*   **Data Drift Monitoring:** Evidently AI (HTML reports)
*   **Containerization:** Docker
*   **CI/CD & Automation:** GitHub Actions
*   **Artifact Storage:** GitHub Releases (Acting as a lightweight Model Registry)

## 📊 Model Monitoring & Data Drift
In a production environment, machine learning models degrade over time due to changing data patterns (concept and data drift). This project includes monitoring capabilities using **Evidently AI**:
- **Automated Drift Reports:** Generates comprehensive HTML reports comparing inference traffic against reference baseline datasets.
- **Proactive Maintenance:** Tracks statistical metrics across features (e.g., transaction amounts, temporal shifts) to determine optimal retraining triggers.
- 

## 🚀 Key Engineering Features

1.  **Decoupled Model Architecture:** 
    Heavy binary files (the MLflow registry and XGBoost model weights) are strictly excluded from the Git repository. They are compressed (`mlruns.zip`) and hosted externally via **GitHub Releases**. 
2.  **Dynamic Container Initialization:** 
    The `Dockerfile` is configured to dynamically fetch, download, and extract the model artifact from the remote registry during the build phase. This ensures the Git history remains clean and lightweight.
3.  **Automated CI/CD Pipeline:** 
    A GitHub Actions workflow is triggered on every push to the `main` branch. It spins up a pristine Ubuntu environment, verifies dependencies, and automatically builds the Docker image to ensure the pipeline is never broken by local environment issues (e.g., WSL2/Docker Desktop deadlocks).
4.  **Clean Repository Metrics:** 
    Configured `.gitattributes` to exclude auto-generated monitoring reports (Evidently HTML files) from repository statistics, accurately reflecting the project's Python codebase.

## 📂 Repository Structure
```text
├── .github/workflows/   # CI/CD pipeline definitions (GitHub Actions)
├── src/                 # Application source code
│   └── api/             # FastAPI application and routing
├── requirements.txt     # Strict Python dependencies
├── Dockerfile           # Multi-stage build instructions for the API
├── .dockerignore        # Docker context exclusions
├── .gitignore           # Git tracking exclusions (ignoring heavy artifacts)
└── .gitattributes       # Repository language statistics rules
