#!/usr/bin/env python3
"""
Test webhook with proper Stripe signature
"""

import os
import json
import time
import hmac
import hashlib
import requests

def create_stripe_signature(payload, webhook_endpoint_secret, timestamp=None):
    """Create a proper Stripe webhook signature"""
    
    if timestamp is None:
        timestamp = str(int(time.time()))
    
    # Extract the actual secret from whsec_xxxxx format
    if webhook_endpoint_secret.startswith('whsec_'):
        secret = webhook_endpoint_secret[6:]  # Remove 'whsec_' prefix
    else:
        secret = webhook_endpoint_secret
    
    # Create signature payload: timestamp.payload
    signed_payload = f"{timestamp}.{payload}"
    
    # Create HMAC-SHA256 signature using base64 decoded secret
    import base64
    try:
        # Stripe webhook secrets are base64 encoded
        secret_bytes = base64.b64decode(secret)
    except:
        # If not base64, use as-is
        secret_bytes = secret.encode('utf-8')
    
    signature = hmac.new(
        secret_bytes,
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Format as Stripe expects: t=timestamp,v1=signature
    return f"t={timestamp},v1={signature}"

def test_webhook_with_signature():
    """Test webhook endpoint with proper signature"""
    
    print("🔐 Testing Webhook with Proper Stripe Signature")
    print("=" * 60)
    
    # Your webhook secret
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET') or 'whsec_BFaJ5UuUy5p7DUO6CTgm1Bnu14yIZpqg'
    
    # Create mock event
    mock_event = {
        "id": f"evt_test_{int(time.time())}",
        "object": "event",
        "api_version": "2020-08-27",
        "created": int(time.time()),
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{int(time.time())}",
                "object": "checkout.session",
                "customer_email": "test-webhook@redforge.ai",
                "customer": f"cus_test_{int(time.time())}",
                "subscription": f"sub_test_{int(time.time())}",
                "payment_status": "paid",
                "metadata": {
                    "tier": "starter",
                    "email": "test-webhook@redforge.ai",
                    "source": "webhook_test"
                }
            }
        }
    }
    
    # Convert to JSON payload
    payload = json.dumps(mock_event, separators=(',', ':'))
    print(f"📦 Payload size: {len(payload)} bytes")
    
    # Create proper Stripe signature
    timestamp = str(int(time.time()))
    stripe_signature = create_stripe_signature(payload, webhook_secret, timestamp)
    print(f"🔐 Signature: {stripe_signature[:50]}...")
    
    # Send to webhook endpoint
    print(f"\n📤 Sending to: https://redforge.onrender.com/webhook")
    
    try:
        response = requests.post(
            'https://redforge.onrender.com/webhook',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'stripe-signature': stripe_signature,
                'User-Agent': 'Stripe/1.0 (+https://stripe.com/docs/webhooks)'
            },
            timeout=30
        )
        
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ Webhook signature validation successful!")
            return True
        else:
            print(f"\n❌ Webhook failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Webhook request failed: {e}")
        return False

def test_signature_locally():
    """Test signature generation locally"""
    
    print("\n🧪 Testing signature generation locally...")
    
    import stripe
    webhook_secret = 'whsec_BFaJ5UuUy5p7DUO6CTgm1Bnu14yIZpqg'
    
    payload = '{"test": "data"}'
    timestamp = str(int(time.time()))
    
    # Generate signature
    signature = create_stripe_signature(payload, webhook_secret, timestamp)
    print(f"Generated signature: {signature}")
    
    # Test with Stripe's validation
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        print("✅ Local signature validation passed!")
        return True
    except Exception as e:
        print(f"❌ Local signature validation failed: {e}")
        return False

if __name__ == "__main__":
    print("🔐 Stripe Webhook Signature Test")
    print("=" * 60)
    
    # Test local signature generation first
    if test_signature_locally():
        print("\n" + "="*60)
        # Test actual webhook endpoint
        test_webhook_with_signature()
    else:
        print("❌ Local signature test failed, skipping webhook test")