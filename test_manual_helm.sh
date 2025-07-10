#!/bin/bash

# Manual test to create and publish Helm chart
set -e

echo "🔧 Manual Helm Chart Publishing Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if helm is available
if ! command -v helm &> /dev/null; then
    echo "❌ Helm not found. Installing..."
    # On macOS
    brew install helm || echo "Please install Helm manually"
    exit 1
fi

# Package the chart manually
echo "📦 Packaging Helm chart..."
cd helm/redforge-sidecar
helm package . --destination ../../
cd ../../

echo "📋 Generated chart packages:"
ls -la *.tgz 2>/dev/null || echo "No .tgz files found"

echo "✅ Manual packaging complete"

# Test chart installation (dry-run)
echo "🧪 Testing chart installation (dry-run)..."
helm install test-guardrail ./redforge-sidecar-*.tgz \
    --namespace test \
    --set openai.apiKey="test-key" \
    --create-namespace \
    --dry-run

echo "✅ Manual Helm test successful!"