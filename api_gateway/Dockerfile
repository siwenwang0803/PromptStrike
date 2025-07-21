FROM python:3.11-slim
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy API Gateway code
COPY . /app

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "main_simple:app"]