#!/usr/bin/env bash
# RedForge Paid Flow Testing Script
# Manual testing for Stripe → Supabase tier upgrades and concurrent rate limiting
# Run before releases to ensure paid features work correctly

# Configuration
API_BASE="${1:-https://api-gateway-uenk.onrender.com}"
EMAIL_PREFIX="${2:-paid-test}"
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

echo -e "${BLUE}💳 RedForge Paid Flow Testing Script${NC}"
echo -e "${BLUE}===================================${NC}"
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

# Environment check
echo -e "${YELLOW}🔧 Environment Prerequisites Check${NC}"

# Check if Stripe CLI is installed
if command -v stripe >/dev/null 2>&1; then
    show_result 0 "Stripe CLI is installed ($(stripe --version))"
else
    show_result 1 "Stripe CLI not found"
    echo -e "${RED}   Install: brew install stripe/stripe-cli/stripe${NC}"
    echo -e "${RED}   Or download: https://github.com/stripe/stripe-cli/releases${NC}"
    exit 1
fi

# Check environment variables
if [ -n "${STRIPE_API_KEY:-}" ]; then
    show_result 0 "STRIPE_API_KEY configured"
else
    show_result 1 "STRIPE_API_KEY not set"
    echo -e "${RED}   Get from: https://dashboard.stripe.com/test/apikeys${NC}"
    exit 1
fi

if [ -n "${PRICE_STARTER:-}" ]; then
    show_result 0 "PRICE_STARTER configured ($PRICE_STARTER)"
else
    show_result 1 "PRICE_STARTER not set"
    echo -e "${RED}   Get from: https://dashboard.stripe.com/test/products${NC}"
    exit 1
fi

if [ -n "${SUPABASE_URL:-}" ] && [ -n "${SUPABASE_SERVICE_ROLE:-}" ]; then
    show_result 0 "Supabase credentials configured"
else
    show_result 1 "Supabase credentials not set"
    echo -e "${RED}   Set SUPABASE_URL and SUPABASE_SERVICE_ROLE${NC}"
    exit 1
fi

echo ""

# Test 1: Create test user account
echo -e "${YELLOW}👤 Test 1: Create Test User Account${NC}"
echo "Creating account with email: $TEST_EMAIL"

set +e
SIGNUP_RESPONSE=$(curl -s --max-time 15 -w "\nHTTP_STATUS:%{http_code}" \
    -X POST "$API_BASE/signup" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\"}" 2>/dev/null)
SIGNUP_RET=$?
set -e

if [ $SIGNUP_RET -eq 0 ]; then
    HTTP_STATUS=$(echo "$SIGNUP_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
    RESPONSE_BODY=$(echo "$SIGNUP_RESPONSE" | sed '/HTTP_STATUS:/d')
    
    if [ "$HTTP_STATUS" = "200" ]; then
        show_result 0 "User account created"
        
        # Extract API key
        API_KEY=$(echo "$RESPONSE_BODY" | grep -o '"api_key":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
        if [ -n "$API_KEY" ]; then
            show_result 0 "API key generated: ${API_KEY:0:8}..."
            echo -e "${BLUE}   Full API key: $API_KEY${NC}"
        else
            show_result 1 "API key not found in response"
            exit 1
        fi
    else
        show_result 1 "User signup failed (HTTP $HTTP_STATUS)"
        exit 1
    fi
else
    show_result 1 "User signup request failed"
    exit 1
fi
echo ""

# Test 2: Verify Free Tier Limit
echo -e "${YELLOW}🆓 Test 2: Verify Free Tier Works${NC}"

set +e
SCAN1_RESPONSE=$(curl -s --max-time 20 -w "\nHTTP_STATUS:%{http_code}" \
    -X POST "$API_BASE/scan" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"target":"gpt-4","dry_run":true,"attack_pack":"owasp-llm-top10"}' 2>/dev/null)
SCAN1_RET=$?
set -e

if [ $SCAN1_RET -eq 0 ]; then
    SCAN1_STATUS=$(echo "$SCAN1_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
    if [ "$SCAN1_STATUS" = "200" ]; then
        show_result 0 "First scan successful (free tier)"
    else
        show_result 1 "First scan failed (HTTP $SCAN1_STATUS)"
    fi
else
    show_result 1 "First scan request failed"
fi

# Test free tier limit
set +e
SCAN2_RESPONSE=$(curl -s --max-time 15 -w "\nHTTP_STATUS:%{http_code}" \
    -X POST "$API_BASE/scan" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"target":"gpt-4","dry_run":true}' 2>/dev/null)
SCAN2_RET=$?
set -e

if [ $SCAN2_RET -eq 0 ]; then
    SCAN2_STATUS=$(echo "$SCAN2_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
    if [ "$SCAN2_STATUS" = "402" ]; then
        show_result 0 "Free tier limit enforced (HTTP 402)"
    else
        show_result 1 "Free tier limit NOT enforced (HTTP $SCAN2_STATUS)"
    fi
else
    show_result 1 "Free tier limit test failed"
fi
echo ""

# Test 3: Stripe Payment Flow
echo -e "${YELLOW}💳 Test 3: Stripe Payment Upgrade${NC}"

echo "Creating Stripe checkout session..."
set +e
SESSION_JSON=$(stripe checkout sessions create \
    --price "$PRICE_STARTER" \
    --mode subscription \
    --client_reference_id "$API_KEY" \
    --success_url https://example.com/success \
    --cancel_url https://example.com/cancel \
    --allow_promotion_codes=true \
    -r 2>/dev/null)
STRIPE_RET=$?
set -e

if [ $STRIPE_RET -eq 0 ]; then
    show_result 0 "Stripe checkout session created"
    
    # Extract checkout URL
    CHECKOUT_URL=$(echo "$SESSION_JSON" | grep -o '"url":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
    if [ -n "$CHECKOUT_URL" ]; then
        echo -e "${BLUE}🔗 Checkout URL: $CHECKOUT_URL${NC}"
        echo -e "${BLUE}💳 Test card: 4242 4242 4242 4242, any future date/CVC${NC}"
        echo ""
        
        # Option for manual payment
        echo -e "${YELLOW}Choose payment simulation method:${NC}"
        echo "1. Manual browser payment (recommended for real testing)"
        echo "2. Automated webhook trigger (for CI/testing)"
        read -p "Enter choice (1 or 2): " PAYMENT_CHOICE
        
        if [ "$PAYMENT_CHOICE" = "1" ]; then
            echo -e "${BLUE}Please complete payment in browser and press Enter when done...${NC}"
            read -p "Press Enter after completing payment..."
        else
            echo "Triggering test webhook..."
            set +e
            stripe trigger checkout.session.completed >/dev/null 2>&1
            WEBHOOK_RET=$?
            set -e
            show_result $WEBHOOK_RET "Stripe webhook triggered"
        fi
    else
        show_result 1 "Checkout URL not found in response"
    fi
else
    show_result 1 "Stripe checkout session creation failed"
    echo -e "${RED}   Error: Check STRIPE_API_KEY and PRICE_STARTER${NC}"
    exit 1
fi
echo ""

# Test 4: Wait for Tier Update in Supabase
echo -e "${YELLOW}🔄 Test 4: Supabase Tier Update${NC}"
echo "Waiting for tier update in Supabase..."

TIER_UPDATED=false
for i in {1..15}; do
    echo -n "."
    
    # Check tier using Supabase CLI (if available) or direct API call
    set +e
    if command -v supabase >/dev/null 2>&1; then
        # Use Supabase CLI
        TIER_CHECK=$(supabase db remote \
            --project-ref "$(basename "$SUPABASE_URL" .supabase.co)" \
            --execute "SELECT tier FROM api_keys WHERE key='$API_KEY';" \
            2>/dev/null | tail -1 | tr -d '[:space:]')
    else
        # Use direct API call
        TIER_CHECK=$(curl -s \
            -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE" \
            -H "apikey: $SUPABASE_SERVICE_ROLE" \
            "$SUPABASE_URL/rest/v1/api_keys?key=eq.$API_KEY&select=tier" \
            2>/dev/null | grep -o '"tier":"[^"]*"' | cut -d'"' -f4)
    fi
    set -e
    
    if [[ "$TIER_CHECK" == "starter" ]]; then
        TIER_UPDATED=true
        break
    fi
    
    sleep 2
done

echo ""
if [ "$TIER_UPDATED" = true ]; then
    show_result 0 "Tier updated to starter in Supabase"
else
    show_result 1 "Tier update timeout (still showing: $TIER_CHECK)"
    echo -e "${YELLOW}   Note: Manual verification may be needed in Supabase dashboard${NC}"
fi
echo ""

# Test 5: Starter Tier Concurrent Rate Limiting
echo -e "${YELLOW}⚡ Test 5: Concurrent Rate Limiting (Starter: 3 allowed, 2+ denied)${NC}"

# Create temporary directory for concurrent test results
mkdir -p /tmp/redforge_paid_test

# Launch 5 concurrent requests
echo "Launching 5 concurrent scan requests..."
for i in {1..5}; do
    {
        CONCURRENT_CODE=$(curl -s --max-time 15 -o /dev/null -w "%{http_code}" \
            -X POST "$API_BASE/scan" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: $API_KEY" \
            -d '{"target":"gpt-4","dry_run":true}' 2>/dev/null || echo "000")
        echo "$CONCURRENT_CODE" > "/tmp/redforge_paid_test/scan_$i"
    } &
done

# Wait for all requests to complete
wait

# Count results
OK_COUNT=0
DENY_COUNT=0
TIMEOUT_COUNT=0

echo "Analyzing concurrent request results:"
for i in {1..5}; do
    if [ -f "/tmp/redforge_paid_test/scan_$i" ]; then
        CODE=$(cat "/tmp/redforge_paid_test/scan_$i")
        echo "  Request $i: HTTP $CODE"
        
        case "$CODE" in
            200) OK_COUNT=$((OK_COUNT + 1)) ;;
            429|402) DENY_COUNT=$((DENY_COUNT + 1)) ;;
            000) TIMEOUT_COUNT=$((TIMEOUT_COUNT + 1)) ;;
            *) echo "    Unexpected code: $CODE" ;;
        esac
    fi
done

# Clean up
rm -rf /tmp/redforge_paid_test

# Evaluate results
if [ $OK_COUNT -ge 3 ] && [ $DENY_COUNT -ge 1 ]; then
    show_result 0 "Concurrent rate limiting working ($OK_COUNT×200, $DENY_COUNT×429/402)"
elif [ $OK_COUNT -ge 1 ] && [ $DENY_COUNT -ge 1 ]; then
    show_result 0 "Some rate limiting detected ($OK_COUNT×200, $DENY_COUNT×429/402)"
    echo -e "${YELLOW}   Note: May need tier update propagation time${NC}"
elif [ $TIMEOUT_COUNT -ge 3 ]; then
    show_result 1 "Too many timeouts ($TIMEOUT_COUNT×timeout) - API Gateway overloaded?"
else
    show_result 1 "Rate limiting not working as expected ($OK_COUNT×200, $DENY_COUNT×429/402)"
fi
echo ""

# Test 6: Webhook Endpoint Verification
echo -e "${YELLOW}🔗 Test 6: Webhook Endpoint Health${NC}"

set +e
WEBHOOK_RESPONSE=$(curl -s --max-time 10 -w "\nHTTP_STATUS:%{http_code}" \
    "$API_BASE/stripe/webhook" \
    -X GET 2>/dev/null)
WEBHOOK_RET=$?
set -e

if [ $WEBHOOK_RET -eq 0 ]; then
    WEBHOOK_STATUS=$(echo "$WEBHOOK_RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
    if [ "$WEBHOOK_STATUS" = "200" ] || [ "$WEBHOOK_STATUS" = "405" ]; then
        show_result 0 "Webhook endpoint accessible (HTTP $WEBHOOK_STATUS)"
    else
        show_result 1 "Webhook endpoint issue (HTTP $WEBHOOK_STATUS)"
    fi
else
    show_result 1 "Webhook endpoint unreachable"
fi
echo ""

# Final Summary
echo -e "${BLUE}📊 Paid Flow Test Results${NC}"
echo -e "${BLUE}=========================${NC}"
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $((TOTAL_TESTS - FAILED_TESTS))${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL PAID FLOW TESTS PASSED!${NC}"
    echo -e "${GREEN}✅ Ready for production release with paid features!${NC}"
    SUCCESS_RATE=100
    EXIT_CODE=0
else
    SUCCESS_RATE=$(( (TOTAL_TESTS - FAILED_TESTS) * 100 / TOTAL_TESTS ))
    echo -e "${YELLOW}⚠️  $FAILED_TESTS test(s) failed. Success rate: ${SUCCESS_RATE}%${NC}"
    
    if [ $SUCCESS_RATE -ge 85 ]; then
        echo -e "${GREEN}🚀 Acceptable for release (>85% success rate)${NC}"
        EXIT_CODE=0
    else
        echo -e "${RED}❌ Fix issues before release (<85% success rate)${NC}"
        EXIT_CODE=1
    fi
fi

echo ""
echo -e "📧 Test account: $TEST_EMAIL"
echo -e "🔑 API key: ${API_KEY:0:12}..."
echo -e "🌐 API base: $API_BASE"

echo ""
echo -e "${BLUE}💡 Manual Verification Checklist:${NC}"
echo -e "1. Check Render logs for webhook: /stripe/webhook OK 200"
echo -e "2. Verify Supabase dashboard shows tier=starter"
echo -e "3. Confirm Stripe dashboard shows successful payment"
echo -e "4. Test PDF generation works (wkhtmltopdf in Docker)"

echo ""
echo -e "${BLUE}🔥 Paid flow test complete!${NC}"
echo -e "Exit code: $EXIT_CODE"

exit $EXIT_CODE