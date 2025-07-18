"""
ConvertKit Integration for RedForge
Handles email capture and nurture sequences
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class ConvertKitClient:
    """ConvertKit API client for email marketing"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.getenv('KIT_API_KEY')
        self.api_secret = api_secret or os.getenv('KIT_API_SECRET')
        self.base_url = "https://api.convertkit.com/v3"
        
        if not self.api_key:
            print("⚠️  Kit API key not configured. Email capture will use fallback mode.")
            self.api_key = None
            self.api_secret = None
    
    def add_subscriber(self, email: str, first_name: Optional[str] = None, 
                      tags: Optional[list] = None, custom_fields: Optional[Dict] = None) -> bool:
        """Add subscriber to ConvertKit"""
        
        if not self.api_key:
            print("⚠️  Kit not configured, using fallback mode")
            return False
        
        data = {
            'api_key': self.api_key,
            'email': email
        }
        
        if first_name:
            data['first_name'] = first_name
            
        if custom_fields:
            data.update(custom_fields)
        
        try:
            # Add to main subscribers list (using form ID 8320684)
            response = requests.post(
                f"{self.base_url}/forms/8320684/subscribe",
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                subscriber_id = response.json().get('subscription', {}).get('subscriber', {}).get('id')
                
                # Add tags if provided
                if tags and subscriber_id:
                    self._add_tags(subscriber_id, tags)
                
                return True
            else:
                print(f"ConvertKit API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"ConvertKit integration error: {e}")
            return False
    
    def _add_tags(self, subscriber_id: int, tags: list) -> bool:
        """Add tags to subscriber"""
        
        for tag in tags:
            try:
                data = {
                    'api_key': self.api_key,
                    'email': subscriber_id
                }
                
                requests.post(
                    f"{self.base_url}/tags/{tag}/subscribe",
                    data=data,
                    timeout=10
                )
            except Exception as e:
                print(f"Error adding tag {tag}: {e}")
        
        return True
    
    def trigger_sequence(self, email: str, sequence_id: str) -> bool:
        """Trigger a specific email sequence"""
        
        data = {
            'api_key': self.api_key,
            'email': email
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/sequences/{sequence_id}/subscribe",
                data=data,
                timeout=30
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error triggering sequence: {e}")
            return False


class EmailCaptureManager:
    """Manage email capture and user journey"""
    
    def __init__(self):
        try:
            self.convertkit = ConvertKitClient()
        except Exception as e:
            print(f"⚠️  ConvertKit initialization failed: {e}")
            self.convertkit = None
        
        self.config_dir = Path.home() / ".redforge"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.email_file = self.config_dir / "email_data.json"
    
    def capture_email(self, email: str, source: str, user_tier: str = "free", 
                     name: Optional[str] = None) -> bool:
        """Capture email and add to appropriate nurture sequence"""
        
        # Determine tags based on source and tier
        tags = self._get_tags(source, user_tier)
        
        # Custom fields for segmentation
        custom_fields = {
            'tier': user_tier,
            'source': source,
            'signup_date': datetime.now().isoformat(),
            'product_hunt_launch': 'true' if source == 'product_hunt' else 'false'
        }
        
        # Add to ConvertKit (if available)
        success = False
        if self.convertkit is not None:
            success = self.convertkit.add_subscriber(
                email=email,
                first_name=name,
                tags=tags,
                custom_fields=custom_fields
            )
        else:
            print("⚠️  Kit not available, storing email locally only")
            success = True  # Consider local storage as success
        
        if success:
            # Store locally for CLI integration
            self._store_email_data(email, source, user_tier, name)
            
            # Trigger appropriate welcome sequence (if ConvertKit available)
            if self.convertkit is not None:
                self._trigger_welcome_sequence(email, source, user_tier)
        
        return success
    
    def _get_tags(self, source: str, user_tier: str) -> list:
        """Get ConvertKit tags based on source and tier"""
        
        tags = ['redforge-user']
        
        # Source tags
        source_tags = {
            'landing_page': 'landing-signup',
            'product_hunt': 'product-hunt-2025',
            'github': 'github-visitor',
            'cli_first_run': 'cli-user',
            'free_limit_reached': 'conversion-ready',
            'payment_completed': 'paid-customer'
        }
        
        if source in source_tags:
            tags.append(source_tags[source])
        
        # Tier tags
        if user_tier == 'free':
            tags.append('free-tier')
        elif user_tier in ['starter', 'pro']:
            tags.append('paid-customer')
            tags.append(f'{user_tier}-plan')
        
        return tags
    
    def _trigger_welcome_sequence(self, email: str, source: str, user_tier: str):
        """Trigger appropriate welcome email sequence"""
        
        if self.convertkit is None:
            print("⚠️  Kit not available, skipping welcome sequence")
            return
        
        # Sequence IDs (you'll need to create these in ConvertKit)
        sequences = {
            'free_welcome': 'FREE_WELCOME_SEQ_ID',
            'product_hunt': 'PRODUCT_HUNT_SEQ_ID', 
            'conversion_nurture': 'CONVERSION_SEQ_ID',
            'paid_onboarding': 'PAID_ONBOARD_SEQ_ID'
        }
        
        # Determine which sequence to trigger
        if user_tier == 'free':
            if source == 'product_hunt':
                sequence_id = sequences['product_hunt']
            elif source == 'free_limit_reached':
                sequence_id = sequences['conversion_nurture']
            else:
                sequence_id = sequences['free_welcome']
        else:
            sequence_id = sequences['paid_onboarding']
        
        # Trigger the sequence
        self.convertkit.trigger_sequence(email, sequence_id)
    
    def _store_email_data(self, email: str, source: str, user_tier: str, name: Optional[str]):
        """Store email data locally for CLI integration"""
        
        email_data = {}
        
        # Load existing data
        if self.email_file.exists():
            try:
                with open(self.email_file, 'r') as f:
                    email_data = json.load(f)
            except:
                email_data = {}
        
        # Add new data
        email_data[email] = {
            'name': name,
            'tier': user_tier,
            'source': source,
            'captured_at': datetime.now().isoformat(),
            'convertkit_added': True
        }
        
        # Save data
        with open(self.email_file, 'w') as f:
            json.dump(email_data, f, indent=2)
    
    def get_user_email(self) -> Optional[str]:
        """Get stored email for current user"""
        
        if not self.email_file.exists():
            return None
        
        try:
            with open(self.email_file, 'r') as f:
                email_data = json.load(f)
                
            # Return the most recent email
            if email_data:
                recent_email = max(email_data.items(), 
                                 key=lambda x: x[1].get('captured_at', ''))
                return recent_email[0]
        except:
            pass
        
        return None
    
    def update_user_tier(self, email: str, new_tier: str):
        """Update user tier after payment"""
        
        # Update ConvertKit (if available)
        if self.convertkit is not None:
            self.convertkit.add_subscriber(
                email=email,
                custom_fields={'tier': new_tier},
                tags=self._get_tags('payment_completed', new_tier)
            )
        else:
            print("⚠️  Kit not available, updating local data only")
        
        # Update local data
        if self.email_file.exists():
            try:
                with open(self.email_file, 'r') as f:
                    email_data = json.load(f)
                
                if email in email_data:
                    email_data[email]['tier'] = new_tier
                    email_data[email]['upgraded_at'] = datetime.now().isoformat()
                    
                    with open(self.email_file, 'w') as f:
                        json.dump(email_data, f, indent=2)
            except:
                pass


# Convenience functions for easy integration
def capture_email(email: str, source: str = "landing_page", name: Optional[str] = None) -> bool:
    """Simple email capture function"""
    manager = EmailCaptureManager()
    return manager.capture_email(email, source, "free", name)

def notify_free_limit_reached(email: str) -> bool:
    """Trigger conversion sequence when free limit reached"""
    manager = EmailCaptureManager()
    return manager.capture_email(email, "free_limit_reached", "free")

def notify_payment_completed(email: str, tier: str) -> bool:
    """Update user after successful payment"""
    manager = EmailCaptureManager()
    manager.update_user_tier(email, tier)
    return True