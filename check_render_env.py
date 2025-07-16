#!/usr/bin/env python3
"""
Check if Render environment variables are working
"""

import requests
import json

def check_render_environment():
    """Check Render environment variables"""
    
    print("🔍 Checking Render Environment Variables")
    print("=" * 50)
    
    try:
        # Test the health endpoint to see if it shows env status
        response = requests.get("https://redforge.onrender.com/", timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service is healthy")
            print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Test webhook endpoint with a simple request to see error details
    print(f"\n🧪 Testing webhook endpoint for error details...")
    
    try:
        response = requests.post(
            "https://redforge.onrender.com/webhook",
            data='{"test": "check_env"}',
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"Webhook Status: {response.status_code}")
        print(f"Webhook Response: {response.text}")
        
        if response.status_code == 400:
            # This is expected - we want to see the error message
            print("✅ Webhook is responding (400 is expected for invalid signature)")
        
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")

def test_webhook_with_proper_secret():
    """Test webhook with the correct secret now"""
    
    print(f"\n🔐 Testing Webhook with Updated Secret")
    print("=" * 50)
    
    import hmac
    import hashlib
    import time
    
    webhook_secret = 'whsec_BFaJ5UuUy5p7DUO6CTgm1Bnu14yIZpqg'
    
    # Create a simple test payload
    payload = json.dumps({
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{int(time.time())}",
                "customer_email": "test@redforge.ai",
                "metadata": {
                    "tier": "starter",
                    "email": "test@redforge.ai"
                }
            }
        }
    })
    
    timestamp = str(int(time.time()))
    
    # Create signature using the full secret
    signed_payload = f"{timestamp}.{payload}"
    signature = hmac.new(
        webhook_secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    stripe_signature = f"t={timestamp},v1={signature}"
    
    print(f"Payload length: {len(payload)} bytes")
    print(f"Signature: {stripe_signature[:50]}...")
    
    try:
        response = requests.post(
            "https://redforge.onrender.com/webhook",
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'stripe-signature': stripe_signature
            },
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook signature validation successful!")
            return True
        else:
            print(f"❌ Webhook still failing: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    check_render_environment()
    test_webhook_with_proper_secret()
    
    print(f"\n💡 If webhook is still failing:")
    print(f"1. Check Render dashboard → Service → Environment")
    print(f"2. Verify STRIPE_WEBHOOK_SECRET is set correctly")
    print(f"3. Redeploy the service after adding the env var")
    print(f"4. Check Render logs for detailed error messages")