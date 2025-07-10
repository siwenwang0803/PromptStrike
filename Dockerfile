# Multi-stage build for PromptStrike CLI
FROM python:3.11-slim AS builder

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

# Set work directory
WORKDIR /app

# Create virtual environment
RUN python -m venv .venv

# Copy requirements and source code
COPY . .

# Install package and dependencies using pip
RUN .venv/bin/pip install --upgrade pip && \
    .venv/bin/pip install .

# Production stage
FROM python:3.11-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 promptstrike \
    && useradd --uid 1000 --gid promptstrike --shell /bin/bash --create-home promptstrike

# Set work directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=promptstrike:promptstrike /app/.venv /app/.venv

# Copy application code
COPY --chown=promptstrike:promptstrike . .

# Create directories for output (before switching to non-root user)
RUN mkdir -p /app/reports /app/data && \
    chown -R promptstrike:promptstrike /app/reports /app/data

# Switch to non-root user
USER promptstrike

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import promptstrike; print('OK')" || exit 1

# Set entrypoint
ENTRYPOINT ["python", "-m", "promptstrike.cli"]
CMD ["--help"]

# Labels for metadata
LABEL org.opencontainers.image.title="PromptStrike CLI" \
      org.opencontainers.image.description="Developer-first automated LLM red-team platform" \
      org.opencontainers.image.vendor="PromptStrike" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/siwenwang0803/PromptStrike"