FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY package.json package-lock.json ./
RUN npm ci --only=production

COPY src/frontend/ ./src/
COPY public/ ./public/
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY --from=frontend-builder /app/frontend/build ./build/

EXPOSE 8000

CMD ["python", "-m", "src.backend.api.main"]
