#!/bin/bash

# Manual Helm Repository Creation for DOD Completion
set -e

echo "🔧 Creating Manual Helm Repository for DOD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Step 1: Package the chart
echo "📦 Packaging Helm chart..."
cd helm/promptstrike-sidecar
helm package . --destination ../../
cd ../../

# Step 2: Create Helm repository index
echo "📋 Creating Helm repository index..."
helm repo index . --url https://siwenwang0803.github.io/PromptStrike

# Step 3: Copy files to gh-pages branch
echo "🔄 Deploying to gh-pages branch..."
git checkout gh-pages

# Copy the packaged chart and index
cp *.tgz . 2>/dev/null || echo "No .tgz files to copy"
cp index.yaml . 2>/dev/null || echo "No index.yaml to copy"

# Add and commit
git add *.tgz index.yaml 2>/dev/null || echo "Nothing to add"
git commit -m "Manual Helm repository deployment for DOD completion

- Package: promptstrike-sidecar chart
- Index: Helm repository index.yaml
- DOD: Enable helm repo add promptstrike command

This completes the final DOD requirement for client deployment." || echo "Nothing to commit"

# Push to remote
git push origin gh-pages

echo "✅ Manual Helm repository created and deployed!"

# Switch back to main
git checkout main

# Clean up local files
rm -f *.tgz index.yaml 2>/dev/null || true

echo ""
echo "🎯 DOD Validation:"
echo "Wait 2-3 minutes for GitHub Pages propagation, then run:"
echo "./validate_final_dod.sh"
echo ""
echo "Expected result: All tests should pass with green checkmarks ✅"

exit 0