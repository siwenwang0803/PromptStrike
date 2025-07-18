#!/bin/bash
# RedForge API Gateway Deployment Script

set -e

echo "🚀 Deploying RedForge API Gateway..."

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "📦 Running in Docker container"
    DEPLOYMENT_MODE="docker"
else
    echo "🖥️  Running on local system"
    DEPLOYMENT_MODE="local"
fi

# Install dependencies
echo "📥 Installing dependencies..."
if [ "$DEPLOYMENT_MODE" = "docker" ]; then
    pip install -r /app/api_gateway/requirements.txt
else
    cd api_gateway
    pip install -r requirements.txt
fi

# Check environment variables
echo "🔧 Checking environment variables..."
required_vars=(
    "SUPABASE_URL"
    "SUPABASE_SERVICE_KEY"
    "REDFORGE_API_BASE_URL"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    else
        echo "✅ $var is set"
    fi
done

# Run database migrations
echo "🗄️  Running database migrations..."
if [ "$DEPLOYMENT_MODE" = "docker" ]; then
    python /app/scripts/run_migrations.py
else
    python ../scripts/run_migrations.py
fi

# Start the API gateway
echo "🌐 Starting API Gateway..."
if [ "$DEPLOYMENT_MODE" = "docker" ]; then
    cd /app/api_gateway
    exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4
else
    uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --reload
fi