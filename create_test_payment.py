#!/usr/bin/env python3
"""
Create test mode payment link for testing
"""

import os
import time
import stripe
from datetime import datetime, timedelta

# Use TEST key for testing
stripe.api_key = os.getenv('STRIPE_TEST_SECRET_KEY')

def create_test_payment_link():
    """Create a test mode payment link"""
    
    print("🧪 Creating TEST MODE payment link...")
    
    try:
        timestamp = int(time.time())
        test_email = f"test-{timestamp}@redforge.ai"
        
        # Create test mode checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'RedForge Starter Plan (TEST)',
                        'description': 'Monthly subscription to RedForge LLM Security Platform (TEST MODE)',
                    },
                    'unit_amount': 2900,  # $29.00
                    'recurring': {
                        'interval': 'month',
                        'interval_count': 1
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://redforge.solvas.ai/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://redforge.solvas.ai/cancel',
            customer_email=test_email,
            allow_promotion_codes=True,
            metadata={
                'tier': 'starter',
                'email': test_email,
                'source': 'test_mode',
                'timestamp': str(timestamp)
            },
            expires_at=int((datetime.now() + timedelta(hours=24)).timestamp())
        )
        
        print(f"✅ TEST MODE payment link created!")
        print(f"📧 Test Email: {test_email}")
        print(f"🆔 Session ID: {session.id}")
        print(f"🔗 Payment URL: {session.url}")
        print(f"💰 Amount: $29.00/month (TEST MODE)")
        print(f"💳 Use test card: 4242 4242 4242 4242")
        print(f"📅 Expiry: Any future date (e.g., 12/34)")
        print(f"🔒 CVC: Any 3 digits (e.g., 123)")
        
        # Save details
        with open('test_payment_link.txt', 'w') as f:
            f.write(f"TEST MODE Payment Link\n")
            f.write(f"======================\n")
            f.write(f"Test Email: {test_email}\n")
            f.write(f"Session ID: {session.id}\n")
            f.write(f"Payment URL: {session.url}\n")
            f.write(f"Created: {datetime.now()}\n")
            f.write(f"Amount: $29.00/month (TEST MODE)\n")
            f.write(f"Test Card: 4242 4242 4242 4242\n")
            f.write(f"Test Expiry: 12/34\n")
            f.write(f"Test CVC: 123\n")
        
        return session.url
        
    except Exception as e:
        print(f"❌ Error creating test payment link: {e}")
        return None

def create_live_payment_with_warning():
    """Create live payment with warning about real charges"""
    
    print("\n💰 Creating LIVE MODE payment link...")
    print("⚠️  WARNING: This will charge real money!")
    print("⚠️  Only use real credit/debit cards!")
    
    try:
        # Use LIVE key
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        
        timestamp = int(time.time())
        test_email = f"live-{timestamp}@redforge.ai"
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'RedForge Starter Plan',
                        'description': 'Monthly subscription to RedForge LLM Security Platform',
                    },
                    'unit_amount': 2900,  # $29.00
                    'recurring': {
                        'interval': 'month',
                        'interval_count': 1
                    }
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://redforge.solvas.ai/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://redforge.solvas.ai/cancel',
            customer_email=test_email,
            metadata={
                'tier': 'starter',
                'email': test_email,
                'source': 'live_mode',
                'timestamp': str(timestamp)
            },
            expires_at=int((datetime.now() + timedelta(hours=24)).timestamp())
        )
        
        print(f"✅ LIVE MODE payment link created!")
        print(f"💰 Amount: $29.00/month (REAL CHARGES)")
        print(f"🔗 Payment URL: {session.url}")
        print(f"⚠️  Use REAL card only - test cards will be declined!")
        
        return session.url
        
    except Exception as e:
        print(f"❌ Error creating live payment link: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Creating Payment Links")
    print("=" * 50)
    
    # Create test mode link
    test_url = create_test_payment_link()
    
    if test_url:
        print(f"\n🧪 TEST MODE LINK (Use this first):")
        print(f"   {test_url}")
        print(f"   💳 Test card: 4242 4242 4242 4242")
        print(f"   📅 Expiry: 12/34")
        print(f"   🔒 CVC: 123")
    
    # Ask about live mode
    print(f"\n" + "=" * 50)
    print("🤔 Do you want to create a LIVE MODE link too?")
    print("   This will charge REAL money!")
    print("   Only use if you want to test with real payment.")
    
    live_url = create_live_payment_with_warning()
    
    if live_url:
        print(f"\n💰 LIVE MODE LINK (REAL CHARGES):")
        print(f"   {live_url}")
        print(f"   ⚠️  Use REAL card only!")
    
    print(f"\n✅ Payment links created!")
    print(f"📁 Details saved to: test_payment_link.txt")