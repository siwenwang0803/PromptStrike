<!-- source: docker-compose.yml idx:0 lines:68 -->

```yml
# PromptStrike CLI Development Environment
# Reference: cid-roadmap-v1 Sprint S-1

version: '3.8'

services:
  promptstrike-cli:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: promptstrike-cli
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PYTHONPATH=/app
    volumes:
      - ./reports:/app/reports
      - ./data:/app/data
      - ./config:/app/config
    working_dir: /app
    command: ["--help"]
    
  # Development container with source code mounted
  promptstrike-dev:
    build:
      context: .
      dockerfile: Dockerfile
      target: builder
    container_name: promptstrike-dev
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PYTHONPATH=/app
    volumes:
      - .:/app
      - /app/.venv  # Preserve virtual environment
    working_dir: /app
    command: ["poetry", "shell"]
    tty: true
    stdin_open: true

  # Future: Vector database for attack patterns
  chromadb:
    image: chromadb/chroma:latest
    container_name: promptstrike-vectordb
    ports:
      - "8000:8000"
    volumes:
      - ./data/chroma:/chroma/chroma
    environment:
      - CHROMA_SERVER_HOST=0.0.0.0
      - CHROMA_SERVER_PORT=8000
    profiles:
      - full

  # Future: Metrics and monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: promptstrike-metrics
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
    profiles:
      - monitoring

networks:
  default:
    name: promptstrike-network
```