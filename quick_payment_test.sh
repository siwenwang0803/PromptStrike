#!/usr/bin/env bash
# Quick payment test for RedForge - minimal version

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🚀 RedForge Quick Payment Test${NC}"
echo "=============================="

# 1. Check API health
echo -e "\n1️⃣ Checking API health..."
HEALTH=$(curl -s https://redforge.onrender.com/healthz | grep -o '"database":"connected"' || echo "failed")
if [[ "$HEALTH" == *"connected"* ]]; then
    echo -e "${GREEN}✅ API is healthy${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
    exit 1
fi

# 2. Test webhook endpoint
echo -e "\n2️⃣ Testing webhook endpoint..."
WEBHOOK_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST https://redforge.onrender.com/stripe/webhook)
if [ "$WEBHOOK_CODE" = "400" ]; then
    echo -e "${GREEN}✅ Webhook endpoint ready${NC}"
else
    echo -e "${RED}❌ Webhook not responding correctly (HTTP $WEBHOOK_CODE)${NC}"
fi

# 3. Payment instructions
echo -e "\n3️⃣ ${YELLOW}Manual Payment Test:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Payment Links:"
echo ""
echo "💵 $1 Test Link:"
echo "   ${1:-[Set your $1 test link as first argument]}"
echo ""
echo "💰 $29 Production Link:"
echo "   https://buy.stripe.com/[your-29-dollar-link]"
echo ""
echo "🏷️ Use promo code: PH50 (for 50% off)"
echo "💳 Test card: 4242 4242 4242 4242"
echo "📅 Expiry: Any future date"
echo "🔢 CVC: Any 3 digits"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -e "\n${YELLOW}After payment, check:${NC}"
echo "✉️  Email for API key (from dev@solvas.ai)"
echo "📊 Stripe Dashboard → Events (should show 200 OK)"
echo "🔍 Render logs for processing details"

echo -e "\n4️⃣ ${YELLOW}Test your API key:${NC}"
echo '```bash'
echo 'curl -X POST https://redforge.onrender.com/scan \'
echo '  -H "X-API-Key: rk_YOUR_KEY_HERE" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d "{\"target\": \"gpt-4\", \"dry_run\": true}"'
echo '```'

echo -e "\n${GREEN}Ready to test! Follow the steps above.${NC}"