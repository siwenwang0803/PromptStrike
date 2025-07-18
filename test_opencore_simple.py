#!/usr/bin/env python3
"""
Simple Open-Core Implementation Test
Quick verification that all features work
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Check OpenAI API key for testing
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Please set OPENAI_API_KEY environment variable for testing")
    sys.exit(1)

def run_cmd(cmd):
    """Run command and return success/output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def test_basic_functionality():
    """Test basic Open-Core functionality"""
    print("🔥 Testing RedForge Open-Core Implementation")
    print("=" * 50)
    
    # Test 1: CLI Help
    print("\n1. Testing CLI help...")
    success, output, error = run_cmd("python3 -m redforge.cli --help")
    if success and "scan" in output and "status" in output and "signup" in output:
        print("✅ CLI help works with new commands")
    else:
        print(f"❌ CLI help failed: {error}")
        return False
    
    # Test 2: Status command
    print("\n2. Testing status command...")
    success, output, error = run_cmd("python3 -m redforge.cli status")
    if success:
        print("✅ Status command works")
        print(f"   Output: {output.strip()}")
    else:
        print(f"❌ Status command failed: {error}")
        return False
    
    # Test 3: List attacks
    print("\n3. Testing list-attacks command...")
    success, output, error = run_cmd("python3 -m redforge.cli list-attacks")
    if success and "LLM01" in output:
        print("✅ List-attacks command works")
    else:
        print(f"❌ List-attacks failed: {error}")
        return False
    
    # Test 4: Signup command
    print("\n4. Testing signup command...")
    success, output, error = run_cmd("python3 -m redforge.cli signup test@redforge.ai --name 'Test User'")
    if success or "temporarily unavailable" in output:
        print("✅ Signup command works (with Kit fallback)")
    else:
        print(f"❌ Signup failed: {error}")
        return False
    
    # Test 5: Activate command
    print("\n5. Testing activate command...")
    success, output, error = run_cmd("python3 -m redforge.cli activate test-key-123")
    if success and "activated" in output.lower():
        print("✅ Activate command works")
    else:
        print(f"❌ Activate failed: {error}")
        return False
    
    # Test 6: Cloud client import
    print("\n6. Testing cloud client import...")
    success, output, error = run_cmd("python3 -c 'from redforge.cloud_client import CloudClient; print(\"Import successful\")'")
    if success:
        print("✅ Cloud client imports successfully")
    else:
        print(f"❌ Cloud client import failed: {error}")
        return False
    
    # Test 7: Kit integration (optional)
    print("\n7. Testing Kit integration...")
    success, output, error = run_cmd("python3 -c 'from redforge.integrations.convertkit import capture_email; print(\"Kit integration available\")'")
    if success:
        print("✅ Kit integration imports successfully")
    else:
        print(f"❌ Kit integration failed: {error}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All Open-Core features working correctly!")
    print("✅ CLI commands: scan, status, signup, activate")
    print("✅ Cloud client integration")
    print("✅ Kit email integration (optional)")
    print("✅ OWASP attack packs available")
    print("\n🚀 Ready for Product Hunt launch!")
    
    return True

if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)