#!/usr/bin/env bash
# Direct API Gateway test to debug the connection issue

API_BASE="https://api-gateway-uenk.onrender.com"

echo "=== Direct API Gateway Test ==="
echo "API Base: $API_BASE"
echo ""

echo "Test 1: Basic curl connection"
curl -v "$API_BASE/healthz"
echo ""

echo "Test 2: Check if docs endpoint exists"
curl -v "$API_BASE/docs"
echo ""

echo "Test 3: Test signup endpoint"
TEST_EMAIL="debug-$(date +%s)@test.com"
echo "Testing signup with: $TEST_EMAIL"
curl -v -X POST "$API_BASE/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\"}"
echo ""