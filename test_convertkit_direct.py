#!/usr/bin/env python3
"""
Test ConvertKit API directly
"""

import os
import requests
import json

def test_convertkit_api():
    """Test ConvertKit API with your credentials"""
    
    # Your ConvertKit credentials
    API_KEY = "C1FqQhtdxLgI3L1k3BEa2Q"
    API_SECRET = os.getenv('CONVERTKIT_API_SECRET')
    
    if not API_SECRET:
        print("❌ Please set CONVERTKIT_API_SECRET environment variable")
        print("   You can find it in ConvertKit Settings → Advanced → API")
        return
    
    print("🧪 Testing ConvertKit API Directly")
    print("=" * 50)
    
    # Test email
    test_email = "test-direct@redforge.ai"
    
    # Method 1: Create subscriber with tags
    print("\n1️⃣ Creating subscriber with tags...")
    
    response = requests.post(
        'https://api.convertkit.com/v3/subscribers',
        json={
            'api_secret': API_SECRET,
            'email': test_email,
            'tags': ['redforge-test', 'api-test']
        }
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Subscriber created successfully!")
        subscriber_id = response.json().get('subscriber', {}).get('id')
        print(f"Subscriber ID: {subscriber_id}")
    else:
        print("❌ Failed to create subscriber")
        print(f"Error: {response.text}")
        
    # Method 2: List tags to verify they exist
    print("\n2️⃣ Listing your tags...")
    
    tags_response = requests.get(
        f'https://api.convertkit.com/v3/tags?api_secret={API_SECRET}'
    )
    
    if tags_response.status_code == 200:
        tags = tags_response.json().get('tags', [])
        print(f"Found {len(tags)} tags:")
        for tag in tags[:5]:  # Show first 5
            print(f"  - {tag['name']} (ID: {tag['id']})")
    else:
        print("❌ Failed to list tags")
        
    print("\n" + "=" * 50)
    print("📌 Check your ConvertKit dashboard:")
    print("   https://app.convertkit.com/subscribers")
    print(f"   Look for: {test_email}")

if __name__ == "__main__":
    test_convertkit_api()