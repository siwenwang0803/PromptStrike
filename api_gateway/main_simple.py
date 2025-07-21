#!/usr/bin/env python3
"""
RedForge API Gateway - Production Simple Version
Handles authentication, rate limiting, and scan orchestration
"""

import os
import uuid
import json
import hmac
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
import stripe
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Stripe Configuration
stripe_secret = os.getenv("STRIPE_SECRET")
if not stripe_secret:
    logging.error("STRIPE_SECRET environment variable is required")
    logging.error("Available env vars: " + ", ".join([k for k in os.environ.keys() if "STRIPE" in k]))
    raise ValueError("STRIPE_SECRET is required")
else:
    stripe.api_key = stripe_secret
    logging.info(f"Stripe API key configured: {stripe_secret[:8]}...")

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
if not STRIPE_WEBHOOK_SECRET:
    logging.error("STRIPE_WEBHOOK_SECRET environment variable is required")
else:
    logging.info(f"Stripe webhook secret configured: {STRIPE_WEBHOOK_SECRET[:8]}...")

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "dev@solvas.ai")

# Models
class StripeWebhookPayload(BaseModel):
    id: str
    object: str
    type: str
    data: Dict[str, Any]

class ScanRequest(BaseModel):
    target: str = Field(..., description="LLM target (e.g., 'gpt-4', 'claude-3')")
    attack_pack: str = Field(default="owasp-top-10", description="Attack pack to use")
    dry_run: bool = Field(default=False, description="Run limited test scan")
    format: str = Field(default="json", description="Report format: json, html, pdf")
    webhook_url: Optional[str] = Field(None, description="Callback URL for completion")

class ScanResponse(BaseModel):
    scan_id: str
    status: str
    estimated_duration: int  # seconds
    queue_position: Optional[int] = None

class ScanStatus(BaseModel):
    scan_id: str
    status: str  # queued, running, completed, failed
    progress: float  # 0.0 to 1.0
    current_attack: Optional[str] = None
    attacks_completed: int
    total_attacks: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report_url: Optional[str] = None
    error: Optional[str] = None

class APIKeyCreate(BaseModel):
    name: str = Field(..., description="Friendly name for the API key")

class APIKeyResponse(BaseModel):
    key: str
    name: str
    tier: str
    created_at: datetime
    usage_count: int
    revoked: bool

# Initialize Supabase
try:
    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE", "")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE environment variables are required")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    logging.info(f"Supabase initialized with URL: {supabase_url}")
    
except Exception as e:
    logging.error(f"Failed to initialize Supabase: {e}")
    # Create a mock client for now
    supabase = None

# Retry wrapper for Supabase queries
@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),          # Max 3 attempts
    wait=wait_fixed(0.5)                 # 0.5s between attempts
)
def fetch_api_key(key: str):
    """Fetch API key with retry logic"""
    if supabase is None:
        raise Exception("Supabase client not initialized")
    
    result = supabase.table("api_keys").select(
        "key, user_id, tier, usage_count, revoked, rate_limit_per_hour, users(tier, free_scans_used)"
    ).eq("key", key).eq("revoked", False).execute()
    
    return result

@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.5)
)
def update_api_key_usage(key: str, usage_count: int):
    """Update API key usage with retry logic"""
    if supabase is None:
        raise Exception("Supabase client not initialized")
    
    return supabase.table("api_keys").update({
        "usage_count": usage_count,
        "last_used_at": datetime.utcnow().isoformat()
    }).eq("key", key).execute()

@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.5)
)
def update_user_scans(user_id: str, free_scans_used: int):
    """Update user scan count with retry logic"""
    if supabase is None:
        raise Exception("Supabase client not initialized")
    
    return supabase.table("users").update({
        "free_scans_used": free_scans_used
    }).eq("id", user_id).execute()

@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.5)
)
def create_or_update_user_from_stripe(email: str, stripe_customer_id: str, tier: str):
    """Create or update user from Stripe payment"""
    if supabase is None:
        raise Exception("Supabase client not initialized")
    
    # Check if user exists
    existing_user = supabase.table("users").select("*").eq("email", email).execute()
    
    if existing_user.data:
        # Update existing user
        user_id = existing_user.data[0]["id"]
        supabase.table("users").update({
            "tier": tier,
            "stripe_customer_id": stripe_customer_id,
            "upgraded_at": datetime.utcnow().isoformat()
        }).eq("id", user_id).execute()
        return user_id
    else:
        # Create new user
        user_result = supabase.table("users").insert({
            "email": email,
            "tier": tier,
            "stripe_customer_id": stripe_customer_id,
            "created_at": datetime.utcnow().isoformat(),
            "upgraded_at": datetime.utcnow().isoformat()
        }).execute()
        return user_result.data[0]["id"]

@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_fixed(0.5)
)
def create_api_key_for_user(user_id: str, tier: str, name: str = "Stripe Auto-Generated"):
    """Create API key for new paid user"""
    if supabase is None:
        raise Exception("Supabase client not initialized")
    
    # Generate API key
    api_key = f"rk_{secrets.token_urlsafe(32)}"
    
    # Create API key record
    supabase.table("api_keys").insert({
        "key": api_key,
        "name": name,
        "user_id": user_id,
        "tier": tier,
        "usage_count": 0,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    return api_key

def send_welcome_email(email: str, api_key: str, tier: str):
    """Send welcome email with API key to new paid user"""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logging.warning("Email not configured, skipping welcome email")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = f"🔥 Welcome to RedForge {tier.title()} Plan - Your API Key Inside!"
        
        # Email body
        body = f"""
        <html>
        <body style="font-family: 'Roboto', Arial, sans-serif; line-height: 1.6; color: #e0e0e0; background: #0a0f1e; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background: #1a233a; border-radius: 10px; padding: 30px; border: 1px solid #00ffff;">
                <h1 style="color: #00ffff; text-align: center; text-shadow: 0 0 10px #00ffff;">🔥 Welcome to RedForge!</h1>
                
                <p>Thank you for upgrading to the <strong>{tier.title()} Plan</strong>! Your payment has been processed successfully.</p>
                
                <div style="background: rgba(0,255,255,0.1); padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #00ffff;">
                    <h3 style="color: #00ffff; margin-top: 0;">Your API Key:</h3>
                    <code style="background: rgba(0,0,0,0.4); padding: 10px; border-radius: 4px; display: block; font-size: 14px; word-break: break-all; color: #00ff88;">{api_key}</code>
                    <p style="margin: 10px 0 0 0; font-size: 12px; opacity: 0.8;">⚠️ Keep this key secure and don't share it publicly</p>
                </div>
                
                <h3 style="color: #00ffff;">Quick Start:</h3>
                <pre style="background: rgba(0,0,0,0.6); padding: 15px; border-radius: 8px; overflow-x: auto; color: #00ffff;">
# Install RedForge CLI
pip install redforge

# Set your API key
export REDFORGE_API_KEY="{api_key}"

# Run unlimited scans
redforge scan gpt-4 --cloud
redforge scan claude-3 --cloud
                </pre>
                
                <h3 style="color: #00ffff;">What's Next?</h3>
                <ul>
                    <li>✅ <strong>Unlimited scans</strong> - No more 1-scan limit</li>
                    <li>✅ <strong>Clean reports</strong> - No watermarks</li>
                    <li>✅ <strong>All formats</strong> - JSON, HTML, PDF exports</li>
                    <li>✅ <strong>Priority support</strong> - Fast response times</li>
                </ul>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://github.com/siwenwang0803/RedForge" style="background: linear-gradient(45deg, #00ffff, #007acc); color: #0a0f1e; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">View Documentation</a>
                </div>
                
                <p style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); opacity: 0.7;">
                    Questions? Reply to this email or contact <a href="mailto:dev@solvas.ai" style="color: #00ffff;">dev@solvas.ai</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, email, text)
        server.quit()
        
        logging.info(f"Welcome email sent to {email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send welcome email to {email}: {e}")
        return False

# Initialize FastAPI
app = FastAPI(
    title="RedForge API Gateway",
    description="Cloud-based LLM Security Scanning Platform",
    version="0.3.1"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://redforge.solvas.ai", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware for logging and debugging
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request for logging and debugging"""
    req_id = uuid.uuid4().hex[:8]
    request.state.req_id = req_id
    
    # Log the request
    logging.info(f"[{req_id}] {request.method} {request.url.path} - {request.client.host}")
    
    response = await call_next(request)
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = req_id
    
    # Log the response
    logging.info(f"[{req_id}] Response: {response.status_code}")
    
    return response

# Rate limiting (simple in-memory for now)
request_counts = {}

def simple_rate_limit(ip: str, limit: int = 100) -> bool:
    """Simple rate limiting"""
    current_time = datetime.now()
    
    if ip not in request_counts:
        request_counts[ip] = []
    
    # Remove old requests (older than 1 hour)
    request_counts[ip] = [
        req_time for req_time in request_counts[ip]
        if (current_time - req_time).seconds < 3600
    ]
    
    if len(request_counts[ip]) >= limit:
        return False
    
    request_counts[ip].append(current_time)
    return True

# Dependencies
async def verify_api_key(request: Request, x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key and return user/tier info"""
    
    # Simple rate limiting
    client_ip = request.client.host
    if not simple_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Check if Supabase is available
    if supabase is None:
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. Please try again later."
        )
    
    try:
        # Check if key exists and is active (with retry)
        result = fetch_api_key(x_api_key)
        
        if not result.data:
            raise HTTPException(
                status_code=401, 
                detail="Invalid or revoked API key"
            )
        
        key_data = result.data[0]
        user_data = key_data["users"]
        
        # Check for key sharing abuse (free tier)
        if user_data["tier"] == "free":
            # Check usage count for potential sharing
            if key_data["usage_count"] > 5:  # Suspicious usage for free tier
                logging.warning(f"Potential key sharing detected for free tier: {x_api_key[:8]}...")
                # Auto-revoke after threshold
                if key_data["usage_count"] > 10:
                    try:
                        supabase.table("api_keys").update({"revoked": True}).eq("key", x_api_key).execute()
                    except Exception as e:
                        logging.warning(f"Failed to revoke API key: {e}")
                    raise HTTPException(status_code=429, detail="API key revoked due to excessive usage. Generate a new key.")
            
            if user_data["free_scans_used"] >= 1:
                raise HTTPException(
                    status_code=402,
                    detail="Free tier limit reached. Upgrade to continue scanning."
                )
        
        return {
            "key": key_data["key"],
            "user_id": key_data["user_id"],
            "tier": user_data["tier"],
            "usage_count": key_data["usage_count"],
            "free_scans_used": user_data["free_scans_used"]
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        req_id = getattr(request.state, 'req_id', 'unknown')
        logging.error(f"[{req_id}] API key verification error: {e}")
        # Return 503 for database connectivity issues
        if "Name or service not known" in str(e) or "timeout" in str(e).lower():
            raise HTTPException(status_code=503, detail=f"Database service temporarily unavailable. Please retry in a few seconds. (Request ID: {req_id})")
        raise HTTPException(status_code=500, detail=f"Internal server error. (Request ID: {req_id})")

# Routes
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "RedForge API Gateway",
        "version": "0.3.1",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/healthz")
async def health_check_detailed(request: Request):
    """Detailed health check for monitoring"""
    database_status = "connected" if supabase is not None else "disconnected"
    overall_status = "ok" if supabase is not None else "degraded"
    req_id = getattr(request.state, 'req_id', 'unknown')
    
    return {
        "service": "RedForge API Gateway",
        "version": "0.3.1",
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "database": database_status,
        "request_id": req_id,
        "supabase_url": os.getenv("SUPABASE_URL", "not_set")[:50] + "..." if os.getenv("SUPABASE_URL") else "not_set"
    }

@app.post("/signup")
async def signup(request: Request):
    """User signup and API key generation"""
    try:
        body = await request.json()
        email = body.get("email")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Generate API key
        import secrets
        api_key = f"rk_{secrets.token_urlsafe(32)}"
        
        # Store in Supabase (with retry logic)
        @retry(
            retry=retry_if_exception_type(Exception),
            stop=stop_after_attempt(3),
            wait=wait_fixed(0.5)
        )
        def create_user_account():
            if supabase is None:
                raise Exception("Supabase client not initialized")
                
            # Create user record
            user_result = supabase.table("users").insert({
                "email": email,
                "tier": "free",
                "created_at": datetime.now().isoformat()
            }).execute()
            
            # Create API key record
            api_key_result = supabase.table("api_keys").insert({
                "key": api_key,
                "user_id": user_result.data[0]["id"],
                "tier": "free",
                "usage_count": 0,
                "created_at": datetime.now().isoformat()
            }).execute()
            
            return user_result.data[0]
        
        user_data = create_user_account()
        
        # Add to ConvertKit if configured
        try:
            kit_api_key = os.getenv("KIT_API_KEY")
            if kit_api_key:
                import requests
                kit_response = requests.post(
                    f"https://api.convertkit.com/v3/forms/8320684/subscribe",
                    data={
                        "api_key": kit_api_key,
                        "email": email,
                        "tags": ["redforge-signup", "free-tier"]
                    },
                    timeout=10
                )
                logging.info(f"ConvertKit signup: {kit_response.status_code}")
        except Exception as e:
            logging.warning(f"ConvertKit signup failed: {e}")
        
        return {
            "message": "Account created successfully",
            "api_key": api_key,
            "tier": "free",
            "user_id": user_data["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/stripe/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle Stripe webhook events"""
    try:
        # Get raw request body
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header or not STRIPE_WEBHOOK_SECRET:
            logging.warning(f"Missing Stripe signature or webhook secret. sig_header: {bool(sig_header)}, STRIPE_WEBHOOK_SECRET: {bool(STRIPE_WEBHOOK_SECRET)}")
            logging.warning(f"STRIPE_WEBHOOK_SECRET value: {STRIPE_WEBHOOK_SECRET[:20] if STRIPE_WEBHOOK_SECRET else 'None'}...")
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logging.error(f"Invalid Stripe payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logging.error(f"Invalid Stripe signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Process the event
        event_type = event["type"]
        logging.info(f"Processing Stripe event: {event_type}")
        
        if event_type == "checkout.session.completed":
            # Payment successful - upgrade user
            background_tasks.add_task(handle_successful_payment, event["data"]["object"])
            
        elif event_type == "customer.subscription.deleted":
            # Subscription cancelled - downgrade user
            background_tasks.add_task(handle_subscription_cancelled, event["data"]["object"])
            
        elif event_type == "invoice.payment_failed":
            # Payment failed - notify user
            background_tasks.add_task(handle_payment_failed, event["data"]["object"])
        
        else:
            logging.info(f"Unhandled Stripe event type: {event_type}")
        
        return {"received": True}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logging.error(f"Stripe webhook error: {e}")
        logging.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def handle_successful_payment(checkout_session):
    """Process successful payment and upgrade user"""
    try:
        customer_id = checkout_session["customer"]
        customer_email = checkout_session["customer_details"]["email"]
        amount_total = checkout_session["amount_total"]  # In cents
        
        # Determine tier based on amount
        if amount_total == 100:  # $1.00 test
            tier = "starter"
        elif amount_total == 2900:  # $29.00 production
            tier = "starter"
        elif amount_total == 9900:  # $99.00
            tier = "pro"
        else:
            logging.warning(f"Unknown payment amount: {amount_total}")
            tier = "starter"  # Default to starter
        
        logging.info(f"Processing payment: {customer_email} -> {tier} tier (${amount_total/100})")
        
        # Create or update user in Supabase
        user_id = create_or_update_user_from_stripe(
            email=customer_email,
            stripe_customer_id=customer_id,
            tier=tier
        )
        
        # Generate API key for the user
        api_key = create_api_key_for_user(user_id, tier, f"{tier.title()} Plan")
        
        # Send welcome email with API key
        email_sent = send_welcome_email(customer_email, api_key, tier)
        
        # Update ConvertKit if available
        try:
            kit_api_key = os.getenv("KIT_API_KEY")
            if kit_api_key:
                import requests
                kit_response = requests.post(
                    f"https://api.convertkit.com/v3/forms/8320684/subscribe",
                    data={
                        "api_key": kit_api_key,
                        "email": customer_email,
                        "tags": [f"redforge-{tier}", "paid-user", "stripe-customer"]
                    },
                    timeout=10
                )
                logging.info(f"ConvertKit update: {kit_response.status_code}")
        except Exception as e:
            logging.warning(f"ConvertKit update failed: {e}")
        
        # Log success
        logging.info(f"User upgrade completed: {customer_email} -> {tier} | API key: {api_key[:8]}... | Email: {'✅' if email_sent else '❌'}")
        
        # Store payment record for audit
        if supabase:
            try:
                supabase.table("payment_history").insert({
                    "user_id": user_id,
                    "stripe_customer_id": customer_id,
                    "stripe_session_id": checkout_session["id"],
                    "amount_cents": amount_total,
                    "tier": tier,
                    "email_sent": email_sent,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            except Exception as e:
                logging.warning(f"Failed to log payment history: {e}")
        
    except Exception as e:
        logging.error(f"Failed to process successful payment: {e}")

async def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription["customer"]
        
        # Find user by Stripe customer ID and downgrade
        if supabase:
            result = supabase.table("users").select("*").eq("stripe_customer_id", customer_id).execute()
            
            if result.data:
                user_id = result.data[0]["id"]
                email = result.data[0]["email"]
                
                # Downgrade to free tier
                supabase.table("users").update({
                    "tier": "free",
                    "downgraded_at": datetime.utcnow().isoformat()
                }).eq("id", user_id).execute()
                
                # Revoke existing API keys
                supabase.table("api_keys").update({
                    "revoked": True,
                    "revoked_at": datetime.utcnow().isoformat()
                }).eq("user_id", user_id).execute()
                
                logging.info(f"User downgraded to free tier: {email}")
                
    except Exception as e:
        logging.error(f"Failed to handle subscription cancellation: {e}")

async def handle_payment_failed(invoice):
    """Handle failed payment"""
    try:
        customer_id = invoice["customer"]
        
        # Find user and send notification
        if supabase:
            result = supabase.table("users").select("email").eq("stripe_customer_id", customer_id).execute()
            
            if result.data:
                email = result.data[0]["email"]
                logging.warning(f"Payment failed for user: {email}")
                # TODO: Send payment failed notification email
                
    except Exception as e:
        logging.error(f"Failed to handle payment failure: {e}")

@app.post("/scan", response_model=ScanResponse)
async def create_scan(
    request_obj: Request,
    scan_request: ScanRequest,
    background_tasks: BackgroundTasks,
    auth_data: Dict = Depends(verify_api_key)
):
    """Create a new LLM security scan"""
    scan_id = str(uuid.uuid4())
    
    # Check concurrent scan limits
    tier = auth_data["tier"]
    concurrent_limit = {"free": 1, "starter": 3, "pro": 10}[tier]
    
    # Count active scans for user
    active_scans = supabase.table("scan_history").select("id").eq("user_id", auth_data["user_id"]).is_("completed_at", "null").execute()
    
    if len(active_scans.data) >= concurrent_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Concurrent scan limit reached ({concurrent_limit} for {tier} tier). Wait for current scans to complete."
        )
    
    # Calculate scan parameters based on tier
    if tier == "free":
        max_attacks = 5  # Limited attacks for free tier
    elif tier == "starter":
        max_attacks = 50  # Full OWASP Top 10
    else:  # pro
        max_attacks = 100  # All attack packs
    
    # Queue the scan
    scan_data = {
        "id": scan_id,
        "api_key": auth_data["key"],
        "user_id": auth_data["user_id"],
        "target": scan_request.target,
        "attack_pack": scan_request.attack_pack,
        "dry_run": scan_request.dry_run,
        "format": scan_request.format,
        "max_attacks": max_attacks,
        "tier": tier,
        "created_at": datetime.utcnow().isoformat(),
        "status": "queued"
    }
    
    # Save to database
    supabase.table("scan_history").insert({
        "id": scan_id,
        "api_key": auth_data["key"],
        "user_id": auth_data["user_id"],
        "scan_type": "dry-run" if scan_request.dry_run else "full",
        "target_model": scan_request.target,
        "attack_count": max_attacks,
        "metadata": json.dumps(scan_data)
    }).execute()
    
    # Increment usage counter (with retry)
    if tier == "free":
        try:
            update_user_scans(auth_data["user_id"], auth_data["free_scans_used"] + 1)
        except Exception as e:
            logging.warning(f"Failed to update user scan count: {e}")
    
    try:
        update_api_key_usage(auth_data["key"], auth_data["usage_count"] + 1)
    except Exception as e:
        logging.warning(f"Failed to update API key usage: {e}")
    
    # Start background scan
    background_tasks.add_task(process_scan, scan_id, scan_data)
    
    return ScanResponse(
        scan_id=scan_id,
        status="queued",
        estimated_duration=300,  # 5 minutes estimate
        queue_position=1
    )

@app.get("/scan/{scan_id}/status", response_model=ScanStatus)
async def get_scan_status(scan_id: str, auth_data: Dict = Depends(verify_api_key)):
    """Get scan status and progress"""
    try:
        result = supabase.table("scan_history").select("*").eq("id", scan_id).eq("user_id", auth_data["user_id"]).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        scan = result.data[0]
        metadata = json.loads(scan["metadata"] or "{}")
        
        return ScanStatus(
            scan_id=scan_id,
            status=metadata.get("status", "unknown"),
            progress=metadata.get("progress", 0.0),
            current_attack=metadata.get("current_attack"),
            attacks_completed=metadata.get("attacks_completed", 0),
            total_attacks=scan["attack_count"],
            started_at=scan["created_at"],
            completed_at=scan["completed_at"],
            report_url=scan["report_url"],
            error=metadata.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get scan status error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/scan/{scan_id}/report")
async def get_scan_report(scan_id: str, auth_data: Dict = Depends(verify_api_key)):
    """Get scan report download URL"""
    try:
        result = supabase.table("scan_history").select("report_url").eq("id", scan_id).eq("user_id", auth_data["user_id"]).execute()
        
        if not result.data or not result.data[0]["report_url"]:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"download_url": result.data[0]["report_url"]}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get scan report error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Background processing
async def process_scan(scan_id: str, scan_data: Dict):
    """Process scan in background (simplified)"""
    try:
        # Update status to running
        await update_scan_status(scan_id, "running", 0.1)
        
        # Simulate scan processing
        await asyncio.sleep(2)  # Simulate work
        await update_scan_status(scan_id, "running", 0.5, "Processing attacks...")
        
        await asyncio.sleep(2)  # Simulate more work
        await update_scan_status(scan_id, "generating_report", 0.9)
        
        # Mark as completed
        await update_scan_status(scan_id, "completed", 1.0)
        
        # Update with report URL
        supabase.table("scan_history").update({
            "completed_at": datetime.utcnow().isoformat(),
            "report_url": f"https://reports.redforge.ai/{scan_id}.json"
        }).eq("id", scan_id).execute()
        
    except Exception as e:
        await update_scan_status(scan_id, "failed", 0.0, error=str(e))

async def update_scan_status(scan_id: str, status: str, progress: float, current_attack: Optional[str] = None, error: Optional[str] = None):
    """Update scan status in database"""
    try:
        # Get current metadata
        result = supabase.table("scan_history").select("metadata").eq("id", scan_id).execute()
        if result.data:
            metadata = json.loads(result.data[0]["metadata"] or "{}")
        else:
            metadata = {}
        
        # Update metadata
        metadata.update({
            "status": status,
            "progress": progress,
            "current_attack": current_attack,
            "attacks_completed": int(progress * metadata.get("max_attacks", 50)),
            "last_updated": datetime.utcnow().isoformat()
        })
        
        if error:
            metadata["error"] = error
        
        # Save back to database
        supabase.table("scan_history").update({
            "metadata": json.dumps(metadata)
        }).eq("id", scan_id).execute()
        
    except Exception as e:
        logging.error(f"Error updating scan status: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)