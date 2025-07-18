#!/usr/bin/env python3
"""
RedForge API Gateway - Production Simple Version
Handles authentication, rate limiting, and scan orchestration
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import asyncio
import logging
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

# Models
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
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required")
    
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

# Initialize FastAPI
app = FastAPI(
    title="RedForge API Gateway",
    description="Cloud-based LLM Security Scanning Platform",
    version="0.2.0"
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
        "version": "0.2.0",
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
        "version": "0.2.0",
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "database": database_status,
        "request_id": req_id,
        "supabase_url": os.getenv("SUPABASE_URL", "not_set")[:50] + "..." if os.getenv("SUPABASE_URL") else "not_set"
    }

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