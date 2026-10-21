FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Model artifacts are provided at runtime, not embedded in the Docker image.
# MODEL_PATH and METRICS_PATH define their locations.
RUN mkdir -p /app/models /app/reports/batch

COPY src /app/src

EXPOSE 8080

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]