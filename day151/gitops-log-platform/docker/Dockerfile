FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY manifests/ ./manifests/
COPY web/ ./web/

# Expose dashboard port
EXPOSE 8000

CMD ["python", "src/main.py"]
