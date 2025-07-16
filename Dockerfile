# RedForge Webhook Server - Docker deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements-simple.txt .

# Install dependencies
RUN pip install -r requirements-simple.txt

# Copy application code
COPY app.py .

# Create data directory
RUN mkdir -p ./data

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]