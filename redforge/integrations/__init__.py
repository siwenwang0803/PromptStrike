"""
RedForge Integrations Module
Email marketing and third-party service integrations
"""

from .convertkit import ConvertKitClient, EmailCaptureManager, capture_email, notify_free_limit_reached, notify_payment_completed

__all__ = [
    'ConvertKitClient',
    'EmailCaptureManager', 
    'capture_email',
    'notify_free_limit_reached',
    'notify_payment_completed'
]