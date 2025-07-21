#!/usr/bin/env bash
# Quick fix for the enhanced test script issues

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 Quick Test Fix - Debugging Issues${NC}"
echo ""

# Issue 1: API Gateway Health Check with Timeout
echo -e "${YELLOW}🌐 Testing API Gateway with timeout${NC}"
set +e
HEALTH_RESPONSE=$(timeout 10 curl -s https://api-gateway-uenk.onrender.com/healthz 2>/dev/null || echo "timeout")
HEALTH_RET=$?
set -e

if [ "$HEALTH_RESPONSE" = "timeout" ]; then
    echo -e "${RED}❌ API Gateway timeout (>10s)${NC}"
    echo -e "${YELLOW}   Suggestion: Check Render service status${NC}"
elif echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✅ API Gateway healthy${NC}"
else
    echo -e "${RED}❌ API Gateway unhealthy: $HEALTH_RESPONSE${NC}"
fi
echo ""

# Issue 2: Check Report Command Capabilities
echo -e "${YELLOW}📄 Testing Report Generation Capabilities${NC}"

# Create a dummy scan result for testing
mkdir -p ./test_reports
cat > ./test_reports/dummy_scan.json << 'EOF'
{
  "scan_id": "test_123",
  "target": "gpt-4",
  "results": [],
  "tier": "free",
  "watermark": "Test report"
}
EOF

# Test current report command
echo "Testing redforge report command..."
set +e
REPORT_OUTPUT=$(redforge report ./test_reports/dummy_scan.json -o ./test_reports/compliance_report.json 2>&1)
REPORT_RET=$?
set -e

if [ $REPORT_RET -eq 0 ]; then
    echo -e "${GREEN}✅ Report command works${NC}"
    if [ -f "./test_reports/compliance_report.json" ]; then
        echo -e "${GREEN}✅ Compliance report generated${NC}"
    fi
else
    echo -e "${RED}❌ Report command failed${NC}"
    echo -e "${RED}   Output: $REPORT_OUTPUT${NC}"
fi

# Check what report formats are actually available
echo ""
echo -e "${YELLOW}📋 Available Report Formats:${NC}"
echo "Current CLI only supports compliance reports, not PDF/HTML output formats"
echo "The enhanced test script incorrectly assumes PDF/HTML generation exists"
echo ""

# Issue 3: Check if core CLI scan creates the expected reports
echo -e "${YELLOW}🧪 Testing CLI Report Generation${NC}"
echo "Running offline scan to see what reports are actually created..."

set +e
SCAN_OUTPUT=$(redforge scan gpt-4 --offline --output ./test_reports 2>&1)
SCAN_RET=$?
set -e

if [ $SCAN_RET -eq 0 ]; then
    echo -e "${GREEN}✅ Offline scan completed${NC}"
    
    echo "Files created in ./test_reports/:"
    ls -la ./test_reports/ | grep -v "^total\|^d"
    
    echo ""
    echo "Available file types:"
    ls ./test_reports/*.* 2>/dev/null | sed 's/.*\./  - /' | sort -u
else
    echo -e "${RED}❌ Offline scan failed${NC}"
    echo "$SCAN_OUTPUT"
fi

echo ""
echo -e "${BLUE}🎯 Recommendations:${NC}"
echo "1. Add timeout to API Gateway curl calls (--max-time 10)"
echo "2. Remove PDF/HTML report tests (not implemented in CLI)"
echo "3. Focus on JSON report + compliance report testing"
echo "4. Check Render service status if API Gateway timeouts persist"

# Cleanup
rm -rf ./test_reports

echo ""
echo -e "${GREEN}🔧 Quick diagnosis complete!${NC}"