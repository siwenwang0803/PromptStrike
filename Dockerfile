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

# Create a simple server script and run it
RUN echo 'import http.server; import socketserver; PORT = 8000; Handler = http.server.SimpleHTTPRequestHandler; httpd = socketserver.TCPServer(("", PORT), Handler); print(f"RedForge serving on port {PORT}"); httpd.serve_forever()' > server.py
CMD ["python", "server.py"]