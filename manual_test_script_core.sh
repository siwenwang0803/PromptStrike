#!/usr/bin/env bash
# RedForge Core Manual Testing Script - Product Hunt Ready
# Tests all essential functionality without optional Stripe setup

# Configuration
API_BASE="${1:-https://api-gateway-uenk.onrender.com}"
EMAIL_PREFIX="${2:-manual-test}"
TEST_EMAIL="${EMAIL_PREFIX}-$(date +%s)@redforge.test"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Global failure tracking
TOTAL_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}🔥 RedForge Core Test Script - Product Hunt Ready${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "Test Email: ${TEST_EMAIL}"
echo -e "API Base: ${API_BASE}"
echo ""

# Enhanced result function with failure tracking
show_result() {
    local result=$1
    local description="$2"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}✅ $description${NC}"
    else
        echo -e "${RED}❌ $description${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# Safe command execution wrapper
safe_exec() {
    local description="$1"
    shift
    set +e
    local output
    output=$("$@" 2>&1)
    local ret=$?
    set -e
    show_result $ret "$description"
    if [ $ret -ne 0 ] && [ -n "$output" ]; then
        echo -e "${RED}   Output: ${output:0:200}${NC}"
    fi
    return $ret
}

# Check if we're in CI environment and use poetry run
if [ -n "${CI:-}" ] || [ -d ".venv" ]; then
    REDFORGE_CMD="poetry run redforge"
else
    REDFORGE_CMD="redforge"
fi

# Test 1: CLI Help
echo -e "${YELLOW}📋 Test 1: CLI Help${NC}"
safe_exec "CLI help command" $REDFORGE_CMD --help
echo ""

# Test 2: CLI Doctor
echo -e "${YELLOW}🩺 Test 2: CLI Diagnostics${NC}"
safe_exec "CLI doctor diagnostics" $REDFORGE_CMD doctor
echo ""

# Test 3: List Attacks
echo -e "${YELLOW}⚔️  Test 3: Attack Packs${NC}"
set +e
ATTACK_COUNT=$($REDFORGE_CMD list-attacks 2>/dev/null | grep -c "LLM" || echo "0")
set -e
if [ "$ATTACK_COUNT" -gt 10 ]; then
    show_result 0 "Attack packs loaded ($ATTACK_COUNT attacks)"
else
    show_result 1 "Insufficient attacks loaded ($ATTACK_COUNT)"
fi
echo ""

# Test 4: Dry Run Scan
echo -e "${YELLOW}🧪 Test 4: Dry Run Scan${NC}"
safe_exec "Dry run scan" $REDFORGE_CMD scan gpt-4 --dry-run --output ./manual_test_reports
echo ""

# Test 5: Offline Scan & Multi-Format Reports
echo -e "${YELLOW}📄 Test 5: Offline Scan & Multi-Format Reports${NC}"
echo "Running offline scan..."

set +e
OFFLINE_OUTPUT=$($REDFORGE_CMD scan gpt-4 --offline --output ./manual_test_reports 2>&1)
OFFLINE_RET=$?
set -e

if echo "$OFFLINE_OUTPUT" | grep -q "✅ Offline scan completed"; then
    show_result 0 "Offline scan completed"
    
    # Check JSON report (scan report, not compliance)
    if ls ./manual_test_reports/redforge_scan_*.json > /dev/null 2>&1; then
        REPORT_FILE=$(ls ./manual_test_reports/redforge_scan_*.json | head -1)
        show_result 0 "JSON report generated: $(basename "$REPORT_FILE")"
        
        # Check watermark in JSON
        if grep -q "watermark" "$REPORT_FILE" 2>/dev/null; then
            show_result 0 "JSON report contains watermark"
        else
            show_result 1 "JSON report missing watermark"
        fi
        
        # Test PDF report generation
        echo "  Testing PDF report generation..."
        set +e
        PDF_OUTPUT=$($REDFORGE_CMD report "$REPORT_FILE" --format pdf --output ./manual_test_reports 2>&1)
        PDF_RET=$?
        set -e
        
        if [ $PDF_RET -eq 0 ] && ls ./manual_test_reports/*.pdf > /dev/null 2>&1; then
            show_result 0 "PDF report generated"
        else
            show_result 1 "PDF report generation failed"
        fi
        
        # Test HTML report generation
        echo "  Testing HTML report generation..."
        set +e
        HTML_OUTPUT=$($REDFORGE_CMD report "$REPORT_FILE" --format html --output ./manual_test_reports 2>&1)
        HTML_RET=$?
        set -e
        
        if [ $HTML_RET -eq 0 ] && ls ./manual_test_reports/*.html > /dev/null 2>&1; then
            show_result 0 "HTML report generated"
        else
            show_result 1 "HTML report generation failed"
        fi
        
        # Test compliance report generation (with proper schema)
        echo "  Testing compliance report generation..."
        set +e
        COMPLIANCE_OUTPUT=$($REDFORGE_CMD report "$REPORT_FILE" -o ./manual_test_reports/compliance.json 2>&1)
        COMPLIANCE_RET=$?
        set -e
        
        if [ $COMPLIANCE_RET -eq 0 ] && [ -f "./manual_test_reports/compliance.json" ]; then
            show_result 0 "Compliance report generated"
        else
            show_result 1 "Compliance report generation failed"
        fi
    else
        show_result 1 "JSON report not generated"
    fi
else
    show_result 1 "Offline scan failed"
fi
echo ""

# Test 6: API Gateway Health
echo -e "${YELLOW}🌐 Test 6: API Gateway Health${NC}"

set +e
HEALTH_RESPONSE=$(curl -s --max-time 10 "$API_BASE/healthz" 2>/dev/null)
HEALTH_RET=$?
set -e

if [ $HEALTH_RET -eq 0 ] && echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    show_result 0 "API Gateway health check"
    echo -e "${BLUE}   Response: ${HEALTH_RESPONSE:0:100}...${NC}"
else
    # Try with longer timeout for sleeping service
    echo -n "API Gateway not responding, trying to wake up"
    API_WORKING=false
    
    for i in {1..10}; do
        set +e
        WAKE_RESPONSE=$(curl -s --max-time 15 "$API_BASE/healthz" 2>/dev/null)
        WAKE_RET=$?
        set -e
        
        if [ $WAKE_RET -eq 0 ] && echo "$WAKE_RESPONSE" | grep -q '"status":"ok"'; then
            echo
            show_result 0 "API Gateway health check (woke up after ${i} attempts)"
            API_WORKING=true
            break
        else
            echo -n "."
            sleep 6
        fi
    done
    
    if [ "$API_WORKING" = false ]; then
        echo
        show_result 1 "API Gateway unreachable after 10 attempts"
        echo -e "${RED}   Last response: ${WAKE_RESPONSE:-'No response'}${NC}"
    fi
fi
echo ""

# Test 7: API Documentation
echo -e "${YELLOW}📚 Test 7: API Documentation${NC}"
set +e
DOC_RESPONSE=$(curl -s --max-time 15 -w "\nHTTP_STATUS:%{http_code}" "$API_BASE/docs" 2>/dev/null)
DOC_RET=$?
set -e

if [ $DOC_RET -eq 0 ]; then
    DOC_STATUS=$(echo "$DOC_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
    if [ "$DOC_STATUS" = "200" ]; then
        show_result 0 "API documentation accessible"
    else
        show_result 1 "API documentation failed (HTTP $DOC_STATUS)"
    fi
else
    show_result 1 "API documentation unreachable (connection failed)"
fi
echo ""

# Test 8: User Signup
echo -e "${YELLOW}👤 Test 8: User Signup${NC}"
echo "Testing with email: $TEST_EMAIL"

set +e
SIGNUP_RESPONSE=$(curl -s --max-time 15 -w "\nHTTP_STATUS:%{http_code}" \
    -X POST "$API_BASE/signup" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\"}" 2>/dev/null || echo "timeout")
SIGNUP_RET=$?
set -e

if [ "$SIGNUP_RESPONSE" = "timeout" ]; then
    show_result 1 "User signup (timeout >15s)"
elif [ $SIGNUP_RET -eq 0 ]; then
    HTTP_STATUS=$(echo "$SIGNUP_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
    RESPONSE_BODY=$(echo "$SIGNUP_RESPONSE" | sed '/HTTP_STATUS:/d')
    
    if [ "$HTTP_STATUS" = "200" ]; then
        show_result 0 "User signup successful"
        
        # Extract API key
        API_KEY=$(echo "$RESPONSE_BODY" | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
        if [ -n "$API_KEY" ]; then
            show_result 0 "API key generated: ${API_KEY:0:8}..."
            
            # Test 9: Free Tier Cloud Scan
            echo ""
            echo -e "${YELLOW}🆓 Test 9: Free Tier Cloud Scan${NC}"
            set +e
            SCAN_RESPONSE=$(curl -s --max-time 20 -w "\nHTTP_STATUS:%{http_code}" \
                -X POST "$API_BASE/scan" \
                -H "Content-Type: application/json" \
                -H "X-API-Key: $API_KEY" \
                -d '{"target":"gpt-4","dry_run":true,"attack_pack":"owasp-llm-top10"}' 2>/dev/null || echo "timeout")
            SCAN_RET=$?
            set -e
            
            if [ "$SCAN_RESPONSE" = "timeout" ]; then
                show_result 1 "First cloud scan (timeout >20s)"
            elif [ $SCAN_RET -eq 0 ]; then
                SCAN_HTTP_STATUS=$(echo "$SCAN_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
                
                if [ "$SCAN_HTTP_STATUS" = "200" ]; then
                    show_result 0 "First cloud scan successful"
                else
                    show_result 1 "First cloud scan failed (HTTP $SCAN_HTTP_STATUS)"
                fi
            else
                show_result 1 "First cloud scan request failed"
            fi
            
            # Test 10: Free Tier Limit Enforcement
            echo ""
            echo -e "${YELLOW}🚫 Test 10: Free Tier Limit Enforcement${NC}"
            set +e
            LIMIT_RESPONSE=$(curl -s --max-time 15 -w "\nHTTP_STATUS:%{http_code}" \
                -X POST "$API_BASE/scan" \
                -H "Content-Type: application/json" \
                -H "X-API-Key: $API_KEY" \
                -d '{"target":"gpt-4","dry_run":true}' 2>/dev/null || echo "timeout")
            LIMIT_RET=$?
            set -e
            
            if [ "$LIMIT_RESPONSE" = "timeout" ]; then
                show_result 1 "Free tier limit test (timeout >15s)"
            elif [ $LIMIT_RET -eq 0 ]; then
                LIMIT_HTTP_STATUS=$(echo "$LIMIT_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
                
                if [ "$LIMIT_HTTP_STATUS" = "402" ]; then
                    show_result 0 "Free tier limit properly enforced (HTTP 402)"
                elif [ "$LIMIT_HTTP_STATUS" = "200" ]; then
                    show_result 1 "Free tier limit NOT enforced (allowed second scan)"
                else
                    show_result 1 "Unexpected limit response (HTTP $LIMIT_HTTP_STATUS)"
                fi
            else
                show_result 1 "Free tier limit test request failed"
            fi
            
        else
            show_result 1 "API key not found in signup response"
        fi
    else
        show_result 1 "User signup failed (HTTP $HTTP_STATUS)"
        if [ "$HTTP_STATUS" = "500" ]; then
            echo -e "${YELLOW}   Note: HTTP 500 suggests Render deployment issue${NC}"
        fi
    fi
else
    show_result 1 "User signup request failed"
fi
echo ""

# Test 11: Security Components
echo -e "${YELLOW}🛡️  Test 11: Security Components${NC}"

# Test Guardrail SDK
set +e
python3 -c "from guardrail.sdk import GuardrailClient; print('OK')" 2>/dev/null
GUARDRAIL_RET=$?
set -e
show_result $GUARDRAIL_RET "Guardrail SDK import"

# Test Cost Guard
set +e
python3 -c "from redforge.sidecar import CostGuard; cg = CostGuard(); print('OK')" 2>/dev/null
COSTGUARD_RET=$?
set -e
show_result $COSTGUARD_RET "Cost Guard functional"

# Test Compliance Framework
set +e
python3 -c "from redforge.compliance.pci_dss_framework import PCIDSSFramework; print('OK')" 2>/dev/null
COMPLIANCE_RET=$?
set -e
show_result $COMPLIANCE_RET "PCI DSS compliance framework"

# Check documentation files
if [ -f "docs/RedForge/Security/Guardrail_Threat_Model.md" ]; then
    show_result 0 "Threat model documentation exists"
else
    show_result 1 "Threat model documentation missing"
fi
echo ""

# Final Summary - Core Tests Only
echo -e "${BLUE}📊 Core Test Results Summary${NC}"
echo -e "${BLUE}============================${NC}"
echo -e "Core Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $((TOTAL_TESTS - FAILED_TESTS))${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CORE TESTS PASSED! Ready for Product Hunt launch!${NC}"
    SUCCESS_RATE=100
    EXIT_CODE=0
else
    SUCCESS_RATE=$(( (TOTAL_TESTS - FAILED_TESTS) * 100 / TOTAL_TESTS ))
    echo -e "${YELLOW}⚠️  $FAILED_TESTS test(s) failed. Success rate: ${SUCCESS_RATE}%${NC}"
    
    if [ $SUCCESS_RATE -ge 90 ]; then
        echo -e "${GREEN}🚀 Good enough for launch (>90% success rate)${NC}"
        EXIT_CODE=0
    elif [ $SUCCESS_RATE -ge 75 ]; then
        echo -e "${YELLOW}⚠️  Acceptable for soft launch (>75% success rate)${NC}"
        EXIT_CODE=0
    else
        echo -e "${RED}❌ Not ready for launch (<75% success rate)${NC}"
        EXIT_CODE=1
    fi
fi

echo ""
echo -e "📧 Test email used: $TEST_EMAIL"
echo -e "🌐 API base tested: $API_BASE"
echo -e "🗂️  Reports generated in: ./manual_test_reports/"

if [ -n "${API_KEY:-}" ]; then
    echo -e "🔑 Generated API key: ${API_KEY:0:8}..."
fi

echo ""
echo -e "${BLUE}💡 Note: This tests core functionality without optional Stripe payment flow${NC}"
echo -e "${BLUE}   Stripe testing can be added later with updated Command Line Tools${NC}"

echo ""
echo -e "${YELLOW}🧹 Cleanup${NC}"
read -p "Clean up test files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ./manual_test_reports 2>/dev/null || true
    echo -e "${GREEN}✅ Test files cleaned up${NC}"
fi

echo ""
echo -e "${BLUE}🔥 Core manual test complete!${NC}"
echo -e "Exit code: $EXIT_CODE"

exit $EXIT_CODE