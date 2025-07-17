#!/usr/bin/env python3
"""
Direct Kit API test with proper tag IDs
"""

import requests
import json

# Your Kit credentials
API_KEY = "C1FqQhtdxLgI3L1k3BEa2Q"
API_SECRET = input("Enter your Kit API Secret (from Settings → Advanced → API): ")

print("\n🧪 Testing Kit API...")
print("=" * 50)

# First, let's get your tag IDs
print("\n1️⃣ Getting tag list...")
tags_response = requests.get(
    f'https://api.convertkit.com/v3/tags?api_secret={API_SECRET}'
)

tag_map = {}
if tags_response.ok:
    tags = tags_response.json().get('tags', [])
    print(f"\nFound {len(tags)} tags:")
    for tag in tags:
        print(f"  - {tag['name']} (ID: {tag['id']})")
        tag_map[tag['name']] = tag['id']
else:
    print(f"❌ Failed to get tags: {tags_response.status_code}")
    print(tags_response.text)

# Create subscriber with tag IDs
print("\n2️⃣ Creating subscriber...")
test_email = "kit-test-direct@redforge.ai"

# Try to find or create tags
tag_ids = []
for tag_name in ['redforge-user', 'landing-signup', 'product-hunt-2025']:
    if tag_name in tag_map:
        tag_ids.append(tag_map[tag_name])
        print(f"  ✅ Using existing tag: {tag_name}")

# Method 1: Create subscriber
response = requests.post(
    'https://api.convertkit.com/v3/subscribers',
    json={
        'api_secret': API_SECRET,
        'email': test_email
    }
)

if response.ok:
    subscriber = response.json().get('subscriber', {})
    subscriber_id = subscriber.get('id')
    print(f"\n✅ Subscriber created/found!")
    print(f"   ID: {subscriber_id}")
    print(f"   Email: {subscriber.get('email')}")
    
    # Add tags separately
    if tag_ids and subscriber_id:
        print(f"\n3️⃣ Adding tags to subscriber...")
        for tag_id in tag_ids:
            tag_response = requests.post(
                f'https://api.convertkit.com/v3/tags/{tag_id}/subscribers',
                json={
                    'api_secret': API_SECRET,
                    'subscribers': [subscriber_id]
                }
            )
            if tag_response.ok:
                print(f"  ✅ Added tag ID: {tag_id}")
            else:
                print(f"  ❌ Failed to add tag: {tag_response.text}")
else:
    print(f"\n❌ Failed to create subscriber: {response.status_code}")
    print(response.text)

print("\n" + "=" * 50)
print("📌 Check your Kit dashboard now:")
print("   https://app.convertkit.com/subscribers")
print(f"   Look for: {test_email}")
print("\n✅ If this works, the issue is with Render environment variables!")