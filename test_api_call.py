#!/usr/bin/env python3
"""
Test script to verify API call works
"""

import asyncio
import httpx
import os
import json

async def test_openai_api():
    """Test OpenAI API call"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, world!"}],
        "max_tokens": 10
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')}")
                return True
            else:
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openai_api())
    if success:
        print("✅ API call successful")
    else:
        print("❌ API call failed")