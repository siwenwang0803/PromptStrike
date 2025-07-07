#!/bin/bash

# DOD Verification Script for Helm Repository
# Verifies that clients can successfully use the exact DOD command

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🎯 PromptStrike DOD Verification - Helm Repository${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test repository URL
REPO_URL="https://siwenwang0803.github.io/PromptStrike"
CHART_NAME="promptstrike-sidecar"
CHART_VERSION="0.2.0"

echo -e "${BLUE}📝 Testing DOD Command Sequence${NC}"
echo ""

# Step 1: Add Helm repository
echo -e "${YELLOW}Step 1: Adding Helm repository...${NC}"
if helm repo add promptstrike $REPO_URL 2>/dev/null; then
    echo -e "${GREEN}✅ Repository added successfully${NC}"
else
    echo -e "${RED}❌ Failed to add repository${NC}"
    echo "   URL: $REPO_URL"
    echo "   This may be because GitHub Pages needs time to propagate"
    echo "   Expected after GitHub Actions workflow completes"
    exit 1
fi

# Step 2: Update repository index
echo -e "${YELLOW}Step 2: Updating repository index...${NC}"
if helm repo update; then
    echo -e "${GREEN}✅ Repository index updated${NC}"
else
    echo -e "${RED}❌ Failed to update repository index${NC}"
    exit 1
fi

# Step 3: Search for chart
echo -e "${YELLOW}Step 3: Searching for PromptStrike charts...${NC}"
if helm search repo promptstrike --versions; then
    echo -e "${GREEN}✅ Chart found in repository${NC}"
else
    echo -e "${RED}❌ Chart not found in repository${NC}"
    exit 1
fi

# Step 4: Verify specific chart version
echo -e "${YELLOW}Step 4: Verifying chart version $CHART_VERSION...${NC}"
if helm search repo $CHART_NAME --version $CHART_VERSION | grep -q $CHART_VERSION; then
    echo -e "${GREEN}✅ Chart version $CHART_VERSION available${NC}"
else
    echo -e "${RED}❌ Chart version $CHART_VERSION not found${NC}"
    echo "Available versions:"
    helm search repo $CHART_NAME --versions
    exit 1
fi

# Step 5: Test dry-run installation
echo -e "${YELLOW}Step 5: Testing dry-run installation...${NC}"
NAMESPACE="ps-test"
if helm install guardrail promptstrike/$CHART_NAME \
    --namespace $NAMESPACE \
    --set openai.apiKey="test-key" \
    --dry-run --debug >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Dry-run installation successful${NC}"
else
    echo -e "${RED}❌ Dry-run installation failed${NC}"
    echo "Running detailed dry-run for debugging:"
    helm install guardrail promptstrike/$CHART_NAME \
        --namespace $NAMESPACE \
        --set openai.apiKey="test-key" \
        --dry-run --debug
    exit 1
fi

# Step 6: Verify index.yaml accessibility
echo -e "${YELLOW}Step 6: Verifying index.yaml accessibility...${NC}"
if curl -s -f "$REPO_URL/index.yaml" >/dev/null; then
    echo -e "${GREEN}✅ index.yaml accessible at $REPO_URL/index.yaml${NC}"
else
    echo -e "${RED}❌ index.yaml not accessible${NC}"
    echo "   URL: $REPO_URL/index.yaml"
    exit 1
fi

# Step 7: Verify chart package accessibility
echo -e "${YELLOW}Step 7: Verifying chart package accessibility...${NC}"
PACKAGE_URL="$REPO_URL/$CHART_NAME-$CHART_VERSION.tgz"
if curl -s -f "$PACKAGE_URL" >/dev/null; then
    echo -e "${GREEN}✅ Chart package accessible at $PACKAGE_URL${NC}"
else
    echo -e "${YELLOW}⚠️ Chart package not yet accessible (may need time to propagate)${NC}"
    echo "   URL: $PACKAGE_URL"
fi

echo ""
echo -e "${BLUE}📊 DOD VERIFICATION SUMMARY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 DOD COMMAND VERIFIED!${NC}"
echo ""
echo -e "${BLUE}✅ Client Success Command:${NC}"
echo "helm repo add promptstrike $REPO_URL"
echo "helm repo update"
echo "helm install guardrail promptstrike/$CHART_NAME --set openai.apiKey=\$KEY"
echo ""
echo -e "${GREEN}🚀 PromptStrike Helm Repository is DOD-compliant!${NC}"

# Cleanup
helm repo remove promptstrike 2>/dev/null || true

exit 0