#!/usr/bin/env python3
"""
Test scanner directly
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from redforge.core.scanner import LLMScanner
from redforge.core.attacks import AttackPackLoader
from redforge.utils.config import Config

async def test_scanner():
    """Test scanner directly"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return False
    
    # Create config
    config = Config()
    config.api_key = api_key
    
    # Create scanner
    scanner = LLMScanner(
        target="gpt-3.5-turbo",
        config=config,
        max_requests=1,
        timeout=10,
        verbose=True
    )
    
    # Load one attack
    attack_loader = AttackPackLoader()
    attacks = attack_loader.load_pack("owasp-llm-top10")
    
    if not attacks:
        print("❌ No attacks loaded")
        return False
    
    # Test first attack
    first_attack = attacks[0]
    print(f"Testing attack: {first_attack.id}")
    
    try:
        async with scanner:
            result = await scanner.run_attack(first_attack)
            print(f"✅ Attack result: {result.attack_id}")
            print(f"   Vulnerable: {result.is_vulnerable}")
            print(f"   Response: {result.response_received[:100]}...")
            return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_scanner())
    if success:
        print("✅ Scanner test successful")
    else:
        print("❌ Scanner test failed")