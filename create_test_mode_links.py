#!/usr/bin/env python3
"""
Guide to create Stripe test mode payment links

This script helps you understand how to create test payment links in Stripe.
"""

print("""
🧪 How to Create Stripe Test Mode Payment Links
=============================================

1. Login to Stripe Dashboard:
   https://dashboard.stripe.com/

2. Switch to TEST MODE:
   - Look for the toggle switch in the top-right corner
   - Make sure it says "Test mode" (not "Live mode")

3. Create Payment Links:
   a) Go to: Products > Payment Links
   b) Click "New" or "Create payment link"
   c) Create your products:
      
      Starter Plan:
      - Name: "RedForge Starter"
      - Price: $29.00
      - Billing: Monthly
      - Description: "Unlimited security scans, OWASP patterns, Clean reports"
      
      Pro Plan:
      - Name: "RedForge Pro"
      - Price: $99.00
      - Billing: Monthly
      - Description: "Everything in Starter + Priority support, Custom patterns, API access"

4. Configure Payment Link Settings:
   - ✅ Collect customer name
   - ✅ Collect customer email
   - ✅ Allow promotion codes (for PH50 coupon)
   - ✅ Don't ask for phone number
   - ✅ Adjustable quantity: OFF

5. After Creation:
   - Copy the payment link URL
   - It should look like: https://buy.stripe.com/test_[unique_id]
   - The "test_" prefix indicates it's a test mode link

6. Test the Links:
   - Use test card: 4242 4242 4242 4242
   - Any future expiry date
   - Any 3-digit CVC
   - Any 5-digit ZIP

IMPORTANT: Test mode payment links are different from live mode links!
Make sure you're in TEST MODE when creating them.

Alternative: Use Stripe CLI
==========================
stripe products create --name "RedForge Starter" --description "Monthly subscription"
stripe prices create --product [PRODUCT_ID] --unit-amount 2900 --currency usd --recurring-interval month
stripe payment-links create --line-items "price=[PRICE_ID],quantity=1"
""")

# If you have the Stripe API key, you could also create them programmatically:
print("""

To create test links programmatically (requires stripe package):
=============================================================

import stripe
stripe.api_key = "sk_test_YOUR_TEST_SECRET_KEY"  # Use TEST key!

# Create product
product = stripe.Product.create(
    name="RedForge Starter",
    description="Unlimited security scans for LLM applications"
)

# Create price
price = stripe.Price.create(
    product=product.id,
    unit_amount=2900,  # $29.00 in cents
    currency="usd",
    recurring={"interval": "month"}
)

# Create payment link
payment_link = stripe.PaymentLink.create(
    line_items=[{
        "price": price.id,
        "quantity": 1
    }],
    after_completion={
        "type": "redirect",
        "redirect": {
            "url": "https://redforge.solvas.ai/success"
        }
    }
)

print(f"Payment link URL: {payment_link.url}")
""")