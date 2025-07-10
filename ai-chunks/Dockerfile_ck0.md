<!-- source: Dockerfile idx:0 lines:78 -->

```text
# Multi-stage build for RedForge CLI
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set work directory
WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python:3.11-slim as production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 redforge \
    && useradd --uid 1000 --gid redforge --shell /bin/bash --create-home redforge

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=redforge:redforge /app/.venv /app/.venv

# Copy application code
COPY --chown=redforge:redforge . .

# Switch to non-root user
USER redforge

# Create directories for output
RUN mkdir -p /app/reports /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import redforge; print('OK')" || exit 1

# Set entrypoint
ENTRYPOINT ["python", "-m", "redforge.cli"]
CMD ["--help"]

# Labels for metadata
LABEL org.opencontainers.image.title="RedForge CLI" \
      org.opencontainers.image.description="Developer-first automated LLM red-team platform" \
      org.opencontainers.image.vendor="RedForge" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/siwenwang0803/RedForge"
```