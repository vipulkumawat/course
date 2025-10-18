FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend source code
COPY backend/src ./backend/src
COPY backend/config ./backend/config

# Copy frontend build (will be built in docker-compose)
COPY frontend/build ./frontend/build

# Expose port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app/backend/src

# Run the application
CMD ["python", "backend/src/main.py"]
