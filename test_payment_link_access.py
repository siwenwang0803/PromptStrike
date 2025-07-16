#!/usr/bin/env python3
"""
Test payment link access
"""

import requests
import json

def test_payment_link_access():
    """Test if payment link is accessible"""
    
    link = "https://checkout.stripe.com/c/pay/cs_live_a1c5I2Hw72N4UhdKplZYkmFSNAEDT0TDbkUqLTgSGTN6HErhYolUrAacmC"
    
    print(f"🔍 Testing payment link access...")
    print(f"Link: {link}")
    
    try:
        # Test with basic GET request
        response = requests.get(link, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("✅ Link is accessible")
            
            # Check if it contains expected Stripe checkout content
            if "stripe" in response.text.lower() and "checkout" in response.text.lower():
                print("✅ Contains Stripe checkout content")
                return True
            else:
                print("❌ Does not contain expected Stripe content")
                return False
        else:
            print(f"❌ Link returned status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def create_test_mode_payment():
    """Create a test mode payment link"""
    
    print("\n🧪 Creating test mode payment link...")
    
    try:
        import stripe
        
        # Use test key instead
        import os
        stripe.api_key = os.getenv('STRIPE_TEST_SECRET_KEY')
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'RedForge Test Payment'
                    },
                    'unit_amount': 2900,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://redforge.solvas.ai/success',
            cancel_url='https://redforge.solvas.ai/cancel',
        )
        
        print(f"✅ Test mode payment created!")
        print(f"🔗 Test Link: {session.url}")
        print(f"💡 This should work with test cards")
        
        return session.url
        
    except Exception as e:
        print(f"❌ Failed to create test payment: {e}")
        return None

if __name__ == "__main__":
    print("🔧 Testing Payment Link Access")
    print("=" * 50)
    
    if test_payment_link_access():
        print("\n✅ Payment link is working fine")
        print("💡 The issue might be:")
        print("   - Browser blocking popups")
        print("   - Ad blocker interference")
        print("   - Network restrictions")
        print("   - Cookie/JavaScript issues")
        print("\n🔧 Try:")
        print("   - Different browser")
        print("   - Incognito/private mode")
        print("   - Disable ad blockers")
        print("   - Clear cookies")
    else:
        print("\n❌ Payment link has issues")
        
        # Try test mode instead
        test_link = create_test_mode_payment()
        if test_link:
            print(f"\n🧪 Try this test mode link instead: {test_link}")