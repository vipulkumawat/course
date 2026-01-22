FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/

# Expose API port
EXPOSE 8000

# Run API server
CMD ["python", "-m", "src.api.forecast_api"]
