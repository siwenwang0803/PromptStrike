#!/usr/bin/env python3
"""
RedForge Webhook Server - Simple Version for Render
"""

import os
import json
import stripe
import requests
from datetime import datetime
from pathlib import Path

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Configure Kit (formerly ConvertKit)
CONVERTKIT_API_KEY = os.getenv('KIT_API_KEY')
CONVERTKIT_API_SECRET = os.getenv('KIT_API_SECRET')

# Simple Flask app (more compatible with Render)
try:
    from flask import Flask, request, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def health():
        return jsonify({
            "service": "RedForge Payment API v2",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "kit_configured": bool(CONVERTKIT_API_KEY)
        })
    
    @app.route('/webhook/email-capture', methods=['POST', 'OPTIONS'])
    def email_capture():
        # Handle CORS preflight
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'ok'})
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        
        try:
            data = request.get_json()
            email = data.get('email')
            source = data.get('source', 'unknown')
            tags = data.get('tags', [])
            
            if not email:
                return jsonify({"error": "Email required"}), 400
            
            # Add to Kit (formerly ConvertKit) - only need API key for form submissions
            if CONVERTKIT_API_KEY:
                print(f"Attempting to add {email} to Kit...")
                # Use form subscription endpoint (form ID: 8320684 - RedForge form)
                ck_response = requests.post(
                    'https://api.convertkit.com/v3/forms/8320684/subscribe',
                    json={
                        'api_key': CONVERTKIT_API_KEY,
                        'email': email
                    }
                )
                
                if ck_response.ok:
                    response = jsonify({"status": "success", "message": "Added to Kit"})
                    print(f"✅ Successfully added {email} to Kit")
                else:
                    # Log but don't fail
                    print(f"Kit API error: {ck_response.status_code} - {ck_response.text}")
                    response = jsonify({"status": "success", "message": f"Kit error: {ck_response.status_code}"})
            else:
                # Save locally as fallback
                print(f"Kit not configured - API_KEY: {bool(CONVERTKIT_API_KEY)}")
                response = jsonify({"status": "success", "message": "Kit not configured"})
            
            # Add CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
            
        except Exception as e:
            response = jsonify({"error": str(e)})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 500
    
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