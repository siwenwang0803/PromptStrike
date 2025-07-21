# RedForge CLI - Docker deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF generation
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    xvfb \
    fonts-liberation \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy application code
COPY redforge/ ./redforge/
COPY examples/ ./examples/
COPY docs/ ./docs/

# Create directories for reports and config
RUN mkdir -p ./reports ./config

# Expose port (for future API server)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Copy API Gateway code and requirements
COPY api_gateway/ ./api_gateway/
RUN pip install -r api_gateway/requirements.txt

# Set working directory to API Gateway
WORKDIR /app/api_gateway

# Run the API Gateway
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main_simple:app"]