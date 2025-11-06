FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY web/ ./web/

# Create directories for runtime data
RUN mkdir -p /app/logs /app/checkpoints

EXPOSE 8000

CMD ["python", "-m", "src.multi_project_manager"]
