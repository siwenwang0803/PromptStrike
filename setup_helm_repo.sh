#!/bin/bash

# PromptStrike Helm Repository Setup for v0.2.0-alpha
set -e

echo "🚀 Setting up PromptStrike Helm Repository v0.2.0-alpha"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command -v helm &> /dev/null; then
    print_error "Helm is not installed. Please install Helm first."
    exit 1
fi

if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

print_status "Prerequisites check passed"

# Clean up any existing packages
print_info "Cleaning up existing packages..."
rm -f *.tgz index.yaml 2>/dev/null || true

# Step 1: Package both charts
print_info "📦 Packaging Helm charts..."

# Package CLI chart
print_info "Packaging promptstrike-cli chart..."
cd helm/promptstrike-cli
helm package . --destination ../../
cd ../../

# Package sidecar chart
print_info "Packaging promptstrike-sidecar chart..."
cd helm/promptstrike-sidecar
helm package . --destination ../../
cd ../../

print_status "Charts packaged successfully"

# Step 2: Create Helm repository index
print_info "📋 Creating Helm repository index..."
helm repo index . --url https://siwenwang0803.github.io/PromptStrike

print_status "Repository index created"

# Step 3: Check if gh-pages branch exists
print_info "🔍 Checking GitHub Pages setup..."

if git show-ref --verify --quiet refs/heads/gh-pages; then
    print_status "gh-pages branch exists"
else
    print_warning "Creating gh-pages branch..."
    git checkout --orphan gh-pages
    git rm -rf .
    echo "# PromptStrike Helm Repository" > README.md
    git add README.md
    git commit -m "Initial gh-pages commit"
    git checkout main
    print_status "gh-pages branch created"
fi

# Step 4: Deploy to gh-pages branch
print_info "🚀 Deploying to GitHub Pages..."

# Save current branch
CURRENT_BRANCH=$(git branch --show-current)

# Switch to gh-pages
git checkout gh-pages

# Copy the packaged charts and index
cp *.tgz . 2>/dev/null || print_warning "No .tgz files to copy"
cp index.yaml . 2>/dev/null || print_warning "No index.yaml to copy"

# Create a simple index.html for the repository
cat > index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>PromptStrike Helm Repository</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .chart { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        .version { color: #666; font-size: 0.9em; }
        code { background: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 PromptStrike Helm Repository</h1>
        <p>Developer-first automated LLM red-team platform</p>
    </div>

    <h2>📦 Available Charts</h2>
    
    <div class="chart">
        <h3>promptstrike-cli</h3>
        <p class="version">Version: 0.2.0 | App Version: 0.2.0-alpha</p>
        <p>PromptStrike CLI for running automated LLM security scans</p>
    </div>

    <div class="chart">
        <h3>promptstrike-sidecar</h3>
        <p class="version">Version: 0.2.0 | App Version: 0.2.0-alpha</p>
        <p>PromptStrike Guardrail Sidecar for runtime security monitoring</p>
    </div>

    <h2>🚀 Quick Start</h2>
    
    <h3>Add Repository</h3>
    <pre><code>helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike
helm repo update</code></pre>

    <h3>Install CLI Chart</h3>
    <pre><code>helm install my-cli promptstrike/promptstrike-cli \
  --set secrets.openaiApiKey="your-api-key"</code></pre>

    <h3>Install Sidecar Chart</h3>
    <pre><code>helm install my-sidecar promptstrike/promptstrike-sidecar \
  --set openai.apiKey="your-api-key"</code></pre>

    <h2>📚 Documentation</h2>
    <p>For detailed documentation, visit our <a href="https://github.com/siwenwang0803/PromptStrike">GitHub repository</a>.</p>
</body>
</html>
EOF

# Add and commit changes
git add . 2>/dev/null || print_warning "Nothing to add"

if git diff --staged --quiet; then
    print_warning "No changes to commit"
else
    git commit -m "Deploy Helm repository v0.2.0-alpha

📦 Charts Updated:
- promptstrike-cli: v0.2.0 (app: 0.2.0-alpha)
- promptstrike-sidecar: v0.2.0 (app: 0.2.0-alpha)

🐳 Docker Images:
- CLI: siwenwang0803/promptstrike:v0.2.0-alpha
- Sidecar: promptstrike/guardrail-sidecar:latest

🎯 Features:
- OWASP LLM Top 10 testing (19 attacks)
- Kubernetes Job scheduler
- Persistent storage for reports
- Security policies and RBAC
- Monitoring with Prometheus

Repository: https://siwenwang0803.github.io/PromptStrike"

    print_status "Changes committed to gh-pages"
fi

# Push to remote
print_info "⬆️ Pushing to GitHub..."
if git push origin gh-pages; then
    print_status "Successfully pushed to GitHub Pages"
else
    print_error "Failed to push to GitHub Pages"
    exit 1
fi

# Switch back to original branch
git checkout "$CURRENT_BRANCH"

# Clean up local files
print_info "🧹 Cleaning up local files..."
rm -f *.tgz index.yaml index.html 2>/dev/null || true

print_status "Cleanup completed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 Helm Repository Setup Complete!${NC}"
echo ""
echo -e "${BLUE}📍 Repository URL:${NC} https://siwenwang0803.github.io/PromptStrike"
echo ""
echo -e "${YELLOW}⏰ Wait 2-3 minutes for GitHub Pages propagation, then test:${NC}"
echo ""
echo -e "${BLUE}# Add repository${NC}"
echo "helm repo add promptstrike https://siwenwang0803.github.io/PromptStrike"
echo "helm repo update"
echo ""
echo -e "${BLUE}# List available charts${NC}"
echo "helm search repo promptstrike"
echo ""
echo -e "${BLUE}# Install CLI chart${NC}"
echo "helm install my-cli promptstrike/promptstrike-cli \\"
echo "  --set secrets.openaiApiKey=\"your-api-key\""
echo ""
echo -e "${BLUE}# Install sidecar chart${NC}"
echo "helm install my-sidecar promptstrike/promptstrike-sidecar \\"
echo "  --set openai.apiKey=\"your-api-key\""
echo ""
echo -e "${GREEN}✅ Ready for v0.2.0-alpha release!${NC}"

exit 0