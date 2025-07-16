#!/usr/bin/env python3
"""
RedForge Webhook Server - Minimal Version for Render
Standalone webhook server without CLI dependencies
"""

import os
import json
import logging
import stripe
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure Stripe (using environment variables only)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
DOMAIN = os.getenv('DOMAIN', 'https://redforge.solvas.ai')

# Create data directory
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="RedForge Payment API",
    description="Stripe webhook endpoint for RedForge payments",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pricing configuration
PRICING_PLANS = {
    "starter": {"name": "Starter", "price": 2900, "features": ["100 scans/month", "3 models", "OWASP attacks"]},
    "pro": {"name": "Pro", "price": 9900, "features": ["1000 scans/month", "Unlimited models", "All attack packs"]},
    "enterprise": {"name": "Enterprise", "price": 49900, "features": ["Unlimited scans", "All features", "24/7 support"]},
}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "RedForge Payment API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": "render"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "stripe_configured": bool(stripe.api_key),
            "webhook_secret_configured": bool(WEBHOOK_SECRET),
            "domain": DOMAIN,
            "data_dir": str(DATA_DIR)
        }
    }

@app.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, WEBHOOK_SECRET
        )
        
        logger.info(f"Webhook received: {event['type']}")
        
        # Handle checkout completion
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Save customer data
            customer_data = {
                'email': session.get('customer_email'),
                'stripe_customer_id': session.get('customer'),
                'stripe_subscription_id': session.get('subscription'),
                'tier': session.get('metadata', {}).get('tier', 'starter'),
                'status': 'active',
                'created_at': datetime.now().isoformat(),
                'source': 'webhook'
            }
            
            # Save to JSON file
            customers_file = DATA_DIR / 'customers.json'
            customers = []
            if customers_file.exists():
                try:
                    customers = json.loads(customers_file.read_text())
                except:
                    customers = []
            
            customers.append(customer_data)
            customers_file.write_text(json.dumps(customers, indent=2))
            
            logger.info(f"Customer created: {customer_data['email']}")
            
            return {"status": "success", "customer": customer_data['email']}
        
        return {"status": "handled", "type": event['type']}
        
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/customers")
async def get_customers():
    """Get customer list"""
    customers_file = DATA_DIR / 'customers.json'
    
    if not customers_file.exists():
        return {"customers": [], "count": 0}
    
    try:
        customers = json.loads(customers_file.read_text())
        return {
            "customers": customers,
            "count": len(customers),
            "active_count": len([c for c in customers if c.get('status') == 'active'])
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/test-webhook")
async def test_webhook():
    """Test webhook functionality"""
    
    test_customer = {
        'email': f'test-{int(datetime.now().timestamp())}@example.com',
        'stripe_customer_id': 'cus_test123',
        'stripe_subscription_id': 'sub_test456',
        'tier': 'starter',
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'source': 'test'
    }
    
    customers_file = DATA_DIR / 'customers.json'
    customers = []
    if customers_file.exists():
        try:
            customers = json.loads(customers_file.read_text())
        except:
            customers = []
    
    customers.append(test_customer)
    customers_file.write_text(json.dumps(customers, indent=2))
    
    return {"status": "success", "customer": test_customer}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"🚀 Starting RedForge Webhook Server")
    logger.info(f"   Port: {port}")
    logger.info(f"   Domain: {DOMAIN}")
    logger.info(f"   Stripe: {'✅ Configured' if stripe.api_key else '❌ Missing'}")
    logger.info(f"   Webhook Secret: {'✅ Configured' if WEBHOOK_SECRET else '❌ Missing'}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)