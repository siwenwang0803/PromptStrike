#!/usr/bin/env bash
# RedForge Paid Tier Upgrade Testing Script
# Tests the complete payment → upgrade → API key flow

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_BASE="${API_BASE:-https://redforge.onrender.com}"
TEST_EMAIL="${TEST_EMAIL:-test-$(date +%s)@redforge.test}"
STRIPE_PAYMENT_LINK="${STRIPE_PAYMENT_LINK:-}" # User needs to provide this

echo -e "${BLUE}🧪 RedForge Paid Tier Upgrade Test${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to show test results
show_result() {
    local result=$1
    local description="$2"
    
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}✅ $description${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ $description${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Function to wait for user input
wait_for_payment() {
    echo -e "${YELLOW}👤 Manual Action Required:${NC}"
    echo "1. Open the payment link in your browser"
    echo "2. Complete the payment with test card: 4242 4242 4242 4242"
    echo "3. Use any future expiry date and any CVC"
    echo "4. Apply promo code 'PH50' if testing Product Hunt discount"
    echo ""
    read -p "Press Enter after completing payment..."
}

# Function to check email for API key
check_email() {
    echo -e "${YELLOW}📧 Check your email for:${NC}"
    echo "- Subject: 🔥 Welcome to RedForge Starter Plan - Your API Key Inside!"
    echo "- From: dev@solvas.ai"
    echo ""
    read -p "Enter the API key from the email (or 'skip' to skip): " API_KEY
    
    if [ "$API_KEY" != "skip" ] && [ -n "$API_KEY" ]; then
        echo -e "${GREEN}✅ API Key received: ${API_KEY:0:12}...${NC}"
        return 0
    else
        echo -e "${RED}❌ No API key provided${NC}"
        return 1
    fi
}

# Test 1: Health Check
echo -e "${BLUE}Test 1: API Gateway Health Check${NC}"
echo "----------------------------------------"

HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_BASE/healthz" 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    DATABASE_STATUS=$(echo "$RESPONSE_BODY" | grep -o '"database":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    if [ "$DATABASE_STATUS" = "connected" ]; then
        show_result 0 "API Gateway is healthy and database connected"
    else
        show_result 1 "API Gateway is up but database not connected"
    fi
else
    show_result 1 "API Gateway health check failed (HTTP $HTTP_CODE)"
    echo -e "${RED}Cannot proceed with tests. Check your API Gateway deployment.${NC}"
    exit 1
fi
echo ""

# Test 2: Webhook Endpoint Check
echo -e "${BLUE}Test 2: Stripe Webhook Endpoint${NC}"
echo "----------------------------------------"

WEBHOOK_TEST=$(curl -s -X POST -w "\n%{http_code}" \
    "$API_BASE/stripe/webhook" \
    -H "Content-Type: application/json" \
    -d '{"test": true}' 2>/dev/null || echo "000")
    
WEBHOOK_CODE=$(echo "$WEBHOOK_TEST" | tail -1)

if [ "$WEBHOOK_CODE" = "400" ]; then
    show_result 0 "Webhook endpoint is active (returns 400 for missing signature)"
elif [ "$WEBHOOK_CODE" = "200" ]; then
    show_result 0 "Webhook endpoint is active"
else
    show_result 1 "Webhook endpoint issue (HTTP $WEBHOOK_CODE)"
fi
echo ""

# Test 3: Payment Link Validation
echo -e "${BLUE}Test 3: Payment Link Configuration${NC}"
echo "----------------------------------------"

if [ -z "$STRIPE_PAYMENT_LINK" ]; then
    echo -e "${YELLOW}⚠️  No payment link provided${NC}"
    echo "Set STRIPE_PAYMENT_LINK environment variable or enter it now:"
    read -p "Stripe payment link URL: " STRIPE_PAYMENT_LINK
fi

if [[ "$STRIPE_PAYMENT_LINK" =~ ^https://buy.stripe.com/ ]]; then
    show_result 0 "Valid Stripe payment link format"
    echo -e "${BLUE}Payment link: $STRIPE_PAYMENT_LINK${NC}"
else
    show_result 1 "Invalid payment link format"
    echo -e "${RED}Payment link should start with https://buy.stripe.com/${NC}"
    exit 1
fi
echo ""

# Test 4: Complete Payment Flow
echo -e "${BLUE}Test 4: Complete Payment → Upgrade Flow${NC}"
echo "----------------------------------------"
echo -e "Test email: ${YELLOW}$TEST_EMAIL${NC}"
echo ""

# Open payment link
if command -v open >/dev/null 2>&1; then
    open "$STRIPE_PAYMENT_LINK"
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$STRIPE_PAYMENT_LINK"
else
    echo -e "${YELLOW}Please manually open: $STRIPE_PAYMENT_LINK${NC}"
fi

# Wait for payment
wait_for_payment

# Give webhook time to process
echo -e "${YELLOW}⏳ Waiting 10 seconds for webhook processing...${NC}"
sleep 10

# Check for API key email
if check_email; then
    show_result 0 "Payment processed and API key received"
else
    show_result 1 "Payment processed but no API key received"
fi
echo ""

# Test 5: API Key Validation (if provided)
if [ "$API_KEY" != "skip" ] && [ -n "$API_KEY" ]; then
    echo -e "${BLUE}Test 5: API Key Validation${NC}"
    echo "----------------------------------------"
    
    # Test scan with new API key
    SCAN_RESPONSE=$(curl -s -X POST -w "\n%{http_code}" \
        "$API_BASE/scan" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d '{"target": "gpt-4", "dry_run": true}' 2>/dev/null || echo "000")
    
    SCAN_CODE=$(echo "$SCAN_RESPONSE" | tail -1)
    SCAN_BODY=$(echo "$SCAN_RESPONSE" | head -n -1)
    
    if [ "$SCAN_CODE" = "200" ]; then
        SCAN_ID=$(echo "$SCAN_BODY" | grep -o '"scan_id":"[^"]*"' | cut -d'"' -f4 || echo "")
        if [ -n "$SCAN_ID" ]; then
            show_result 0 "API key works - scan initiated (ID: $SCAN_ID)"
        else
            show_result 0 "API key works - scan accepted"
        fi
    elif [ "$SCAN_CODE" = "402" ]; then
        show_result 1 "API key not working - still showing free tier limit"
    else
        show_result 1 "API key validation failed (HTTP $SCAN_CODE)"
    fi
    
    # Test multiple scans (should be unlimited)
    echo -e "${YELLOW}Testing unlimited scans...${NC}"
    SUCCESS_COUNT=0
    for i in {1..3}; do
        MULTI_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
            -X POST "$API_BASE/scan" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: $API_KEY" \
            -d '{"target": "gpt-4", "dry_run": true}' 2>/dev/null || echo "000")
        
        if [ "$MULTI_CODE" = "200" ]; then
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        fi
        sleep 1
    done
    
    if [ $SUCCESS_COUNT -eq 3 ]; then
        show_result 0 "Unlimited scans confirmed (3/3 successful)"
    else
        show_result 1 "Scan limit issue ($SUCCESS_COUNT/3 successful)"
    fi
fi
echo ""

# Test Summary
echo -e "${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}===============${NC}"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Payment → Upgrade flow is working!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Check the logs above.${NC}"
    
    echo -e "${BLUE}Troubleshooting Tips:${NC}"
    echo "1. Check Render logs for webhook processing errors"
    echo "2. Verify Stripe webhook is configured correctly"
    echo "3. Check spam folder for API key email"
    echo "4. Ensure all environment variables are set in Render"
    
    exit 1
fi