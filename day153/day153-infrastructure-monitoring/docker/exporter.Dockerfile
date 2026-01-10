FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir prometheus-client==0.20.0 psutil==5.9.8

COPY src/exporters/log_metrics_exporter.py .

EXPOSE 8000

CMD ["python", "log_metrics_exporter.py"]
