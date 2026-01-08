FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Terraform
RUN curl -fsSL https://releases.hashicorp.com/terraform/1.7.5/terraform_1.7.5_linux_amd64.zip -o terraform.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/ \
    && rm terraform.zip

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose dashboard port
EXPOSE 5000

# Default command
CMD ["python", "web/app.py"]
