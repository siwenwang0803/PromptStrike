# RedForge CLI - Docker deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

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

# Default command: show help
CMD ["python", "-m", "redforge.cli", "--help"]