"""
User Management System - Track user tier and usage
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class UserManager:
    """Manage user tiers and usage tracking"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / ".redforge"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.user_file = self.config_dir / "user.json"
        self.usage_file = self.config_dir / "usage.json"
        
    def get_user_tier(self) -> str:
        """Get current user tier"""
        user_data = self._load_user_data()
        return user_data.get("tier", "free")
    
    def set_user_tier(self, tier: str, email: Optional[str] = None):
        """Set user tier (called after successful payment)"""
        user_data = self._load_user_data()
        user_data["tier"] = tier
        user_data["updated_at"] = datetime.now().isoformat()
        
        if email:
            user_data["email"] = email
            
        self._save_user_data(user_data)
    
    def get_free_usage(self) -> int:
        """Get current free usage count"""
        usage_data = self._load_usage_data()
        return usage_data.get("free_used", 0)
    
    def increment_free_usage(self) -> int:
        """Increment free usage count and return new count"""
        usage_data = self._load_usage_data()
        usage_data["free_used"] = usage_data.get("free_used", 0) + 1
        usage_data["last_used"] = datetime.now().isoformat()
        
        self._save_usage_data(usage_data)
        return usage_data["free_used"]
    
    def can_use_free_tier(self) -> bool:
        """Check if user can still use free tier"""
        if self.get_user_tier() != "free":
            return True  # Paid users can always use
            
        free_used = self.get_free_usage()
        return free_used < 1  # Only allow 1 free scan
    
    def get_usage_status(self) -> Dict:
        """Get complete usage status"""
        tier = self.get_user_tier()
        free_used = self.get_free_usage()
        can_use = self.can_use_free_tier()
        
        return {
            "tier": tier,
            "free_used": free_used,
            "can_use_free": can_use,
            "is_paid": tier != "free",
            "remaining_free": max(0, 1 - free_used) if tier == "free" else "unlimited"
        }
    
    def _load_user_data(self) -> Dict:
        """Load user data from file"""
        if not self.user_file.exists():
            return {}
            
        try:
            with open(self.user_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_user_data(self, data: Dict):
        """Save user data to file"""
        with open(self.user_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_usage_data(self) -> Dict:
        """Load usage data from file"""
        if not self.usage_file.exists():
            return {}
            
        try:
            with open(self.usage_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_usage_data(self, data: Dict):
        """Save usage data to file"""
        with open(self.usage_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def reset_usage(self):
        """Reset usage data (for testing)"""
        self.usage_file.unlink(missing_ok=True)
    
    def activate_paid_tier(self, email: str, tier: str = "starter"):
        """Activate paid tier after successful payment"""
        self.set_user_tier(tier, email)
        
        # Log activation
        activation_data = {
            "email": email,
            "tier": tier,
            "activated_at": datetime.now().isoformat(),
            "method": "stripe_payment"
        }
        
        activation_file = self.config_dir / "activation.json"
        with open(activation_file, 'w') as f:
            json.dump(activation_data, f, indent=2)
            
        print(f"✅ Activated {tier} tier for {email}")