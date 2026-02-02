FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY logs/ ./logs/

EXPOSE 8765 8000

CMD ["python", "backend/server.py", "logs/sample.log"]
