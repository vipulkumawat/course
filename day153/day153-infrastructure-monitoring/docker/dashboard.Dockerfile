FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir flask==3.0.3 requests==2.31.0

COPY src/web/ ./src/web/

EXPOSE 5000

CMD ["python", "src/web/dashboard.py"]
