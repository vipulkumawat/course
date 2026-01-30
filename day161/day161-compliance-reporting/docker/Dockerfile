FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY tests/ ./tests/

# Create data directories
RUN mkdir -p data/logs data/evidence data/reports

EXPOSE 8000

CMD ["python", "src/api/main.py"]
