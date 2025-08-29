FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY tests/ ./tests/

# Copy and build React app
COPY web/ ./web/
WORKDIR /app/web
RUN npm install && npm run build

WORKDIR /app

EXPOSE 8000

CMD ["python", "-m", "src.main"]
