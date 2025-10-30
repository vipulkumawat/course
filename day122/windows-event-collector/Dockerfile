FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY logs/ ./logs/
COPY data/ ./data/

# Create necessary directories
RUN mkdir -p logs data/bookmarks data/state data/cache

# Expose port for dashboard
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app/src
ENV WINDOWS_AGENT_LOG_LEVEL=INFO

# Run the application
CMD ["python", "src/main.py"]
