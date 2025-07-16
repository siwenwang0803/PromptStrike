#!/usr/bin/env python3
"""
RedForge Webhook Server - Simple Version for Render
"""

import os
import json
import stripe
from datetime import datetime
from pathlib import Path

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Simple Flask app (more compatible with Render)
try:
    from flask import Flask, request, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def health():
        return jsonify({
            "service": "RedForge Payment API",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })
    
    @app.route('/webhook', methods=['POST'])
    def webhook():
        payload = request.get_data()
        sig_header = request.headers.get('stripe-signature')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, WEBHOOK_SECRET
            )
            
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                
                # Save customer data
                customer_data = {
                    'email': session.get('customer_email'),
                    'tier': session.get('metadata', {}).get('tier', 'starter'),
                    'status': 'active',
                    'created_at': datetime.now().isoformat()
                }
                
                # Save to file
                customers_file = Path('./customers.json')
                customers = []
                if customers_file.exists():
                    try:
                        customers = json.loads(customers_file.read_text())
                    except:
                        customers = []
                
                customers.append(customer_data)
                customers_file.write_text(json.dumps(customers, indent=2))
                
                return jsonify({"status": "success"})
            
            return jsonify({"status": "handled"})
            
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    
    if __name__ == '__main__':
        port = int(os.getenv('PORT', 8000))
        app.run(host='0.0.0.0', port=port)

except ImportError:
    # Fallback to FastAPI
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import uvicorn
    
    app = FastAPI()
    
    @app.get("/")
    async def health():
        return {"service": "RedForge Payment API", "status": "healthy"}
    
    @app.post("/webhook")
    async def webhook(request: Request):
        return {"status": "webhook received"}
    
    if __name__ == "__main__":
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)