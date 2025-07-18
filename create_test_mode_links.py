#!/usr/bin/env python3
"""
Create TEST mode payment links for testing
"""

import os
import stripe
from datetime import datetime, timedelta

# Use TEST API key from environment
stripe.api_key = os.getenv('STRIPE_TEST_SECRET_KEY')
if not stripe.api_key:
    print("❌ Please set STRIPE_TEST_SECRET_KEY environment variable")
    exit(1)

def create_test_payment_links():
    """Create test mode payment links"""
    
    print("🧪 Creating TEST MODE Payment Links")
    print("=" * 50)
    
    # Create Starter Plan link ($29/month)
    print("\n1️⃣ Creating Starter Plan link...")
    try:
        starter_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'RedForge Starter Plan (TEST)',
                        'description': 'Monthly subscription - LLM Security Platform',
                    },
                    'unit_amount': 2900,  # $29.00
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://redforge.solvas.ai/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://redforge.solvas.ai/cancel',
            metadata={
                'tier': 'starter',
                'test_mode': 'true'
            }
        )
        
        print(f"✅ Starter link created!")
        print(f"📝 Session ID: {starter_session.id}")
        print(f"🔗 TEST Link: {starter_session.url}")
        starter_url = starter_session.url
        
    except Exception as e:
        print(f"❌ Error: {e}")
        starter_url = None
    
    # Create Pro Plan link ($99/month)
    print("\n2️⃣ Creating Pro Plan link...")
    try:
        pro_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'RedForge Pro Plan (TEST)',
                        'description': 'Monthly subscription - LLM Security Platform',
                    },
                    'unit_amount': 9900,  # $99.00
                    'recurring': {
                        'interval': 'month'
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://redforge.solvas.ai/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://redforge.solvas.ai/cancel',
            metadata={
                'tier': 'pro',
                'test_mode': 'true'
            }
        )
        
        print(f"✅ Pro link created!")
        print(f"📝 Session ID: {pro_session.id}")
        print(f"🔗 TEST Link: {pro_session.url}")
        pro_url = pro_session.url
        
    except Exception as e:
        print(f"❌ Error: {e}")
        pro_url = None
    
    print("\n" + "=" * 50)
    print("💳 TEST MODE PAYMENT LINKS:")
    print("=" * 50)
    
    if starter_url:
        print(f"\n🚀 STARTER PLAN ($29/month):")
        print(f"   {starter_url}")
    
    if pro_url:
        print(f"\n💎 PRO PLAN ($99/month):")
        print(f"   {pro_url}")
    
    print("\n📋 TEST CARD DETAILS:")
    print("Card: 4242 4242 4242 4242")
    print("Expiry: 12/34")
    print("CVC: 123")
    print("ZIP: Any 5 digits")
    
    print("\n⚠️  IMPORTANT:")
    print("These are TEST MODE links!")
    print("They will accept test cards only")
    print("No real money will be charged")
    
    # Save to file
    if starter_url or pro_url:
        with open('test_payment_links.txt', 'w') as f:
            f.write("TEST MODE PAYMENT LINKS\n")
            f.write("=====================\n\n")
            f.write(f"Created: {datetime.now()}\n\n")
            f.write(f"STARTER: {starter_url}\n\n")
            f.write(f"PRO: {pro_url}\n")
        print("\n✅ Links saved to: test_payment_links.txt")

if __name__ == "__main__":
    create_test_payment_links()