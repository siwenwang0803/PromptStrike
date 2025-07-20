#!/usr/bin/env bash
# RedForge Manual Testing Script - Quick Verification
# Run this yourself to verify everything works before Product Hunt launch

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TEST_EMAIL="manual-test-$(date +%s)@redforge.test"
API_BASE="https://api-gateway-uenk.onrender.com"

echo -e "${BLUE}🔥 RedForge Manual Test Script${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Test Email: ${TEST_EMAIL}"
echo -e "API Base: ${API_BASE}"
echo ""

# Function to show test results
show_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

# Test 1: CLI Help
echo -e "${YELLOW}📋 Test 1: CLI Help${NC}"
redforge --help > /dev/null 2>&1
show_result $? "CLI help command"
echo ""

# Test 2: CLI Doctor
echo -e "${YELLOW}🩺 Test 2: CLI Diagnostics${NC}"
redforge doctor > /dev/null 2>&1
show_result $? "CLI doctor diagnostics"
echo ""

# Test 3: List Attacks
echo -e "${YELLOW}⚔️  Test 3: Attack Packs${NC}"
ATTACK_COUNT=$(redforge list-attacks 2>/dev/null | grep -c "LLM" || echo "0")
if [ "$ATTACK_COUNT" -gt 10 ]; then
    echo -e "${GREEN}✅ Attack packs loaded ($ATTACK_COUNT attacks)${NC}"
else
    echo -e "${RED}❌ Insufficient attacks loaded ($ATTACK_COUNT)${NC}"
fi
echo ""

# Test 4: Dry Run Scan
echo -e "${YELLOW}🧪 Test 4: Dry Run Scan${NC}"
redforge scan gpt-4 --dry-run --output ./manual_test_reports > /dev/null 2>&1
show_result $? "Dry run scan"
echo ""

# Test 5: Offline Scan (Report Generation)
echo -e "${YELLOW}📄 Test 5: Offline Scan & Report Generation${NC}"
echo "Running offline scan..."
if redforge scan gpt-4 --offline --output ./manual_test_reports 2>&1 | grep -q "✅ Offline scan completed"; then
    echo -e "${GREEN}✅ Offline scan completed${NC}"
    
    # Check if report was created
    if ls ./manual_test_reports/*.json > /dev/null 2>&1; then
        REPORT_FILE=$(ls ./manual_test_reports/*.json | head -1)
        echo -e "${GREEN}✅ Report generated: $(basename "$REPORT_FILE")${NC}"
        
        # Check report content
        if grep -q "watermark" "$REPORT_FILE" 2>/dev/null; then
            echo -e "${GREEN}✅ Report contains expected watermark${NC}"
        else
            echo -e "${YELLOW}⚠️  Report watermark not found${NC}"
        fi
    else
        echo -e "${RED}❌ No report files generated${NC}"
    fi
else
    echo -e "${RED}❌ Offline scan failed${NC}"
fi
echo ""

# Test 6: API Gateway Health
echo -e "${YELLOW}🌐 Test 6: API Gateway Health${NC}"
HEALTH_RESPONSE=$(curl -s "$API_BASE/healthz" 2>/dev/null || echo '{"status":"error"}')
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "error")

if [ "$HEALTH_STATUS" = "ok" ]; then
    echo -e "${GREEN}✅ API Gateway health check${NC}"
    echo -e "${BLUE}   Response: $(echo "$HEALTH_RESPONSE" | head -c 100)...${NC}"
else
    echo -e "${RED}❌ API Gateway health check failed${NC}"
    echo -e "${RED}   Response: $HEALTH_RESPONSE${NC}"
fi
echo ""

# Test 7: API Documentation
echo -e "${YELLOW}📚 Test 7: API Documentation${NC}"
DOC_RESPONSE=$(curl -s -w "%{http_code}" "$API_BASE/docs" 2>/dev/null | tail -1)
if [ "$DOC_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ API documentation accessible${NC}"
else
    echo -e "${RED}❌ API documentation failed (HTTP $DOC_RESPONSE)${NC}"
fi
echo ""

# Test 8: User Signup (Critical for Open-Core)
echo -e "${YELLOW}👤 Test 8: User Signup${NC}"
echo "Testing with email: $TEST_EMAIL"

SIGNUP_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST "$API_BASE/signup" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\"}" 2>/dev/null)

HTTP_STATUS=$(echo "$SIGNUP_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
RESPONSE_BODY=$(echo "$SIGNUP_RESPONSE" | sed '/HTTP_STATUS:/d')

if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ User signup successful${NC}"
    
    # Extract API key if present
    API_KEY=$(echo "$RESPONSE_BODY" | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
    if [ -n "$API_KEY" ]; then
        echo -e "${GREEN}✅ API key generated: ${API_KEY:0:8}...${NC}"
        
        # Test 9: Free Tier Scan
        echo ""
        echo -e "${YELLOW}🆓 Test 9: Free Tier Cloud Scan${NC}"
        SCAN_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
            -X POST "$API_BASE/scan" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: $API_KEY" \
            -d '{"target":"gpt-4","dry_run":true,"attack_pack":"owasp-llm-top10"}' 2>/dev/null)
        
        SCAN_HTTP_STATUS=$(echo "$SCAN_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
        SCAN_BODY=$(echo "$SCAN_RESPONSE" | sed '/HTTP_STATUS:/d')
        
        if [ "$SCAN_HTTP_STATUS" = "200" ]; then
            echo -e "${GREEN}✅ Cloud scan initiated${NC}"
            SCAN_ID=$(echo "$SCAN_BODY" | grep -o '"scan_id":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
            if [ -n "$SCAN_ID" ]; then
                echo -e "${GREEN}✅ Scan ID: $SCAN_ID${NC}"
            fi
        else
            echo -e "${RED}❌ Cloud scan failed (HTTP $SCAN_HTTP_STATUS)${NC}"
            echo -e "${RED}   Response: $SCAN_BODY${NC}"
        fi
        
        # Test 10: Second Scan (Should Hit Free Limit)
        echo ""
        echo -e "${YELLOW}🚫 Test 10: Free Tier Limit${NC}"
        LIMIT_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
            -X POST "$API_BASE/scan" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: $API_KEY" \
            -d '{"target":"gpt-4","dry_run":true}' 2>/dev/null)
        
        LIMIT_HTTP_STATUS=$(echo "$LIMIT_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
        
        if [ "$LIMIT_HTTP_STATUS" = "402" ]; then
            echo -e "${GREEN}✅ Free tier limit enforced (HTTP 402)${NC}"
        elif [ "$LIMIT_HTTP_STATUS" = "200" ]; then
            echo -e "${YELLOW}⚠️  Free tier limit not enforced (allowed second scan)${NC}"
        else
            echo -e "${RED}❌ Unexpected response (HTTP $LIMIT_HTTP_STATUS)${NC}"
        fi
        
    else
        echo -e "${YELLOW}⚠️  API key not found in response${NC}"
    fi
else
    echo -e "${RED}❌ User signup failed (HTTP $HTTP_STATUS)${NC}"
    echo -e "${RED}   Response: $RESPONSE_BODY${NC}"
fi
echo ""

# Test 11: Guardrail Components
echo -e "${YELLOW}🛡️  Test 11: Guardrail Components${NC}"

# Test Guardrail SDK
if python3 -c "from guardrail.sdk import GuardrailClient; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✅ Guardrail SDK import${NC}"
else
    echo -e "${RED}❌ Guardrail SDK import failed${NC}"
fi

# Test Cost Guard
if python3 -c "from redforge.sidecar import CostGuard; cg = CostGuard(); print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✅ Cost Guard functional${NC}"
else
    echo -e "${RED}❌ Cost Guard failed${NC}"
fi

# Test Compliance Framework
if python3 -c "from redforge.compliance.pci_dss_framework import PCIDSSFramework; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✅ PCI DSS compliance framework${NC}"
else
    echo -e "${RED}❌ PCI DSS compliance framework failed${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}===============${NC}"
echo -e "✅ Run complete! Check results above."
echo -e "🗂️  Reports generated in: ./manual_test_reports/"
echo -e "📧 Test email used: $TEST_EMAIL"

if [ -n "$API_KEY" ]; then
    echo -e "🔑 Test API key: ${API_KEY:0:8}..."
fi

echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo -e "1. Check that ALL tests show ✅"
echo -e "2. Verify report files in ./manual_test_reports/"
echo -e "3. If any ❌ failures, investigate and fix"
echo -e "4. Ready for Product Hunt launch when 100% ✅"

# Cleanup option
echo ""
read -p "🗑️  Clean up test files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ./manual_test_reports 2>/dev/null || true
    echo -e "${GREEN}✅ Test files cleaned up${NC}"
fi

echo -e "\n${BLUE}🔥 Manual test complete!${NC}"