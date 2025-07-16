#!/usr/bin/env python3
"""
Test usage tracking functionality
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from redforge.core.user_manager import UserManager

def test_usage_tracking():
    """Test the usage tracking system"""
    
    print("🧪 Testing Usage Tracking System")
    print("=" * 50)
    
    user_manager = UserManager()
    
    # Reset to free tier
    user_manager.set_user_tier("free")
    user_manager.reset_usage()
    
    print("✅ Reset to free tier")
    
    # Check initial status
    status = user_manager.get_usage_status()
    print(f"Initial status: {status}")
    
    # Test first usage
    if user_manager.can_use_free_tier():
        print("✅ Can use free tier - first scan allowed")
        new_count = user_manager.increment_free_usage()
        print(f"After first scan - usage count: {new_count}")
    else:
        print("❌ Cannot use free tier initially")
    
    # Check status after first usage
    status = user_manager.get_usage_status()
    print(f"After first scan: {status}")
    
    # Test second usage (should be blocked)
    if user_manager.can_use_free_tier():
        print("❌ Should not be able to use free tier after 1 scan")
    else:
        print("✅ Correctly blocked after 1 free scan")
    
    # Test paid tier upgrade
    user_manager.activate_paid_tier("test@example.com", "starter")
    status = user_manager.get_usage_status()
    print(f"After paid upgrade: {status}")
    
    if user_manager.can_use_free_tier():
        print("✅ Can use unlimited scans after paid upgrade")
    else:
        print("❌ Should be able to use unlimited scans")
    
    print("\n" + "=" * 50)
    print("🎯 Usage tracking test completed!")

if __name__ == "__main__":
    test_usage_tracking()