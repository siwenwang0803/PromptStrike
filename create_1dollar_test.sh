#!/bin/bash
# Create $1 test product for production verification

echo "Creating $1 test product in Stripe..."

# Make sure you're in live mode
stripe config --set live_mode true

# Create product
PRODUCT_ID=$(stripe products create \
  --name "RedForge Production Test" \
  --description "One dollar test payment for production verification" \
  --type service \
  --output json | jq -r '.id')

echo "Product created: $PRODUCT_ID"

# Create one-time $1 price
PRICE_ID=$(stripe prices create \
  --product $PRODUCT_ID \
  --unit-amount 100 \
  --currency usd \
  --output json | jq -r '.id')

echo "Price created: $PRICE_ID"

# Create payment link
PAYMENT_LINK=$(stripe payment-links create \
  --line-items "price=$PRICE_ID,quantity=1" \
  --after-completion "type=redirect,redirect[url]=https://redforge.solvas.ai/success" \
  --automatic-tax "enabled=false" \
  --output json | jq -r '.url')

echo ""
echo "✅ $1 Test Payment Link Created:"
echo "$PAYMENT_LINK"
echo ""
echo "Use this link to test production payment with real credit card"
echo "After testing, you can disable/delete this product in Stripe Dashboard"