FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./static

# Create data directories
RUN mkdir -p data/{hot,warm,cold,archive}

EXPOSE 8000
CMD ["python", "-m", "src.main"]
