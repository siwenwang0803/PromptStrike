#!/usr/bin/env python3
"""
Simple Kit API test
"""

import requests
import json
import os

# Get from environment or prompt
API_SECRET = os.getenv('CONVERTKIT_API_SECRET', '')

if not API_SECRET:
    print("Set CONVERTKIT_API_SECRET environment variable first!")
    print("export CONVERTKIT_API_SECRET='your_secret_here'")
    exit(1)

# Test email
test_email = "simple-test@redforge.ai"

print(f"Testing Kit API with email: {test_email}")

# Simple subscriber creation
response = requests.post(
    'https://api.convertkit.com/v3/subscribers',
    json={
        'api_secret': API_SECRET,
        'email': test_email
    }
)

print(f"Status: {response.status_code}")
if response.ok:
    print("✅ Success! Check Kit dashboard")
    print(json.dumps(response.json(), indent=2))
else:
    print("❌ Failed:")
    print(response.text)